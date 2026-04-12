from .import parsingnodes
from re import Match


ExceptionFlags = int
FLAG_WARNING = 1

ParsingExceptionTarget = tuple[int, Match|None]|tuple[None,None]

class TronixException(Exception):
    "Base class for tronix exceptions."

    def __init__(self, message:str, flags:ExceptionFlags=0):
        super().__init__(message)
        self.flags = flags

    @property
    def is_warning(self):
        return bool(self.flags & FLAG_WARNING)
    
    @is_warning.setter
    def is_warning(self, value:bool):
        if bool(value) != self.is_warning:
            self.flags ^= FLAG_WARNING

class _TronixRuntimeAssertion(Exception):
    "Assertion raised during script runtime."


class TParsingException(TronixException): #aka syntax exception
    "Base class for all tronix parsing exceptions."

    def __init__(self, message:str, target:ParsingExceptionTarget=(None,None), flags:ExceptionFlags=0):
        super().__init__(message, flags)
        self.target = target

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



class TCompilationException(TronixException):
    "Base class for all tronix compilation exceptions."

    def __init__(self, message:str, target:parsingnodes.ParsingNode|None=None, flags:ExceptionFlags=0):
        super().__init__(message, flags)
        self.target = target

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



class TRuntimeException(TronixException):
    "Base class for all tronix runtime exceptions."
    def __init__(self, message:str, target:parsingnodes.ParsingNode|None=None, flags:ExceptionFlags=0):
        super().__init__(message, flags)
        self.target = target

class TMissingFunction(TRuntimeException):
    "Function is not in the function table."

class TMissingName(TRuntimeException):
    "Name is not in any namespace."

class TNotImplemented(TRuntimeException):
    "Function or operation is not implemented."

class TMustEvaluate(TRuntimeException):
    "Function or operation must result in a value."

class TWrappedException(TRuntimeException):
    def __init__(self, e:Exception, flags:ExceptionFlags=0):
        super().__init__(f"{type(e).__name__}: {e}", flags)
        self._e = e
    
    def unwrap(self):
        return self._e

def wrap(e:Exception, flags:ExceptionFlags=0):
    if isinstance(e, (TronixException, _TronixRuntimeAssertion)):
        return e
    return TWrappedException(e, flags=flags)