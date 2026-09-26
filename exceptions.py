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
    def __init__(self, context_name:str, line_number:int, c:int, line:str, line_start:int, line_end:int, underlines:list[tuple[int, str, int, int]]):
        self.context_name = context_name
        self.line_number = line_number
        self.c = c
        self.line = line
        self.line_start = line_start
        self.line_end = line_end
        self.underlines = underlines

def _get_i_end(node:parsingnodes.ParsingNode)->int:
    if node.ctx.match is None:
        i_end = node.ctx.i if node.ctx.i_end is None else node.ctx.i_end
    else:
        i_end = node.ctx.match.end() if node.ctx.i_end is None else node.ctx.i_end
    for child in node.children:
        x = _get_i_end(child)
        if x > i_end:
            i_end = x
    return i_end

def _get_help_text_info(node:parsingnodes.ParsingNode, s:"script.Script", expand_for_operator:bool=False):
    i = _i = node.ctx.i if node.ctx.match is None else node.ctx.match.start()
    if expand_for_operator and isinstance(node, parsingnodes.ParsingNodeOperator) and node.ctx.optree is not None:
        left = node.ctx.optree.lhand
        while isinstance(left, parsingnodes.operation_node):
            if left.lhand is None:
                left = left.rhand
            else:
                left = left.lhand
        right = node.ctx.optree.rhand
        while isinstance(right, parsingnodes.operation_node):
            right = right.rhand

        lhti = _get_help_text_info(left, s, expand_for_operator=False)
        rhti = _get_help_text_info(right, s, expand_for_operator=False)
        ohti = _get_help_text_info(node, s, expand_for_operator=False)

        i = ohti.underlines[0][2]
        i_end = ohti.underlines[0][3]
        j = lhti.underlines[0][2]
        j_end = rhti.underlines[0][3]
        return _help_text_info(ohti.context_name, ohti.line_number, ohti.c, ohti.line, ohti.line_start, ohti.line_end, [
            (1, "^", i-1, i_end+1),
            (0, "*", j, j_end)
        ])
    else:
        while i < len(s.raw):
            if s.raw[i].isspace():
                i += 1
            else:
                break
        else:
            i = _i
        i_end = _get_i_end(node)
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
        line_start += 1
        line = s.raw[line_start:line_end].rstrip()
        c = i - line_start
        return _help_text_info(node.ctx.name, line_number, c, line, line_start, line_end, [(0, "^", i, i_end)])

def _underline_generate(ustart:int, uend:int, sorted_u:list[tuple[int, str, int, int]], last="\n"):
    for i in range(ustart, uend):
        for _, c, ui, ui_end in sorted_u:
            if i >= ui and i < ui_end:
                yield c
                break
        else:
            yield " "
    yield last


def _base_help_text(info:_help_text_info, error_action:str, error_message):
    if info.underlines:
        ustart, uend = info.underlines[0][2:4]
        for i in range(1, len(info.underlines)):
            u = info.underlines[i]
            if u[2] < ustart:
                ustart = u[2]
            if u[3] > uend:
                uend = u[3]

        if ustart < info.line_start:
            ustart = info.line_start
        if uend > info.line_end:
            uend = info.line_end

        padding = ustart - info.line_start + 2
        sorted_u = sorted(info.underlines, key=lambda u: u[0], reverse=True)
        under = "".join(_underline_generate(ustart, uend, sorted_u))
    else:
        padding = 0
        under = ""
    return f"Error {error_action} script {info.context_name}\nOn line {info.line_number}, character {info.c+1}:\n  {info.line}\n{" "*padding}{under}{error_message}"

class InvalidOverloadException(Exception):
    "Overload is not valid."

class DuplicateOverloadException(InvalidOverloadException):
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

    __TNAME__ = "ParsingException"

    def help_text(self, s:"script.Script", step:Callable[[], Any]|None=None):
        if self._ctx is None:
            if step is None or (node := s.steps_debug.get(step, None)) is None:
                return f"{self.__TNAME__}: {self}"
            self._set_context(ExceptionContext(node, step))
        info = _get_help_text_info(self._ctx.node, s)
        return _base_help_text(info, "parsing", f"{self.__TNAME__}: {self}")

class TPUnknownValue(TParsingException):
    "Could read value but could not determine its type."

    __TNAME__ = "UnknownValue"

class TPEnclMismatch(TParsingException):
    "Enclosing symbols do not match."

    __TNAME__ = "EnclMismatch"

class TPUnexpectedSymbol(TParsingException):
    "Symbol was not expected here."

    __TNAME__ = "UnexpectedSymbol"

class TPExpectedSymbol(TParsingException):
    "Symbol was expected here."

    __TNAME__ = "ExpectedSymbol"

class TPUnexpectedKeyword(TParsingException):
    "Keyword was not expected here."

    __TNAME__ = "UnexpectedKeyword"

class TPExpectedEvaluable(TParsingException):
    "Evaluable expression was expected here."

    __TNAME__ = "ExpectedEvaluable"

class TPExpectedName(TParsingException):
    "Name was expected."

    __TNAME__ = "ExpectedName"

