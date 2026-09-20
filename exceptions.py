from .import parsingnodes
from . import script
from re import Match
from typing import Any, Callable, Self
import weakref


ExceptionFlags = int
FLAG_WARNING = 1

ParsingExceptionTarget = tuple[int, Match|None]|tuple[None,None]

class ExceptionContext:
    def __init__(self, node:parsingnodes.ParsingNode, step:Callable[[], Any]|None=None, parent:Self|None=None):
        self.node = node
        self.step = step
        self.parent = parent
        self._e:weakref.ReferenceType[TronixException]|None = None

class TronixException(Exception):
    "Base class for tronix exceptions."

    def __init__(self, message:str, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
        super().__init__(message)
        self.flags = flags
        self._set_context(ctx)

    def _set_context(self, ctx:ExceptionContext|None):
        self._ctx = ctx
        if ctx is not None:
            ctx._e = weakref.ref(self)

    @property
    def is_warning(self):
        return bool(self.flags & FLAG_WARNING)
    
    @is_warning.setter
    def is_warning(self, value:bool):
        if bool(value) != self.is_warning:
            self.flags ^= FLAG_WARNING

    def help_text(self, s:"script.Script", step:Callable[[], Any]|None=None):
        return None

class _help_text_info:
    def __init__(self, context_name:str, line_number:int, c:int, line:str, i:int, i_end:int, line_start:int, line_end:int):
        self.context_name = context_name
        self.line_number = line_number
        self.c = c
        self.line = line
        self.i = i
        self.i_end = i_end
        self.line_start = line_start
        self.line_end = line_end

def _get_i_end(node:parsingnodes.ParsingNode)->int:
    i_end = node.ctx.match.end() if node.ctx.i_end is None else node.ctx.i_end
    for child in node.children:
        x = _get_i_end(child)
        if x > i_end:
            i_end = x
    return i_end

def _get_help_text_info(e:TronixException, s:"script.Script"):
    i = e._ctx.node.ctx.match.start()
    while s.raw[i].isspace():
        i += 1
    i_end = _get_i_end(e._ctx.node)
    line_start = s.raw.rfind("\n", 0, i)
    line_end = s.raw.find("\n", i)
    if line_start == 0:
        line_number = 2
    elif line_start < 0:
        line_number = 1
    else:
        line_number = s.raw.count("\n", 0, line_start-1)+2
    if line_end < 0:
        line_end = len(s.raw)
    line = s.raw[line_start+1:line_end].rstrip()
    c = i - line_start - 1
    return _help_text_info(e._ctx.node.ctx.name, line_number, c, line, i, i_end, line_start, line_end)

def _base_help_text(info:_help_text_info, focus_length:int, error_message):
    return f"Error running script {info.context_name}\nOn line {info.line_number}, {info.c+1} character{"s"*bool(info.c)} in:\n  {info.line}\n  {" "*info.c}{"^"*focus_length}\n{error_message}"

class DuplicateOverloadException(Exception):
    "Overload already exists in function."

class TraitMergeException(Exception):
    "Could not merge a script function under the desired trait."

class TypeAnnotationException(Exception):
    "Base class for type annotation exceptions."

class InvalidTypeAnnotationException(TypeAnnotationException):
    "Type annotation cannot be parsed."

    def __init__(self, *args, annotation:str):
        super().__init__(*args)
        self.annotation = annotation

class AnnotationUnknownTypeException(TypeAnnotationException):
    "Type annotation specifies unknown type."

    def __init__(self, *args, type_name:str):
        super().__init__(*args)
        self.type_name = type_name

class AnnotationBadArgumentsException(TypeAnnotationException):
    "Type annotation got bad arguments."

class UnknownAnnotationException(Exception):
    "Type annotation name is unknown."

    def __init__(self, *args, name:str):
        super().__init__(*args)
        self.name = name

class AnnotationEnclosureException(Exception):
    "Type annotation has an issue with an enclosing syntax or its contents."

class _TronixRuntimeAssertion(Exception):
    "Assertion raised during script runtime."


class TParsingException(TronixException): #aka syntax exception
    "Base class for all tronix parsing exceptions."

class TUnknownValue(TParsingException):
    "Could read value but could not determine its type."

class TEnclMismatch(TParsingException):
    "Enclosing symbols do not match."

class TUnexpectedSymbol(TParsingException):
    "Symbol was not expected here."

class TExpectedSymbol(TParsingException):
    "Symbol was expected here."

class TUnexpectedKeyword(TParsingException):
    "Keyword was not expected here."

class TExpectedKeyword(TParsingException):
    "Keyword was expected here."

class TExpectedEvaluable(TParsingException):
    "Evaluable expression was expected here."

class TExpectedName(TParsingException):
    "Name was expected."



class TCompilationException(TronixException):
    "Base class for all tronix compilation exceptions."

class TIncorrectParamaterOrder(TCompilationException):
    "Parameter node order is incorrect."

class TInvalidParameter(TCompilationException):
    "Parameter node cannot be evaluated."

class TIncorrectOperandOrder(TCompilationException):
    "Operand/operator order is incorrect."

class TInvalidOperand(TCompilationException):
    "Operand is of invalid node type."

class TIncorrectIfStatement(TCompilationException):
    "Order of ifs/else ifs/elses is incorrect."

class TIncorrentCatchStatement(TCompilationException):
    "Catch statement does not have at most one name and one codeblock (is incorrent)."

class TInvalidFStringEmbeddedExpression(TCompilationException):
    "The given f-string embedded expression is not valid."


class TRuntimeException(TronixException):
    "Base class for all tronix runtime exceptions."

    __TNAME__ = "RuntimeException"

    def help_text(self, s, step=None):
        if self._ctx is None:
            if step is None or (node := s.steps_debug.get(step, None)) is None:
                return f"{self.__TNAME__}: {self}"
            self._set_context(ExceptionContext(node, step))
        info = _get_help_text_info(self, s)
        return _base_help_text(info, min(info.i_end, info.line_end)-info.i, f"{self.__TNAME__}: {self}")

class TMissingFunction(TRuntimeException):
    "Function is not in the function table."

class TMissingName(TRuntimeException):
    "Name is not in any namespace."

    __TNAME__ = "MissingName"

    def __init__(self, message:str, name:str, flags:ExceptionFlags=0, ctx:ExceptionContext=None):
        super().__init__(message, flags, ctx)
        self.name = name

    # def help_text(self, s, step=None):
    #     if self._ctx is None:
    #         if step is None or (node := s.steps_debug.get(step, None)) is None:
    #             return f"{self.__TNAME__}: {self}"
    #         self._set_context(ExceptionContext(node, step))
    #     return _base_help_text(_get_help_text_info(self, s), len(self.name), f"{self.__TNAME__}: {self}")

class TNotImplemented(TRuntimeException):
    "Function or operation is not implemented."

    __TNAME__ = "NotImplemented"

class TMustEvaluate(TRuntimeException):
    "Function or operation must result in a value."

    __TNAME__ = "MustEvaluate"

class TTypeError(TRuntimeException):
    "Expected one type but got another."

    __TNAME__ = "TypeError"

class TInvalidParameterOrder(TRuntimeException):
    "Parameter(s) came in wrong order."

    __TNAME__ = "InvalidParameterOrder"

class TUnknownParameter(TRuntimeException):
    "Unknown parameter."

    __TNAME__ = "UnknownParameter"

class TUserException(TRuntimeException):
    "Exception raised by user code."

    __TNAME__ = "UserException"

class TBadValue(TRuntimeException):
    "Function received a value it didn't like."

    __TNAME__ = "BadValue"

    def __init__(self, message:str, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None, parameter:str|None=None):
        super().__init__(message, flags, ctx)
        self.parameter = parameter

class TWrappedException(TRuntimeException):

    __TNAME__ = "WrappedException"

    def __init__(self, e:Exception, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
        super().__init__(f"Python {type(e).__name__}: {e}", flags, ctx)
        self._e = e
    
    def unwrap(self):
        return self._e

def wrap(e:Exception, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
    if isinstance(e, (TronixException, _TronixRuntimeAssertion)):
        return e
    return TWrappedException(e, flags=flags, ctx=ctx)