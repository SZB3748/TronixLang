from .import parsingnodes
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
        self._ctx = ctx
        ctx._e = weakref.ref(self)

    @property
    def is_warning(self):
        return bool(self.flags & FLAG_WARNING)
    
    @is_warning.setter
    def is_warning(self, value:bool):
        if bool(value) != self.is_warning:
            self.flags ^= FLAG_WARNING

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

class TMissingFunction(TRuntimeException):
    "Function is not in the function table."

class TMissingName(TRuntimeException):
    "Name is not in any namespace."

    __TNAME__ = "MissingName"

class TNotImplemented(TRuntimeException):
    "Function or operation is not implemented."

class TMustEvaluate(TRuntimeException):
    "Function or operation must result in a value."

class TTypeError(TRuntimeException):
    "Expected one type but got another."

class TInvalidParameterOrder(TRuntimeException):
    "Parameter(s) came in wrong order."

class TUnknownParameter(TRuntimeException):
    "Unknown parameter."

class TUserException(TRuntimeException):
    "Exception raised by user code."

class TBadValue(TRuntimeException):
    "Function received a value it didn't like."

    def __init__(self, message:str, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None, parameter:str|None=None):
        super().__init__(message, flags, ctx)
        self.parameter = parameter

class TWrappedException(TRuntimeException):
    def __init__(self, ctx:ExceptionContext, e:Exception, flags:ExceptionFlags=0):
        super().__init__(ctx, f"{type(e).__name__}: {e}", flags)
        self._e = e
    
    def unwrap(self):
        return self._e

def wrap(e:Exception, flags:ExceptionFlags=0, ctx:ExceptionContext|None=None):
    if isinstance(e, (TronixException, _TronixRuntimeAssertion)):
        return e
    return TWrappedException(e, flags=flags, ctx=ctx)