class TPUnexpectedEndOfCode(TParsingException):
    "Code ended abruptly."

    __TNAME__ = "UnexpectedEndOfCode"

    def help_text(self, s, step=None):
        if self._ctx is None:
            if step is None or (node := s.steps_debug.get(step, None)) is None:
                return f"{self.__TNAME__}: {self}"
            self._set_context(ExceptionContext(node, step))
        info = _get_help_text_info(self._ctx.node, s)
        return _base_help_text(info, "parsing", f"{self.__TNAME__}: {self}", clamp_to_line=False)



class TCompilationException(TronixException):
    "Base class for all tronix compilation exceptions."

    __TNAME__ = "CompilationException"

    def help_text(self, s, step=None):
        if self._ctx is None:
            if step is None or (node := s.steps_debug.get(step, None)) is None:
                return f"{self.__TNAME__}: {self}"
            self._set_context(ExceptionContext(node, step))
        info = _get_help_text_info(self._ctx.node, s)
        return _base_help_text(info, "compiling", f"{self.__TNAME__}: {self}")

class TCIncorrectParamaterOrder(TCompilationException):
    "Parameter node order is incorrect."

    __TNAME__ = "IncorrectParameterOrder"

class TCInvalidParameter(TCompilationException):
    "Parameter node cannot be evaluated."

    __TNAME__ = "InvalidParameter"

class TCIncorrectOperandOrder(TCompilationException):
    "Operand/operator order is incorrect."

    __TNAME__ = "IncorrectOperandOrder"

class TCInvalidOperand(TCompilationException):
    "Operand is of invalid node type."

    __TNAME__ = "InvalidOperand"

class TCIncorrectIfStatement(TCompilationException):
    "Order of ifs/else ifs/elses is incorrect."

    __TNAME__ = "IncorrectIfStatement"

class TCIncorrentCatchStatement(TCompilationException):
    "Catch statement does not have at most one name and one codeblock (is incorrent)."

    __TNAME__ = "IncorrectCatchStatement"

class TCInvalidFStringEmbeddedExpression(TCompilationException):
    "The given f-string embedded expression is not valid."

    __TNAME__ = "InvalidFStringEmbeddedExpression"


class TRuntimeException(TronixException):
    "Base class for all tronix runtime exceptions."

    __TNAME__ = "RuntimeException"

    def help_text(self, s, step=None):
        if self._ctx is None:
            if step is None or (node := s.steps_debug.get(step, None)) is None:
                return f"{self.__TNAME__}: {self}"
            self._set_context(ExceptionContext(node, step))
        info = _get_help_text_info(self._ctx.node, s, expand_for_operator=True)
        return _base_help_text(info, "running", f"{self.__TNAME__}: {self}")

class TRMissingFunction(TRuntimeException):
    "Function is not in the function table."

class TRMissingName(TRuntimeException):
    "Name is not in any namespace."

    __TNAME__ = "MissingName"

    def __init__(self, message:str, name:str, flags:ExceptionFlags=0, ctx:ExceptionContext=None):
        super().__init__(message, flags, ctx)
        self.name = name

class TRBadAttribute(TRuntimeException):
    "Object does not like the specified attribute."

    __TNAME__ = "BadAttribute"

    def __init__(self, message:str, name:str, flags:ExceptionFlags=0, ctx:ExceptionContext=None):
        super().__init__(message, flags, ctx)
        self.name = name

class TRBadSubscript(TRuntimeException):
    "Object does not like being subscripted with this value."

    __TNAME__ = "BadAttribute"

    def __init__(self, message:str, value:"script.ScriptVariable", flags:ExceptionFlags=0, ctx:ExceptionContext=None):
        super().__init__(message, flags, ctx)
        self.value = value

class TRNotImplemented(TRuntimeException):
    "Function or operation is not implemented."

    __TNAME__ = "NotImplemented"

class TRMustEvaluate(TRuntimeException):
    "Function or operation must result in a value."

    __TNAME__ = "MustEvaluate"

class TRTypeError(TRuntimeException):
    "Expected one type but got another."

    __TNAME__ = "TypeError"

class TRInvalidParameterOrder(TRuntimeException):
    "Parameter(s) came in wrong order."

    __TNAME__ = "InvalidParameterOrder"

class TRUnknownParameter(TRuntimeException):
    "Unknown parameter."

    __TNAME__ = "UnknownParameter"

class TRUserException(TRuntimeException):
    "Exception raised by user code."

    __TNAME__ = "UserException"

class TRBadValue(TRuntimeException):
    "Function received a value it didn't like."

    __TNAME__ = "BadValue"

    def __init__(self, message:str, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None, parameter:str|None=None):
        super().__init__(message, flags, ctx)
        self.parameter = parameter

class TRWrappedException(TRuntimeException):

    __TNAME__ = "WrappedException"

    def __init__(self, e:Exception, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
        super().__init__(f"Python {type(e).__name__}: {e}", flags, ctx)
        self._e = e
    
    def unwrap(self):
        return self._e

def wrap(e:Exception, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
    if isinstance(e, (TronixException, _TronixRuntimeAssertion)):
        return e
    return TRWrappedException(e, flags=flags, ctx=ctx)