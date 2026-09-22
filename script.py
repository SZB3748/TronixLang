from .import exceptions
from .parsingnodes import *

import hashlib
import inspect
import re
from typing import Any, Awaitable, Callable, Iterable, Self
import weakref

KEYWORDS = {"if","else","loop","catch","global","var","define","and","or","not","break","skip"}

PATTERN_NAME = r"(?:[a-zA-Z_][a-zA-Z0-9_]*)"
PATTERN_NAME_CHARSET = r"[a-zA-Z0-9_]"
PATTERN_OPERATOR = r"(?:\.|[+\-*\/%=><\!]=?)"
PATTERN_INTEGER_LITERAL = r"(?:[0-9]+)"
PATTERN_FLOAT_LITERAL = r"(?:[0-9]+\.[0-9]+)"
PATTERN_STRING_LITERAL_SINGLE = r"(?:f?\'[^\\]*?(?:\\.[^\\]*?)*\')"
PATTERN_STRING_LITERAL_DOUBLE = r"(?:f?\"[^\\]*?(?:\\.[^\\]*?)*\")"
PATTERN_STRING_LITERAL = f"(?:{PATTERN_STRING_LITERAL_DOUBLE}|{PATTERN_STRING_LITERAL_SINGLE})"
PATTERN_KEYWORDS = f"(?:{"|".join(KEYWORDS)})"
PATTERN_LITERAL = f"(?:(?P<value_null>null)|(?P<value_bool>true|false)|(?P<value_float>{PATTERN_FLOAT_LITERAL})|(?P<value_integer>{PATTERN_INTEGER_LITERAL})|(?P<value_string>{PATTERN_STRING_LITERAL}))"
PATTERN_VALUE = f"(?:{PATTERN_LITERAL}|(?P<value_name>{PATTERN_NAME}))"
PATTERN_NAME_VALUE_PAIR = f"(?:(?P<name_value_pair_name>{PATTERN_NAME})\\s*:)"
PATTERN_FUNCTION_BEGIN = f"(?:(?P<function_name>{PATTERN_NAME})\\s*\\()"
PATTERN_SUBSCRIPT_BEGIN = f"(?:\\[)"
_PATTERN_NO_OP = r"^$."
#PATTERN_ASSIGN_BEGIN = f"(?:(?P<assign_name>{PATTERN_NAME})\\s*=)"
PATTERN_MAIN = f"(?P<newline>\\n+)|\\s*(?:(?P<keyword>{PATTERN_KEYWORDS}(?!{PATTERN_NAME_CHARSET}))|(?P<operator>{PATTERN_OPERATOR})|(?P<subscript>{PATTERN_SUBSCRIPT_BEGIN})|(?P<function>{PATTERN_FUNCTION_BEGIN})|(?P<name_value_pair>{PATTERN_NAME_VALUE_PAIR})|(?P<value>{PATTERN_VALUE})|(?P<semicolon>;)|(?P<comma>,)|(?P<parenthesis>\\()|(?P<codeblock>\\{{)|(?P<enclend>[\\]\\)\\}}]))"
PATTERN_FSTRING = f"[^\\S\\r\\n]*(?:(?P<keyword>{"|".join(["and", "or", "not"])})|(?P<operator>{PATTERN_OPERATOR})|(?P<subscript>{PATTERN_SUBSCRIPT_BEGIN})|(?P<function>{PATTERN_FUNCTION_BEGIN})|(?P<name_value_pair>{PATTERN_NAME_VALUE_PAIR})|(?P<value>{PATTERN_VALUE})|(?P<comma>,)|(?P<parenthesis>\\()|(?P<enclend>[\\]\\)])|(?P<fend>\\}}))|(?P<semicolon>{_PATTERN_NO_OP})|(?P<codeblock>{_PATTERN_NO_OP})|(?P<newline>{_PATTERN_NO_OP})"

RE_NAME = re.compile(f"^{PATTERN_NAME}$")
RE_INTEGER = re.compile(f"^{PATTERN_INTEGER_LITERAL}$")
RE_INTEGER_SIGNED = re.compile(f"^\\-?\\s*{PATTERN_INTEGER_LITERAL}$")
RE_MAIN = re.compile(PATTERN_MAIN)
RE_FSTRING = re.compile(PATTERN_FSTRING)

# max told me to call this language Tronix, i'll think abt it 

class ScriptValue[T]:
    def __init__(self, value_type:"ScriptDataType[T]", inner:T):
        self.type = value_type
        self.inner = inner

    def isinstance(self, *dts:"ScriptDataType|ScriptTypeAnnotation"):
        comp_types = []
        for dt in dts:
            if isinstance(dt, ScriptTypeAnnotation):
                if dt.compare(self):
                    return True
            elif dt == BASE_TYPE:
                return True
            else:
                comp_types.append(dt)
        c = self.type
        while c is not BASE_TYPE:
            if c in comp_types:
                return True
            c = c.parent
        return False

class ScriptVariable[T]:
    def __init__(self, value:ScriptValue[T]):
        self.value = value
    
    def type(self):
        return self.value.type

    def get(self)->ScriptValue[T]:
        return self.value
    
    def assign(self, value:ScriptValue[T]):
        self.value = value

class ScriptTypeAnnotation:

    ANNOTATION_NAME:str = None

    @classmethod
    def parse(cls, data:str)->Self:
        raise NotImplementedError

    def __init_subclass__(cls):
        if cls.ANNOTATION_NAME is not None:
            assert cls.ANNOTATION_NAME not in _TYPE_ANNOTATIONS, f"{cls} must define a unique ANNOTATION_NAME"
            _TYPE_ANNOTATIONS[cls.ANNOTATION_NAME] = cls

    def __init__(self, *values):
        raise NotImplementedError

    def __eq__(self, other:"ScriptDataType")->bool:
        raise NotImplementedError
    
    def __ne__(self, other):
        return not (self.__eq__(other))
    
    def compare(self, other:"ScriptValue|Any")->bool:
        raise NotImplementedError
    
    def format_data(self)->str:
        raise NotImplementedError

_TYPE_ANNOTATIONS:dict[str, type[ScriptTypeAnnotation]] = {}

RE_TYPE_ANNOTATION_START = re.compile(f"\\s*(P<name>{PATTERN_NAME})\\s*(?:(P<annotation_start>\\[)|\\s*$)")
def parse_script_type_annotation(s:str):
    m = RE_TYPE_ANNOTATION_START.match(s)
    if m is None:
        raise exceptions.InvalidTypeAnnotationException("Could not parse type annotation", annotation=s)
    name = m["name"]
    annotation_start = m["annotation_start"]
    if annotation_start is None:
        t = name_to_type(name)
        if t is None:
            if name == "null":
                return DATA_TYPE_TABLE[type(None)]
            raise exceptions.AnnotationUnknownTypeException(f"Unknown type: {name}", type_name=name)
        return t
    at = _TYPE_ANNOTATIONS.get(name, None)
    if at is None:
        raise exceptions.UnknownAnnotationException(f"Unknown annotation: {name}", name=name)
    end = s.rfind("]")
    if end == -1 or any(not c.isspace() for c in s[end+1:]):
        raise exceptions.AnnotationEnclosureException("Type annotation was not closed")
    return at.parse(s[m.endpos:end-1])

_TA_ENCL_STARTS = "[("
_TA_ENCL_ENDS = "])"
def split_type_annotation_contents(s:str, seps:str):
    contents:list[str] = []
    start = 0
    encl:int = 0
    enclcount:int = 0
    if not s:
        return contents
    for i, c in enumerate(s):
        c = s[i]
        if c in seps:
            if enclcount:
                continue
            contents.append(s[start:i])
            start = i+1
        elif (encli:=_TA_ENCL_STARTS.find(c)) > -1:
            if enclcount:
                if encli == encl:
                    enclcount += 1
            else:
                encl = encli
                enclcount = 1
        elif c in _TA_ENCL_ENDS:
            if enclcount:
                enclcount -= 1
            else:
                raise exceptions.AnnotationEnclosureException(f"Type annotation has unexpected {repr(c)}")
    if enclcount:
        raise exceptions.AnnotationEnclosureException(f"Type annotation has unmatched: {"".join(_TA_ENCL_STARTS[i] for i in encl)}")
    last = s[start:i]
    if not last.strip():
        contents.append(last)
    return contents

class ScriptDataType[T]:
    """The default datatype containing all the default operation behaviors."""

    def __init__(self, name:str, inner:type[T], parent:"ScriptDataType"):
        self.name = name
        self.inner = inner
        self.parent = parent
        self.__init = False
    
    def issubtype(self, *dts:"ScriptDataType|ScriptTypeAnnotation")->bool:
        if BASE_TYPE in dts:
            return True
        c = self
        while c is not BASE_TYPE:
            if c in dts:
                return True
            c = c.parent
        return False
    
    def parent_chain(self):
        dt = self.parent
        while dt is not BASE_TYPE:
            yield dt
            dt = dt.parent
        yield BASE_TYPE

    def init_subtype(self, subtype:"ScriptDataType"):
        pass

    def init(self):
        if self.__init:
            return self
        chain = list(self.parent_chain())
        for parent in reversed(chain):
            parent.init_subtype(self)
        self.__init = True
        return self

    def serialize(self, value:ScriptValue[T], type_str:bool=False)->Any:
        x = value.inner
        if hasattr(x, "__getstate__"):
            state = x.__getstate__()
            if state is not None:
                return state
        return x
    
    def deserialize(self, x:Any)->T|ScriptValue[T]:
        v = self.inner.__new__(self.inner)
        if hasattr(v, "__setstate__"):
            v.__setstate__(x)
            return ScriptValue(self, v)
        elif isinstance(x, self.inner):
            return ScriptValue(self, x)
        else:
            raise exceptions.TRTypeError(f"could not deserialize data for type {self.name}")

    def construct(self, ctx:"ScriptContext")->ScriptValue:
        return ScriptValue(self, self.inner.__new__())
    
    def conv_str(self, value:ScriptValue[T])->ScriptValue[str]:
        return self.repr(value)

    def conv_bool(self, value:ScriptValue[T])->ScriptValue[bool]:
        return _convert_script_value(bool(value.inner))
    
    def repr(self, value:ScriptValue[T])->ScriptValue[str]:
        return _convert_script_value(f"<value {self.name} at {hex(id(value))}>")
    
    def lt(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner < rhs.get().inner)
    
    def le(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner <= rhs.get().inner)
    
    def gt(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner > rhs.get().inner)
    
    def ge(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner >= rhs.get().inner)
    
    def eq(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner == rhs.get().inner)
    
    def ne(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner != rhs.get().inner)
    
    def add(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner + rhs.get().inner)
    
    def sub(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner - rhs.get().inner)
    
    def mlt(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner * rhs.get().inner)
    
    def div(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner / rhs.get().inner)
    
    def mod(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner % rhs.get().inner)
    
    def iadd(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        l = lhs.get()
        x = l.inner
        x += rhs.get().inner
        if x is l.inner:
            return l
        else:
            return wrap_python_value(x)
    
    def isub(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        l = lhs.get()
        x = l.inner
        x -= rhs.get().inner
        if x is l.inner:
            return l
        else:
            return wrap_python_value(x)
    
    def imlt(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        l = lhs.get()
        x = l.inner
        x *= rhs.get().inner
        if x is l.inner:
            return l
        else:
            return wrap_python_value(x)
    
    def idiv(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        l = lhs.get()
        x = l.inner
        x /= rhs.get().inner
        if x is l.inner:
            return l
        else:
            return wrap_python_value(x)
    
    def imod(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue|None:
        l = lhs.get()
        x = l.inner
        x %= rhs.get().inner
        if x is l.inner:
            return l
        else:
            return wrap_python_value(x)
    
    def uadd(self, h:ScriptVariable[T])->ScriptValue|None:
        return wrap_python_value(+h.get().inner)

    def usub(self, h:ScriptVariable[T])->ScriptValue|None:
        return wrap_python_value(-h.get().inner)

    def unot(self, h:ScriptVariable[T])->ScriptValue|None:
        return wrap_python_value(not h.get().inner)
    
    def getattr(self, obj:ScriptValue[T], name:str)->ScriptValue:
        return wrap_python_value(getattr(obj.inner, name))
    
    def setattr(self, obj:ScriptValue[T], name:str, value:ScriptVariable)->ScriptValue:
        setattr(obj.inner, name, value.get().inner)
        return wrap_python_value(getattr(obj.inner, name))

    def delattr(self, obj:ScriptValue[T], name:str)->ScriptValue:
        v = wrap_python_value(getattr(obj.inner, name))
        delattr(obj.inner, name)
        return v

    def getitem(self, obj:ScriptValue[T], item:ScriptVariable)->ScriptValue:
        return wrap_python_value(obj.inner[item.get().inner])
    
    def setitem(self, obj:ScriptValue[T], item:ScriptVariable, value:ScriptVariable)->ScriptValue:
        obj.inner[item.get().inner] = value.get().inner
        return wrap_python_value(obj.inner[item.get().inner])

    def delitem(self, obj:ScriptValue[T], item:ScriptVariable)->ScriptValue:
        v = wrap_python_value(obj.inner[item.get().inner])
        del obj.inner[item.get().inner]
        return v

    def and_(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue:
        l = lhs.get()
        r = rhs.get()
        if l.type.conv_bool(l).inner:
            return r
        return l

    def or_(self, lhs:ScriptVariable[T], rhs:ScriptVariable)->ScriptValue:
        l = lhs.get()
        r = rhs.get()
        if l.type.conv_bool(l).inner:
            return l
        return r

class ScriptNameValuePair:
    def __init__(self, name:str, value):
        self.name = name
        self.value = value

    def __iter__(self):
        yield self.name
        yield self.value

Namespace = dict[str, ScriptVariable]

class ns_stack:
    def __init__(self, ns:Namespace, prev:Self|None=None):
        self.ns = ns
        self.prev = prev

    def find_name(self, name:str):
        node = self
        while node is not None:
            if name in node.ns:
                return node.ns
            node = node.prev
    
    def pop_name(self, name:str, default=None):
        ns = self.find_name(name)
        if ns is None:
            return default
        return ns.pop(name).get()

class ScriptContext:
    def __init__(self, stack:ns_stack, params:list[ScriptVariable], script:"Script"):
        self.stack = stack
        self.params = params
        self.script = script

FunctionTable = dict[str, Callable[[ScriptContext], ScriptValue]]

SCRIPT_FUNCTION_TABLE:FunctionTable = {}
SCRIPT_GLOBAL_SCOPE:Namespace = {}

class _enclose_stack:
    __slots__ = "c", "end", "pnode", "basenode", "r", "prev"
    def __init__(self, c:str, end:str, pnode:ParsingNode, basenode:ParsingNode, r:Match|None=None, prev:Self|None=None):
        self.c = c
        self.end = end
        self.pnode = pnode
        self.basenode = basenode
        self.r = r
        self.prev = prev


_VA_NAME = object()
_VA_SUBSCRIPT = object()

class _va_path_node:
    def __init__(self, value, type):
        self.value = value
        self.type = type

class _variable_access:
    def __init__(self, path:list[_va_path_node], value_root:ScriptVariable|ScriptValue|None=None):
        self.path = path
        self.value_root = value_root

    async def resolve(self, stack:ns_stack, slice_end:int=None)->ScriptVariable|ScriptValue|None:
        if slice_end is None:
            slice_end = len(self.path)
            
        if self.value_root is None:
            first = self.path[0]
            if first.type is not _VA_NAME:
                raise exceptions._TronixRuntimeAssertion("variable access first path node cannot be a subscript without a root value")
            ns = stack.find_name(first.value)
            if ns is None:
                return None
            target = ns[first.value]
            i = 1
        elif isinstance(self.value_root, (ScriptValue, ScriptVariable)):
            target = self.value_root
            i = 0
        
        subpath = self.path[i:slice_end]
        if not subpath:
            return target
        
        if isinstance(target, ScriptVariable):
            target = target.get()
        for node in subpath:
            if node.type is _VA_NAME:
                target = target.type.getattr(target, node.value)
            elif node.type is _VA_SUBSCRIPT:
                target = target.type.getitem(target, await node.value())
            else:
                raise exceptions._TronixRuntimeAssertion("variable access path node has unrecognized type")
        return target

class _step_evaluation:
    def __init__(self, cb:Callable[[],Awaitable]=None):
        self.cb = cb

    def __call__(self):
        return self.cb()
    
    def __bool__(self):
        return self.cb is not None
    
class _step_expansion:
    def __init__(self, new_ns_stackframe:bool=True, handle_step_control:bool=False):
        self.new_ns_stackframe = new_ns_stackframe
        self.handle_step_control = handle_step_control

    async def __aiter__(self):
        raise NotImplementedError

_STEP_CONTROL_TOP = 1
_STEP_CONTROL_BREAK = 2
_STEP_CONTROL_SKIP = 4
_STEP_CONTROL_EXCEPTION = 8

_DEFAULT_CONTROL_FLAGS_MASK = _STEP_CONTROL_TOP | _STEP_CONTROL_BREAK | _STEP_CONTROL_SKIP

class _step_control:
    def __init__(self, flags:int, value:int=0, exc:Exception|None=None):
        self.flags = flags
        self.value = value
        self.exc = exc

class _fixed_step_expansion(_step_expansion):
    def __init__(self, steps:list[Callable[[],Awaitable]], new_ns_stackframe:bool=True, handle_step_control:bool=False, control_flags_mask:int=_DEFAULT_CONTROL_FLAGS_MASK):
        super().__init__(new_ns_stackframe, handle_step_control)
        self.steps = steps
        self.control_flags_mask = control_flags_mask

    async def __aiter__(self):
        i = 0
        while i < len(self.steps):
            control = yield self.steps[i]
            if isinstance(control, _step_control):
                if self.handle_step_control:
                    flags = control.flags & self.control_flags_mask
                    if control.exc is not None:
                        raise control.exc
                    if flags & _STEP_CONTROL_BREAK:
                        return
                    elif flags & _STEP_CONTROL_TOP:
                        i = 0
                    elif flags & _STEP_CONTROL_SKIP:
                        i += max(1, control.value)
                elif control.exc is not None:
                    raise control.exc
                else:
                    break
            i += 1

class _catch_step_expansion(_fixed_step_expansion):
    def __init__(self, steps:list[Callable[[],Awaitable]], exc_callback:Callable[[Exception],Awaitable], new_ns_stackframe:bool=True, handle_step_control:bool=True, control_flags_mask:int=_DEFAULT_CONTROL_FLAGS_MASK|_STEP_CONTROL_EXCEPTION):
        super().__init__(steps, new_ns_stackframe, handle_step_control, control_flags_mask)
        self.exc_callback = exc_callback

    async def __aiter__(self):
        i = 0
        while i < len(self.steps):
            control = yield self.steps[i]
            if isinstance(control, _step_control):
                if self.handle_step_control:
                    flags = control.flags & self.control_flags_mask
                    if control.exc is not None:
                        if flags & _STEP_CONTROL_EXCEPTION:
                            await self.exc_callback(control.exc)
                        else:
                            raise control.exc
                    if flags & _STEP_CONTROL_BREAK:
                        return
                    elif flags & _STEP_CONTROL_TOP:
                        i = 0
                    elif flags & _STEP_CONTROL_SKIP:
                        i += max(1, control.value)
                elif control.exc is not None:
                    raise control.exc
            i += 1

class _indefinite_step_expansion(_step_expansion):
    def __init__(self, condition:Callable[[], Awaitable[bool]], next_steps:Callable[[], Iterable[Callable[[], Awaitable]]], new_ns_stackframe:bool=True, handle_step_control:bool=False, control_flags_mask:int|None=None):
        super().__init__(new_ns_stackframe, handle_step_control)
        self.condition = condition
        self.next_steps = next_steps
        self.control_flags_mask = _DEFAULT_CONTROL_FLAGS_MASK if control_flags_mask is None else control_flags_mask

    async def __aiter__(self):
        skip_yield = 0
        while await self.condition():
            for step in self.next_steps():
                if skip_yield:
                    skip_yield -= 1
                    continue
                control = yield step
                if isinstance(control, _step_control):
                    if self.handle_step_control:
                        flags = control.flags & self.control_flags_mask
                        if control.exc is not None:
                            raise control.exc
                        if flags & _STEP_CONTROL_BREAK:
                            return
                        elif flags & _STEP_CONTROL_TOP:
                            break
                        elif flags & _STEP_CONTROL_SKIP:
                            skip_yield = max(1, control.value)
                    elif control.exc is not None:
                        raise control.exc
                        

class step_stack_node:
    def __init__(self, parent:"step_stack_node|None", steps:list[Callable[[],Any]]):
        self.parent = parent
        self.steps = steps

    def create_exp_step(self, new_ns_stackframe:bool=True):
        exp = _fixed_step_expansion(self.steps, new_ns_stackframe=new_ns_stackframe)
        async def _step():
            return exp
        return _step


_escape_character_mapping = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "\n": "",
    "\\": "\\",
    "'": "'",
    "\"": "\"",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "v": "\v"
}

_operator_order = [
    {".", "u[]"},
    {"-u", "+u", "notu"},
    {"*", "/", "%"},
    {"+", "-"},
    {"==", "!=", ">=", "<=", ">", "<"},
    {"=", "+=", "-=", "*=", "/=", "%="},
    {"and", "or"}
]

#operator associativity for order sets, True is left-to-right, False is right-to-left. doesn't especially matter for unary
_operator_direction = {
    0: True,
    1: True,
    2: True,
    3: True,
    4: True,
    5: False,
    6: True
}


_operator_order_index = {k:i for i, so in enumerate(_operator_order) for k in so} #maps each operator to the index of its order set

BASE_TYPE = ScriptDataType("any", object, None); BASE_TYPE.parent = BASE_TYPE

DATA_TYPE_TABLE:dict[type, ScriptDataType] = {
    object: BASE_TYPE
}

_name_to_datatype:dict[str, ScriptDataType] = {}

def _convert_script_value[T](value:T):
    t = DATA_TYPE_TABLE.get(type(value), None)
    if t is None:
        return None
    return ScriptValue(t, value)

def name_to_type(name:str):
    t = _name_to_datatype.get(name, None)
    if t is None:
        for dt in DATA_TYPE_TABLE.values():
            _name_to_datatype[dt.name] = dt
            if dt.name == name:
                return dt
    return t

def wrap_python_value[T](value:T|ScriptValue[T]):
    if isinstance(value, ScriptValue):
        return value
    v = _convert_script_value(value)
    if v is None:
        t = type(value)
        st = wrap_python_type(t)
        v = ScriptValue[T](st, value)
    return v

def _resolve_dynamic_type_creation(sup:type, mro:list[type], override_names:dict[str,str]|None)->tuple[ScriptDataType, type[ScriptDataType]]:
    supt = DATA_TYPE_TABLE.get(sup, None)
    if supt is None:
        parent, super_t = _resolve_dynamic_type_creation(mro[0], mro[1:], override_names)
        class _DynamicScriptDataType(super_t):
            pass
        n = sup.__name__
        return _DynamicScriptDataType(n if override_names is None else override_names.get(sup, n), sup, parent).init(), super_t
    else:
        return supt, type(supt)

def wrap_python_type(t:type|ScriptDataType, update_table:bool=True, override_names:str|dict[type,str]|None=None):
    if isinstance(t, ScriptDataType):
        return t
    st = DATA_TYPE_TABLE.get(t, None)
    if st is not None:
        return st

    n = t.__name__
    mro = t.mro()
    parent, super_t = _resolve_dynamic_type_creation(mro[0], mro[1:], override_names if isinstance(override_names, dict) else None)
    class _DynamicScriptDataType(super_t):
        pass
    st = _DynamicScriptDataType(
        n if override_names is None else override_names if isinstance(override_names, str) else override_names.get(t, n),
        t, parent
    )

    if update_table:
        DATA_TYPE_TABLE[t] = st.init()
        return st
    else:
        return st.init()

class Script:

    HASH_FUNC = hashlib.md5

    def __init__(self, raw:str, scope:Namespace=None, global_scope:Namespace=SCRIPT_GLOBAL_SCOPE, function_table:FunctionTable=SCRIPT_FUNCTION_TABLE, loud_expressions:bool=False):
        self.raw = raw
        self._hash = self.HASH_FUNC(raw.encode("utf-8"), usedforsecurity=False).digest()
        self.scope = {} if scope is None else scope
        self.global_scope = global_scope
        self.function_table = function_table
        self.steps:list[Callable[[],Any]] = []
        self.stack = ns_stack(self.scope, ns_stack(global_scope))
        self.steps_stack = step_stack_node(None, self.steps)
        self.steps_debug:weakref.WeakKeyDictionary[Callable[[], Any], ParsingNode] = weakref.WeakKeyDictionary()
        self.loud_expressions = loud_expressions
    
    def parse(self, context_name:str="")->ParsingNode:
        i = 0
        root = ParsingNode(ParsingContext(i, None, context_name))
        current = root
        enclstack:_enclose_stack|None = None

        def end_condition():
            nonlocal current
            if isinstance(current, ParsingNodeConditionPair):
                #if has condition and missing codeblock
                if current.condition is not None and current.codeblock is None:
                    raise exceptions.TPExpectedSymbol("{ expected here", ctx=exceptions.ExceptionContext(current))
                elif current.codeblock is not None: #if has codeblock
                    current = current.parent.parent
                return True
            return False

        def end_loop():
            nonlocal current
            if isinstance(current, ParsingNodeLoopStatement) and current.children and isinstance(current.children[-1], ParsingNodeCodeBlock):
                current = current.parent
                return True
            return False

        def end_catch():
            nonlocal current
            if isinstance(current, ParsingNodeCatchStatement) and current.children and isinstance(current.children[-1], ParsingNodeCodeBlock):
                current = current.parent
                return True
            return False

        def end_loopexpr():
            nonlocal current
            if isinstance(current, ParsingNodeLoopExpression):
                current = current.parent
                return True
            return False

        def loopexpr_wrap_statement(i:int, r:Match|None, context_name:str, ctx_parent:ParsingContext|None):
            nonlocal current
            if isinstance(current, ParsingNodeLoopStatement):
                node = ParsingNodeLoopExpression(ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
                current = node

        def wrap_statement(i:int, r:Match|None, context_name:str, ctx_parent:ParsingContext|None):
            nonlocal current
            if not isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                end_condition() or end_loop() or end_catch()
                loopexpr_wrap_statement(i, r, context_name, ctx_parent)
                exprnode = ParsingNodeExpression(ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(exprnode)
                current = exprnode

        def look_nvpair():
            if isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                ln = current.parent
            else:
                ln = current
            if isinstance(ln, ParsingNodeNVPair) and ln.value is not None:
                return ln
            return None

        def end_nvpair():
            nonlocal current
            looknode:ParsingNodeNVPair|None = look_nvpair()
            if looknode is not None:
                if not isinstance(looknode.value, (ParsingNodeExpression, ParsingNodeParentheses)):
                    raise exceptions.TPExpectedEvaluable(
                        "expected evaluable expression as value for name-value pair",
                        ctx=exceptions.ExceptionContext(looknode)
                    )
                current = looknode.parent

        def fail_vardecl(i:int, r:Match|None, context_name:str, ctx_parent:ParsingContext|None):
            if isinstance(current, ParsingNodeVarDecl):
                raise exceptions.TPExpectedName(
                    "expected variable name",
                    ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                )

        def eof_check(i:int, r:Match|None, context_name:str, ctx_parent:ParsingContext|None):
            if enclstack is not None:
                raise exceptions.TPUnexpectedEndOfCode(
                    f"{enclstack.c} is never matched (expected {repr(enclstack.end)})",
                    ctx=exceptions.ExceptionContext(lambda_node(i, enclstack.r, context_name, ctx_parent))
                )
            node = current
            while node is not root:
                if isinstance(node, ParsingNodeConditionPair):
                    if node.condition is None and node.takes_condition or node.codeblock is None:
                        end = exceptions._get_i_end(node)
                        raise exceptions.TPUnexpectedEndOfCode(
                            f"{"if" if node.takes_condition else "else"} statement is incomplete",
                            ctx=exceptions.ExceptionContext(lambda_node(end, r, context_name, ctx_parent, end+3))
                        )
                elif isinstance(node, ParsingNodeLoopExpression) or (
                    isinstance(node, ParsingNodeLoopStatement) and
                    not (node.children and isinstance(node.children[-1], ParsingNodeCodeBlock))):
                    end = exceptions._get_i_end(node)
                    raise exceptions.TPUnexpectedEndOfCode(
                        "loop statement is incomplete",
                        ctx=exceptions.ExceptionContext(lambda_node(end, r, context_name, ctx_parent, end+3))
                    )
                elif isinstance(node, ParsingNodeCatchStatement) and not node.children:
                    end = exceptions._get_i_end(node)
                    raise exceptions.TPUnexpectedEndOfCode(
                        "catch statement is incomplete",
                        ctx=exceptions.ExceptionContext(lambda_node(end, r, context_name, ctx_parent, end+3))
                    )
                elif isinstance(node, ParsingNodeNVPair) and node.value is None:
                    end = exceptions._get_i_end(node)
                    raise exceptions.TPUnexpectedEndOfCode(
                        "name-value pair is incomplete",
                        ctx=exceptions.ExceptionContext(lambda_node(end, r, context_name, ctx_parent, end+3))
                    )
                node = node.parent


        def lambda_node(i:int, r:Match|None, context_name:str, ctx_parent:ParsingContext|None, i_end:int|None=None):
            return ParsingNode(ParsingContext(i, r, context_name, ctx_parent, i_end), current)

        def check_loopcontrol():
            node = current
            block = False
            while node is not None:
                if isinstance(node, ParsingNodeCodeBlock):
                    block = True
                elif isinstance(node, ParsingNodeLoopStatement):
                    return block
                node = node.parent
            return False

        def handle_match(i:int, r:Match[str], context_name:str, ctx_parent:ParsingContext|None=None):
            nonlocal current, enclstack, root
            if r["newline"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                looknode:ParsingNodeNVPair|None = look_nvpair()
                if looknode is not None:
                    if looknode.value and not isinstance(looknode.children[-1], ParsingNodeOperator):
                        current = looknode.parent
                if isinstance(current, ParsingNodeExpression) and (current.parent is root or isinstance(current.parent, ParsingNodeCodeBlock)) and not isinstance(current.children[-1], ParsingNodeOperator):
                    current = current.parent
            elif (keyword := r["keyword"]) is not None:
                if look_nvpair():
                    raise exceptions.TPUnexpectedKeyword(
                        f"keyword not expected here",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
                if keyword == "if":
                    fail_vardecl(i, r, context_name, ctx_parent)
                    if isinstance(current, ParsingNodeConditionPair):
                        if current.condition is None and current.codeblock is None:
                            current.takes_condition = True
                            return
                        elif current.takes_condition == (current.condition is not None) and current.codeblock is not None:
                            current = current.parent.parent
                        else:
                            raise exceptions.TPUnexpectedKeyword(
                                "keyword \"if\" not expected here",
                                ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                            )
                    if isinstance(current, ParsingNodeExpression):
                        current = current.parent
                    if not (current is root or isinstance(current, ParsingNodeCodeBlock)):
                        raise exceptions.TPUnexpectedKeyword(
                            "keyword \"if\" not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    node = ParsingNodeIfStatement(ParsingContext(i, r, context_name, ctx_parent), current)
                    cond = ParsingNodeConditionPair(ParsingContext(i, r, context_name, ctx_parent), node, takes_condition=True)
                    node.children.append(cond)
                    current.children.append(node)
                    current = cond
                elif keyword == "else":
                    fail_vardecl(i, r, context_name, ctx_parent)
                    while current is not None:
                        if isinstance(current, ParsingNodeConditionPair):
                            break
                        current = current.parent
                    if current is None or current.condition is None or current.codeblock is None:
                        raise exceptions.TPUnexpectedKeyword(
                            "keyword \"else\" not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    current = current.parent
                    cond = ParsingNodeConditionPair(ParsingContext(i, r, context_name, ctx_parent), current)
                    current.children.append(cond)
                    current = cond
                elif keyword == "loop":
                    fail_vardecl(i, r, context_name, ctx_parent)
                    if isinstance(current, ParsingNodeExpression):
                        current = current.parent
                    if not (current is root or isinstance(current, ParsingNodeCodeBlock)):
                        raise exceptions.TPUnexpectedKeyword(
                            f"keyword {repr(keyword)} not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    node = ParsingNodeLoopStatement(ParsingContext(i, r, context_name, ctx_parent), current)
                    current.children.append(node)
                    current = node
                elif keyword == "catch":
                    fail_vardecl(i, r, context_name, ctx_parent)
                    if isinstance(current, ParsingNodeExpression):
                        current = current.parent
                    if not (current is root or isinstance(current, ParsingNodeCodeBlock)):
                        raise exceptions.TPUnexpectedKeyword(
                            f"keyword {repr(keyword)} not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    node = ParsingNodeCatchStatement(ParsingContext(i, r, context_name, ctx_parent), current)
                    current.children.append(node)
                    current = node
                elif keyword in ("global", "var", "define"):
                    fail_vardecl(i, r, context_name, ctx_parent)
                    loopexpr_wrap_statement(i, r, context_name, ctx_parent)
                    if not (current is root or isinstance(current, (ParsingNodeCodeBlock, ParsingNodeLoopExpression))):
                        raise exceptions.TPUnexpectedKeyword(
                            f"keyword {repr(keyword)} not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    node = ParsingNodeVarDecl(ParsingContext(i, r, context_name, ctx_parent), keyword, current)
                    current.children.append(node)
                    current = node
                elif keyword in ("not","and","or"):
                    fail_vardecl(i, r, context_name, ctx_parent)
                    wrap_statement(i, r, context_name, ctx_parent)
                    node = ParsingNodeOperator(keyword, ParsingContext(i, r, context_name, ctx_parent), current)
                    current.children.append(node)
                elif keyword in ("break", "skip"):
                    fail_vardecl(i, r, context_name, ctx_parent)
                    if not check_loopcontrol():
                        raise exceptions.TPUnexpectedKeyword(
                            f"keyword {repr(keyword)} not expected here",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    if keyword == "break":
                        flags = _STEP_CONTROL_BREAK
                    else:
                        flags = _STEP_CONTROL_TOP
                    node = ParsingNodeLoopControl(flags, 0, ParsingContext(i, r, context_name, ctx_parent), current)
                    current.children.append(node)
            elif r["function"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                wrap_statement(i, r, context_name, ctx_parent)
                node = ParsingNodeFunction(r["function_name"], ParsingContext(i, r, context_name), current)
                current.children.append(node)
                enclstack = _enclose_stack("(",")", node, current, r, enclstack)
                current = node
            elif r["name_value_pair"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                name = r["name_value_pair_name"]
                wrap_statement(i, r, context_name, ctx_parent)
                nvpair = ParsingNodeNVPair(ParsingContext(i, r, context_name, ctx_parent), current)
                nnode = ParsingNodeName(name, ParsingContext(i, r, context_name, ctx_parent), nvpair)
                nvpair.children.append(nnode)
                current.children.append(nvpair)
                current = nvpair
            elif r["value"] is not None:
                v_name = r["value_name"]
                v_string = r["value_string"]
                v_integer = r["value_integer"]
                v_float = r["value_float"]
                v_bool = r["value_bool"]
                v_null = r["value_null"]
                escape_current = False
                if v_name:
                    if isinstance(current, ParsingNodeVarDecl):
                        escape_current = True
                    elif not isinstance(current, ParsingNodeCatchStatement):
                        wrap_statement(i, r, context_name, ctx_parent)
                    node = ParsingNodeName(v_name, ParsingContext(i, r, context_name, ctx_parent), current)
                else:
                    fail_vardecl(i, r, context_name, ctx_parent)
                    wrap_statement(i, r, context_name, ctx_parent)
                    if v_string and v_string[0] == "f":
                        vs = v_string[2:-1] #strip off the quotes
                        chars = []
                        ci = 0
                        node = ParsingNodeFString(ParsingContext(i, r, context_name, ctx_parent), current)
                        old_root = root
                        root = current = node
                        while ci < len(vs):
                            c = vs[ci]
                            if c == "\\":
                                ci += 1
                                c = vs[ci]
                                ec = _escape_character_mapping.get(c, None)
                                if ec:
                                    chars.append(ec)
                                elif c == "u":
                                    chars.append(chr(int(vs[ci+1:ci+5], 16)))
                                    ci += 4 #(ci + 5 - 1) + 1
                                elif c == "U":
                                    chars.append(chr(int(vs[ci+1:ci+9], 16)))
                                    ci += 8
                                elif c == "o":
                                    chars.append(chr(int(vs[ci+1:ci+3], 8)))
                                    ci += 2
                                elif c == "x":
                                    chars.append(chr(int(vs[ci+1:ci+3], 16)))
                                    ci += 2
                                else:
                                    chars.append(f"\\{c}")
                                ci += 1
                            elif c == "{":
                                ci += 1
                                in_expression = True
                                fi = i+ci+2
                                if chars:
                                    current.children.append(ParsingNodeValue("".join(chars), ParsingContext(fi-len(chars), r, context_name, ctx_parent), current))
                                    chars.clear()
                                node = ParsingNodeExpression(ParsingContext(fi, None, context_name, ctx_parent), current)
                                current.children.append(node)
                                current = node
                                while in_expression:
                                    fr = RE_FSTRING.match(vs, pos=ci)
                                    if fr is None:
                                        if vs[ci:].strip():
                                            raise exceptions.TParsingException(
                                                "f-string: unrecognizable syntax",
                                                ctx=exceptions.ExceptionContext(lambda_node(fi, fr, context_name, ctx_parent))
                                            )
                                        else:
                                            ... #TODO unexpected end of f-string
                                    if fr["fend"] is not None:
                                        in_expression = False
                                    elif handle_match(fi, fr, context_name, ctx_parent):
                                        ... #TODO unexpected end of f-string
                                    ci += fr.end() - ci
                                current = root
                            else:
                                chars.append(c)
                                ci += 1
                        if chars:
                            root.children.append(ParsingNodeValue("".join(chars), ParsingContext(ci+i+2-len(chars), r, context_name, ctx_parent), root))
                        node = root
                        current = root.parent
                        root = old_root
                    else:
                        if v_string:
                            vs = v_string[1:-1] #strip off the quotes
                            chars = []
                            ci = 0
                            while ci < len(vs):
                                c = vs[ci]
                                if c == "\\":
                                    ci += 1
                                    c = vs[ci]
                                    ec = _escape_character_mapping.get(c, None)
                                    if ec:
                                        chars.append(ec)
                                    elif c == "u":
                                        chars.append(chr(int(vs[ci+1:ci+5], 16)))
                                        ci += 4 #(ci + 5 - 1) + 1
                                    elif c == "U":
                                        chars.append(chr(int(vs[ci+1:ci+9], 16)))
                                        ci += 8
                                    elif c == "o":
                                        chars.append(chr(int(vs[ci+1:ci+3], 8)))
                                        ci += 2
                                    elif c == "x":
                                        chars.append(chr(int(vs[ci+1:ci+3], 16)))
                                        ci += 2
                                    else:
                                        chars.append(f"\\{c}")
                                else:
                                    chars.append(c)
                                ci += 1
                            value = "".join(chars)
                        elif v_integer:
                            value = int(v_integer)
                        elif v_float:
                            value = float(v_float)
                        elif v_bool:
                            value = bool(v_bool == "true")
                        elif v_null:
                            value = None
                        else:
                            raise exceptions.TPUnknownValue(
                                f"unknown value",
                                ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                            )
                        node = ParsingNodeValue(value, ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
                if escape_current:
                    current = current.parent
            elif (operator := r["operator"]) is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                wrap_statement(i, r, context_name, ctx_parent)
                node = ParsingNodeOperator(operator, ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
            elif r["parenthesis"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                wrap_statement(i, r, context_name, ctx_parent)
                node = ParsingNodeParentheses(ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
                enclstack = _enclose_stack("(",")", node, current, r, enclstack)
                current = node
            elif r["subscript"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                node = ParsingNodeSubscript(ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
                enclstack = _enclose_stack("[","]", node, current, r, enclstack)
                current = node
            elif r["codeblock"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                if not (enclstack is None or isinstance(enclstack.pnode, ParsingNodeCodeBlock)):
                    raise exceptions.TPUnexpectedSymbol(
                        "{ unexpected here",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
                if isinstance(current, ParsingNodeExpression):
                    current = current.parent
                if isinstance(current, ParsingNodeConditionPair):
                    if current.takes_condition and current.condition is None:
                        raise exceptions.TPExpectedEvaluable(
                            "expected evaluable expression as if statement condition but got code block instead",
                            ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                        )
                    elif current.codeblock is not None:
                        current = current.parent.parent
                    basenode = current
                elif isinstance(current, ParsingNodeLoopExpression):
                    current = current.parent
                    basenode = current.parent
                elif isinstance(current, ParsingNodeCatchStatement):
                    basenode = current.parent
                else:
                    basenode = current
                node = ParsingNodeCodeBlock(ParsingContext(i, r, context_name, ctx_parent), current)
                current.children.append(node)
                enclstack = _enclose_stack("{","}", node, basenode, r, enclstack)
                current = node
            elif (enclend := r["enclend"]) is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                if enclstack is None:
                    raise exceptions.TPEnclMismatch(
                        f"unmatched {enclend}",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
                elif enclstack.end != enclend:
                    raise exceptions.TPEnclMismatch(
                        f"closing {enclend} does not match opening {enclstack.c}",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
                enclstack.pnode.ctx.i_end = r.end()
                current = enclstack.basenode
                enclstack = enclstack.prev
            elif r["comma"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                if enclstack is not None and isinstance(enclstack.pnode, ParsingNodeFunction):
                    current = enclstack.pnode
                    current.children.append(ParsingNodeComma(ParsingContext(i, r, context_name, ctx_parent), current))
                else:
                    raise exceptions.TPUnexpectedSymbol(
                        "unexpected here",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
            elif r["semicolon"] is not None:
                fail_vardecl(i, r, context_name, ctx_parent)
                end_nvpair()
                end_condition() or end_loop() or end_catch() or end_loopexpr()
                if not (enclstack is None or isinstance(enclstack.pnode, ParsingNodeCodeBlock)) or look_nvpair():
                    raise exceptions.TPUnexpectedSymbol(
                        "unexpected here",
                        ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                    )
                while current is not root:
                    if isinstance(current, (ParsingNodeCodeBlock, ParsingNodeIfStatement, ParsingNodeLoopStatement)):
                        break
                    current = current.parent
                else:
                    current = root
            elif enclstack is not None:
                raise exceptions.TPExpectedSymbol(
                    f"{enclstack.end} expected here",
                    ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                )
            elif isinstance(current, ParsingNodeConditionPair) and current.codeblock is None:
                raise exceptions.TPExpectedSymbol(
                    "{ expected here",
                    ctx=exceptions.ExceptionContext(lambda_node(i, r, context_name, ctx_parent))
                )
            else:
                return True
            
        #build the parse tree
        while True:
            r = RE_MAIN.match(self.raw, pos=i)
            if r is None:
                if self.raw[i:].strip():
                    raise exceptions.TParsingException(
                        "unrecognizable syntax",
                        ctx=exceptions.ExceptionContext(lambda_node(i, None, context_name, None))
                    )
                else:
                    fail_vardecl(i, r, context_name, None)
                    eof_check(i, r, context_name, None)
                return root
            if handle_match(i, r, context_name):
                fail_vardecl(i, r, context_name, None)
                eof_check(i, r, context_name, None)
                return root
            i += r.end() - i

    def _generate_function_call_step(self, node:ParsingNodeFunction, params:list[Callable[[], Awaitable]], paramnodes:list[ParsingNode]):
        async def _function_step(): #evaluable step: step function 
            if node.function_name in self.function_table:
                function = self.function_table[node.function_name]
                evaluated_params:list[ScriptVariable] = []
                va_params:dict[int, tuple[_variable_access, ScriptValue]] = {}
                for i, (paramnode, pf) in enumerate(zip(paramnodes, params)):
                    param = await pf()
                    if isinstance(param, _variable_access):
                        _va = param
                        x = await param.resolve(self.stack)
                        if x is None:
                            raise exceptions.TRMissingName(
                                f"{repr(param.path[0].value)} not found",
                                param.path[0].value,
                                ctx=exceptions.ExceptionContext(paramnode, _function_step)
                            )
                        else:
                            param = x
                    else:
                        _va = None
                    if isinstance(param, ScriptValue): #if this is ScriptValue then len(path) > 1
                        if _va:
                            va_params[i] = _va, param
                        param = ScriptVariable(param)
                    evaluated_params.append(param)

                local_ns = {}
                self.stack = ns_stack(local_ns, self.stack) #push
                ctx = ScriptContext(stack=self.stack, params=evaluated_params, script=self)
                try:
                    value = function(ctx)
                    if inspect.isawaitable(value):
                        value = await value
                except NotImplementedError as e:
                    raise exceptions.TRNotImplemented(
                        f"function {repr(node.function_name)} is not implemented",
                        ctx=exceptions.ExceptionContext(node, _function_step)
                    ) from e
                except Exception as e:
                    raise exceptions.wrap(e)
                if value is NotImplemented:
                    raise exceptions.TRNotImplemented(
                        f"function {repr(node.function_name)} is not implemented",
                        ctx=exceptions.ExceptionContext(node, _function_step)
                    )
                self.stack = self.stack.prev #pop
                for i, (va, val) in va_params.items():
                    l = await va.resolve(self.stack, -1)
                    if l is None:
                        raise exceptions.TRMissingName(
                            f"{repr(va.path[0].value)} not found",
                            va.path[0].value,
                            ctx=exceptions.ExceptionContext(paramnode, _function_step)
                        )
                    if isinstance(l, ScriptVariable):
                        l = l.get()
                    plast = va.path[-1]
                    if plast.type is _VA_SUBSCRIPT:
                        f = l.type.setitem
                        args = l, await plast.value()
                    else:
                        f = l.type.setattr
                        args = l, plast.value

                    param = evaluated_params[i]
                    if param.get() is val:
                        continue
                    try:
                        x = f(*args, param)
                    except NotImplementedError as e:
                        raise exceptions.TRNotImplemented(
                            "function assigned to parameter, but assign is not implemented",
                            ctx=exceptions.ExceptionContext(paramnodes[i], _function_step)
                        ) from e
                    except Exception as e:
                        raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(paramnodes[i], _function_step))
                    if x is NotImplemented:
                        raise exceptions.TRNotImplemented(
                            "function assigned to parameter, but assign is not implemented",
                            ctx=exceptions.ExceptionContext(paramnodes[i], _function_step)
                        )
                return value
            else:
                raise exceptions.TRMissingFunction(f"cannot find function {repr(node.function_name)}", ctx=exceptions.ExceptionContext(node, _function_step))
        self.steps_debug[_function_step] = node
        return _function_step

    def _generate_function_steps(self, node:ParsingNodeFunction, rtv:_step_evaluation|None=None):
        params:list[Callable[[],Any]] = []
        param:Callable[[],Any]|None = None
        paramnodes:list[ParsingNodeExpression|ParsingNodeParentheses|ParsingNodeFunction] = []
        for child in node.children:
            if isinstance(child, ParsingNodeComma):
                if param is None:
                    raise exceptions.TCIncorrectParamaterOrder("comma is not following a parameter", ctx=exceptions.ExceptionContext(child))
                params.append(param)
                param = None
                continue
            elif param is not None:
                raise exceptions.TCIncorrectParamaterOrder("consecutive parameters without a comma", ctx=exceptions.ExceptionContext(child))
                
            if isinstance(child, ParsingNodeFunction):
                param = _step_evaluation()
                self._generate_function_steps(child, param)
            elif isinstance(child, (ParsingNodeExpression, ParsingNodeParentheses)):
                param = _step_evaluation()
                self._generate_expression_steps(child, param)
            else:
                assert False, f"Unexpected node: {child}"
            paramnodes.append(child)

        if param is not None:
            params.append(param)

        step_cb = self._generate_function_call_step(node, params, paramnodes)
        if rtv is None:
            self.steps_stack.steps.append(step_cb)
        else:
            rtv.cb = step_cb

    def _get_expression_operations(self, node:ParsingNodeExpression|ParsingNodeParentheses)->operation_node:
        operators:list[tuple[int, str, ParsingNodeOperator|ParsingNodeSubscript, int]] = []
        lh = None
        root_precedence_level = -1
        root_index = None
        root_direction = None
        for i, child in enumerate(node.children):
            issubscript = isinstance(child, ParsingNodeSubscript)
            if issubscript or isinstance(child, ParsingNodeOperator):
                if issubscript:
                    assert lh is not None, "subscript must have left-hand value"
                    operator = "u[]"
                elif lh is None:
                    operator = f"{child.operator}u"
                else:
                    operator = child.operator
                    lh = None

                precedence = _operator_order_index.get(operator, None)
                assert precedence is not None, f"Missing compilation data for handling operator: {operator}"

                oi = len(operators)
                operators.append((i, operator, child, precedence))
                
                if precedence > root_precedence_level:
                    root_precedence_level = precedence
                    root_index = oi
                    root_direction = _operator_direction[precedence]
                elif precedence == root_precedence_level:
                    if root_direction and oi > root_index:
                        root_index = oi
                    #no other checks needed cause right-left associativity (False direction) needs the first operator as the root
            elif lh is None:
                lh = child
            else:
                raise exceptions.TCIncorrectOperandOrder("consecutive operands where operator is expected", ctx=exceptions.ExceptionContext(child))

        if root_index is None:
            return None #no operators, node only contains a value
        
        def _left_construct(midpoint:int, parent:operation_node, bounds:tuple[int, int]):
            if parent.operation.endswith("u"):
                return
            
            plevel = -1
            next_midpoint = None
            next_direction = None
            for i  in range(bounds[0], midpoint):
                *_, p = operators[i]
                if p > plevel:
                    plevel = p
                    next_midpoint = i
                    next_direction = _operator_direction[p]
                elif p == plevel:
                    if next_direction and i > next_midpoint:
                        next_midpoint = i

            if next_midpoint is None:
                lhand = node.children[parent.position-1]
                if isinstance(lhand, (ParsingNodeParentheses, ParsingNodeExpression)):
                    l = self._get_expression_operations(lhand)
                    if l is None:
                        if len(lhand.children) == 1:
                            lhand = lhand.children[0]
                        else:
                            raise exceptions.TCInvalidOperand("invalid expression", ctx=exceptions.ExceptionContext(lhand))
                    else:
                        lhand = l
                parent.lhand = lhand
            else:
                next = operation_node(*operators[next_midpoint], None, None)
                parent.lhand = next
                _left_construct(next_midpoint, next, (bounds[0], next_midpoint-1))
                _right_construct(next_midpoint, next, (next_midpoint+1, bounds[1]))
        
        def _right_construct(midpoint:int, parent:operation_node, bounds:tuple[int, int]):
            if parent.operation.startswith("u"):
                return
            
            plevel = -1
            next_midpoint = None
            next_direction = None
            for i in range(midpoint+1, bounds[1]+1):
                *_, p = operators[i]
                if p > plevel:
                    plevel = p
                    next_midpoint = i
                    next_direction = _operator_direction[p]
                elif p == plevel:
                    if next_direction and i > next_midpoint:
                        next_midpoint = i
            
            if next_midpoint is None:
                rhand = node.children[parent.position+1]
                if isinstance(rhand, (ParsingNodeParentheses, ParsingNodeExpression)):
                    r = self._get_expression_operations(rhand)
                    if r is None:
                        if len(rhand.children) == 1:
                            rhand = rhand.children[0]
                        else:
                            raise exceptions.TCInvalidOperand("invalid expression", ctx=exceptions.ExceptionContext(rhand))
                    else:
                        rhand.ctx.optree = r
                        rhand = r
                parent.rhand = rhand
            else:
                next = operation_node(*operators[next_midpoint], None, None)
                parent.rhand = next
                _left_construct(next_midpoint, next, (bounds[0], next_midpoint-1))
                _right_construct(next_midpoint, next, (next_midpoint+1, bounds[1]))

        root = operation_node(*operators[root_index], None, None)
        _left_construct(root_index, root, (0, root_index-1))
        _right_construct(root_index, root, (root_index+1, len(operators)-1))

        return root
    
    def _generate_operation_steps(self, operation:operation_node|Any):
        if isinstance(operation, operation_node):
            lhs = self._generate_operation_steps(operation.lhand)   
            rhs = self._generate_operation_steps(operation.rhand)
            return _step_evaluation(_operator_step_generators[operation.operation](self, operation, lhs, rhs))
        elif isinstance(operation, ParsingNodeFunction):
            step_eval = _step_evaluation()
            self._generate_function_steps(operation, rtv=step_eval)
            return step_eval
        elif isinstance(operation, ParsingNodeName):
            return operation
        elif isinstance(operation, ParsingNodeValue):
            value = _convert_script_value(operation.value)
            assert value is not None, f"Failed to lookup type for value: {operation} {repr(operation.value)}"
            return value
        elif isinstance(operation, ParsingNodeNVPair):
            step_eval = _step_evaluation()
            vstep = _step_evaluation()
            self._generate_expression_steps(operation.value, vstep)
            async def _step():
                v = await vstep()
                if isinstance(v, _variable_access):
                    v = await v.resolve(self.stack)
                if isinstance(v, ScriptVariable):
                    v = v.get()
                if not isinstance(v, ScriptValue):
                    raise exceptions.TRMustEvaluate(
                        "value for name-value pair must evaluate but resulted in no value",
                        ctx=exceptions.ExceptionContext(operation.value, _step)
                    )
                return ScriptValue(DATA_TYPE_TABLE[ScriptNameValuePair], ScriptNameValuePair(operation.name.name, v.inner))
            self.steps_debug[_step] = operation.value
            step_eval.cb = _step
            return step_eval
            

    def _generate_expression_steps(self, node:ParsingNodeExpression|ParsingNodeParentheses, rtv:_step_evaluation|None=None):
        operation_tree = self._get_expression_operations(node)
        def _resolve_name(n:ParsingNodeName):
            async def _step():
                ns = self.stack.find_name(n.name)
                if ns is None:
                    raise exceptions.TRMissingName(
                        f"{repr(n.name)} not found",
                        n.name,
                        ctx=exceptions.ExceptionContext(n, _step)
                    )
                return ns[n.name]
            self.steps_debug[_step] = n
            return _step
        def _resolve_value(v:ScriptValue):
            async def _step():
                return v
            self.steps_debug[_step] = v
            return _step
        def _resolve_nvpair(node:ParsingNodeNVPair):
            vstep = _step_evaluation()
            self._generate_expression_steps(node.value, vstep)
            async def _step():
                v = await vstep()
                if isinstance(v, _variable_access):
                    v = await v.resolve(self.stack)
                if isinstance(v, ScriptVariable):
                    v = v.get()
                if not isinstance(v, ScriptValue):
                    raise exceptions.TRMustEvaluate(
                        "value for name-value pair must evaluate but resulted in no value",
                        ctx=exceptions.ExceptionContext(node.value, _step)
                    )
                return ScriptValue(DATA_TYPE_TABLE[ScriptNameValuePair], ScriptNameValuePair(node.name.name, v.inner))
            self.steps_debug[_step] = node.value
            return _step

        if operation_tree is None:
            child = node.children[0]
            while isinstance(child, ParsingNodeParentheses):
                child = child.children[0]
            if isinstance(child, ParsingNodeFunction):
                self._generate_function_steps(child, rtv)
            elif isinstance(child, ParsingNodeName):
                if rtv is not None:
                    rtv.cb = _resolve_name(child)
                elif self.loud_expressions:
                    self.steps_stack.steps.append(_resolve_name(child))
            elif isinstance(child, ParsingNodeValue):
                if rtv is not None:
                    value = _convert_script_value(child.value)
                    rtv.cb = _resolve_value(value)
                elif self.loud_expressions:
                    value = _convert_script_value(child.value)
                    self.steps_stack.steps.append(_resolve_value(value))
            elif isinstance(child, ParsingNodeFString):
                self._generate_f_string_steps(child, rtv)
            elif isinstance(child, ParsingNodeNVPair):
                assert child.name is not None, f"NVPair name is missing {child}"
                assert child.value is not None, f"NVPair value is missing {child}"
                if rtv is not None:
                    rtv.cb = _resolve_nvpair(child)
                elif self.loud_expressions:
                    self.steps_stack.steps.append(_resolve_nvpair(child))
            assert not isinstance(child, ParsingNodeExpression), f"illegal recursive node: {node} -> {child}"
        else:
            os = self._generate_operation_steps(operation_tree)
            if isinstance(os, _step_evaluation) and os:
                if rtv is None:
                    self.steps_stack.steps.append(os.cb)
                else:
                    rtv.cb = os.cb
            elif isinstance(os, ParsingNodeName):
                if rtv is not None:
                    rtv.cb = _resolve_name(os)
            elif isinstance(os, ScriptValue):
                if rtv is not None:
                    rtv.cb = _resolve_value(os)
            else:
                raise exceptions.TCInvalidParameter("failed to evaluate parameter", ctx=exceptions.ExceptionContext(node))

    def _generate_f_string_steps(self, node:ParsingNodeFString, rtv:_step_evaluation|None=None):
        cnodes:dict[int] = {}
        parts:list[str|None] = []
        replace:dict[int, Callable[[], Awaitable]] = {}
        i = 0
        for child in node.children:
            if isinstance(child, ParsingNodeExpression):
                if len(child.children) == 1 and isinstance(child.children[0], ParsingNodeValue):
                    child = child.children[0]
                else:
                    step_eval = _step_evaluation()
                    self._generate_expression_steps(child, step_eval)
                    parts.append(None)
                    cnodes
                    replace[i] = step_eval
                    i += 1
                    continue
            if isinstance(child, ParsingNodeValue):
                if isinstance(child.value, str):
                    parts.append(child.value)
                    i += 1
                else:
                    v = wrap_python_value(child.value)
                    s = v.type.conv_str(v).inner
                    if parts and parts[-1] is not None:
                        parts[-1] += s
                    else:
                        parts.append(s)
                        i += 1
            else:
                raise exceptions.TCInvalidFStringEmbeddedExpression(f"f-string embedded expression must evaluate", ctx=exceptions.ExceptionContext(child))
        async def string_parts():
            for i, part in enumerate(parts):
                if part is None:
                    x = await replace[i]()
                    if isinstance(x, _variable_access):
                        xx = await x.resolve(self.stack)
                        if xx is None:
                            raise exceptions.TRMissingName(
                                f"{repr(x.path[0].value)} not found",
                                x.path[0].value,
                                ctx=exceptions.ExceptionContext(node.children[i], _step)
                            )
                        else:
                            x = xx
                    if isinstance(x, ScriptVariable):
                        x = x.get()
                    v = wrap_python_value(x)
                    yield v.type.conv_str(v).inner
                else:
                    yield part

        async def _step():
            return wrap_python_value("".join([part async for part in string_parts()]))
        
        self.steps_debug[_step] = node
        
        if rtv is None:
            self.steps_stack.steps.append(_step)
        else:
            rtv.cb = _step

    def _generate_if_statement_steps(self, node:ParsingNodeIfStatement, rtv:_step_evaluation|None=None):
        pairs:list[tuple[_step_evaluation, Callable[[], Awaitable[_step_expansion]]]] = []
        last:Callable[[], Awaitable[_step_expansion]] = None

        for pair in node.children:
            assert isinstance(pair, ParsingNodeConditionPair), f"if statement child is not condition pair: {pair}"
            assert pair.codeblock is not None, f"if statement missing code block"
            if pair.condition is None:
                if last is None:
                    last = _step_evaluation()
                    self.steps_stack = stepsnode = step_stack_node(self.steps_stack, [])
                    self._generate_codeblock_steps(pair.codeblock)
                    self.steps_stack = stepsnode.parent
                    last.cb = stepsnode.create_exp_step()
                else:
                    raise exceptions.TCIncorrectIfStatement(
                        "else if cannot come after if",
                        ctx=exceptions.ExceptionContext(pair)
                    )
            elif last is not None:
                raise exceptions.TCIncorrectIfStatement(
                    "else if cannot come after else",
                    ctx=exceptions.ExceptionContext(pair)
                )
            else:
                condition_cb, block_cb = cbpair = _step_evaluation(), _step_evaluation()
                self._generate_expression_steps(pair.condition, condition_cb)
                self.steps_stack = block_frame = step_stack_node(self.steps_stack, [])
                self._generate_codeblock_steps(pair.codeblock)
                self.steps_stack = block_frame.parent
                block_cb.cb = block_frame.create_exp_step()
                pairs.append(cbpair)
        
        async def _step():
            for i, (condition_cb, block_cb) in enumerate(pairs):
                v = await condition_cb()
                if isinstance(v, _variable_access):
                    x = await v.resolve(self.stack)
                    if x is None:
                        raise exceptions.TRMissingName(
                            f"{repr(v.path[0].value)} not found",
                            v.path[0].value,
                            ctx=exceptions.ExceptionContext(node.children[i].condition, _step)
                        )
                    else:
                        v = x
                if not isinstance(v, ScriptValue):
                    raise exceptions.TRMustEvaluate(
                        "if statement condition must evaluate but resulted in no value",
                        ctx=exceptions.ExceptionContext(node.children[i].condition, _step)
                    )
                if v.type.conv_bool(v).inner:
                    return await block_cb()
            if last:
                return await last()

        self.steps_debug[_step] = node
        
        if rtv is None:
            self.steps_stack.steps.append(_step)
        else:
            rtv.cb = _step

    def _generate_loop_statement_steps(self, node:ParsingNodeLoopStatement, rtv:_step_evaluation|None=None):
        assert node.children and isinstance(node.children[-1], ParsingNodeCodeBlock), f"loop statement must at least have a code block, got: {node.children}"
        block = node.children[-1]
        if len(node.children) > 1:
            condition_node = node.children[-2]
            if len(node.children) > 2:
                init_nodes = node.children[:-2]
            else:
                init_nodes = None
        else:
            condition_node = None

        init_steps = []
        if init_nodes:
            self.steps_stack = step_stack_node(self.steps_stack, init_steps)
            for n in init_nodes:
                assert isinstance(n, ParsingNodeLoopExpression), f"loop init node must be loop expression, got: {n}"
                assert len(n.children) == 1 and isinstance(node.children[0], (ParsingNodeExpression, ParsingNodeParentheses, ParsingNodeVarDecl)), f"loop expression node must contain one expression, got: {node.children}"
                child = n.children[0]
                if isinstance(child, ParsingNodeVarDecl):
                    self._generate_vardecl_step(child, self.scope if child.kw == "var" else self.stack.ns if child.kw == "define" else self.global_scope)
                self._generate_expression_steps(n.children[0])
            self.steps_stack = self.steps_stack.parent

        if condition_node is None:
            async def _condition_step():
                return True
        else:
            condition_step = _step_evaluation()
            self._generate_expression_steps(condition_node.children[0], condition_step)
            async def _condition_step():
                x = await condition_step()
                if isinstance(x, ScriptValue):
                    return bool(x.type.conv_bool(x).inner)
                else:
                    raise exceptions.TRMustEvaluate(
                        "loop statement condition expression (the last expression) must evaluate but resulted in no value",
                        ctx=exceptions.ExceptionContext(condition_node, _condition_step)
                    )

        self.steps_stack = step_stack_node(self.steps_stack, [])
        self._generate_codeblock_steps(block)
        block_steps = self.steps_stack.steps
        self.steps_stack = self.steps_stack.parent
        indef = _indefinite_step_expansion(_condition_step, lambda: block_steps, handle_step_control=True)
        async def _step():
            return indef
        self.steps_debug[_step] = node

        if rtv is None:
            self.steps_stack.steps.extend(init_steps)
            self.steps_stack.steps.append(_step)
        else:
            exp = _fixed_step_expansion([*init_steps, _step], new_ns_stackframe=False)
            async def _steps():
                return exp
            self.steps_debug[_step] = node
            rtv.cb = _steps

    def _generate_catch_statement_steps(self, node:ParsingNodeCatchStatement):
        if not node.children or len(node.children) > 2 or (len(node.children) == 1 and not isinstance(node.children[0], ParsingNodeCodeBlock)) or (len(node.children) == 2 and not(isinstance(node.children[0], ParsingNodeName) and isinstance(node.children[1], ParsingNodeCodeBlock))):
            raise exceptions.TCIncorrentCatchStatement(
                "catch statement needs at most one name followed by one codeblock",
                exceptions.ExceptionContext(node)
            )

        if len(node.children) == 1:
            name = None
            blocki = 0
        else:
            nnode:ParsingNodeName = node.children[0]
            name = nnode.name
            blocki = 1

        if name is None:
            async def _catch_step(_:Exception):
                pass
        else:
            async def _catch_step(e:Exception):
                self.stack.find_name(name)[name].assign(wrap_python_value(exceptions.wrap(e)))

        self.steps_stack = step_stack_node(self.steps_stack, [])
        self._generate_codeblock_steps(node.children[blocki])
        block_stepexp = _catch_step_expansion(self.steps_stack.steps, _catch_step)
        self.steps_stack = self.steps_stack.parent

        async def _step():
            if name is not None:
                if self.stack.find_name(name) is None:
                    self.stack.ns[name] = ScriptVariable(ScriptValue(DATA_TYPE_TABLE[type(None)], None))
            return block_stepexp
        
        self.steps_debug[_step] = node

        self.steps_stack.steps.append(_step)


    def _generate_vardecl_step(self, node:ParsingNodeVarDecl, target_ns:Namespace):
        assert node.name is not None
        name = node.name.name
        async def _step():
            ns = self.stack.find_name(name)
            if ns is None:
                target_ns[name] = ScriptVariable(ScriptValue(DATA_TYPE_TABLE[type(None)], None))
            elif ns is not target_ns:
                target_ns[name] = ns.pop(name)
        self.steps_debug[_step] = node
        self.steps_stack.steps.append(_step)

    def _generate_loop_control_step(self, node:ParsingNodeLoopControl):
        async def _step():
            return _step_control(node.flags, node.value)
        self.steps_debug[_step] = node
        self.steps_stack.steps.append(_step)

    def _generate_codeblock_steps(self, node:ParsingNodeCodeBlock):
        for child in node.children:
            if isinstance(child, (ParsingNodeExpression, ParsingNodeParentheses)):
                self._generate_expression_steps(child)
            elif isinstance(child, ParsingNodeFunction):
                self._generate_function_steps(child)
            elif isinstance(child, ParsingNodeCodeBlock):
                self._generate_codeblock_steps(child)
            elif isinstance(child, ParsingNodeIfStatement):
                self._generate_if_statement_steps(child)
            elif isinstance(child, ParsingNodeLoopStatement):
                self._generate_loop_statement_steps(child)
            elif isinstance(child, ParsingNodeCatchStatement):
                self._generate_catch_statement_steps(child)
            elif isinstance(child, ParsingNodeVarDecl):
                self._generate_vardecl_step(child, self.scope if child.kw == "var" else self.stack.ns if child.kw == "define" else self.global_scope)
            elif isinstance(child, ParsingNodeLoopControl):
                self._generate_loop_control_step(child)

    def compile(self, tree:ParsingNode):
        if self.steps:
            self.steps.clear()
            self.steps_stack = step_stack_node(None, self.steps)
            self.steps_debug.clear()
        self._generate_codeblock_steps(tree)


def _validate_h(h):
    return isinstance(h, (_step_evaluation, _variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

async def _resolve_h(script:Script, h, hnode:ParsingNode, step:Callable[[], Any]|None)->ScriptVariable:
    _h = h
    if isinstance(h, _step_evaluation):
        h = await h()
    if isinstance(h, _variable_access):
        x = await h.resolve(script.stack)
        if x is None:
            raise exceptions.TRMissingName(
                f"{repr(h.path[0].value)} not found",
                h.path[0].value,
                ctx=exceptions.ExceptionContext(hnode, step)
            )
        h = x 
        
    if isinstance(h, ScriptVariable):
        return h
    elif isinstance(h, ScriptValue):
        return ScriptVariable(h)
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            raise exceptions.TRMissingName(
                f"{repr(h.name)} not found",
                h.name,
                ctx=exceptions.ExceptionContext(hnode, step)
            )
        return ns[h.name]
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_vh(h):
    return isinstance(h, (_step_evaluation, _variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

async def _resolve_vh(script:Script, h, hnode:ParsingNode, step:Callable[[], Any]|None)->ScriptValue:
    _h = h
    if isinstance(h, _step_evaluation):
        h = await h()
    if isinstance(h, _variable_access):
        h = await h.resolve(script.stack)
    
    if isinstance(h, ScriptVariable):
        return h.get()
    elif isinstance(h, ScriptValue):
        return h
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            raise exceptions.TRMissingName(
                f"{repr(h.name)} not found",
                h.name,
                ctx=exceptions.ExceptionContext(hnode, step)
            )
        return ns[h.name].get()
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_ih(h):
    return isinstance(h, (_step_evaluation, _variable_access, ScriptVariable, ParsingNodeName))

async def _resolve_ih(script:Script, h, hnode:ParsingNode, step:Callable[[], Any]|None, make_name_if_missing:bool=False, get_attr:bool=False):
    _h = h
    if isinstance(h, _step_evaluation):
        h = await h()
    if isinstance(h, _variable_access):
        if get_attr and len(h.path) > 1:
            x = await h.resolve(script.stack, -1)
            if x is None:
                raise exceptions.TRMissingName(
                    f"{repr(h.path[0].value)} not found",
                    h.path[0].value,
                    ctx=exceptions.ExceptionContext(hnode, step)
                )
            elif isinstance(x, ScriptVariable):
                return x.get(), h.path[-1]
            else:
                return x, h.path[-1]
        else:
            h = await h.resolve(script.stack)
        
    if isinstance(h, ScriptVariable):
        return h
    elif isinstance(h, ScriptValue):
        return ScriptVariable(h)
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            if make_name_if_missing:
                ns = script.stack.ns
                ns[h.name] = ScriptVariable(None)
            else:
                raise exceptions.TRMissingName(
                    f"{repr(h.name)} not found",
                    h.name,
                    ctx=exceptions.ExceptionContext(hnode, step)
                )
        return ns[h.name]
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_nh(h):
    return isinstance(h, (_variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

async def _resolve_nh(h)->_variable_access:
    _h = h
    if isinstance(h, _step_evaluation):
        h = await h()
    if isinstance(h, _variable_access):
        return h
    elif isinstance(h, (ScriptValue, ScriptVariable)):
        return _variable_access([], h)
    elif isinstance(h, ParsingNodeName):
        return _variable_access([_va_path_node(h.name, _VA_NAME)])
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")


def _generate_add_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().add(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_sub_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().sub(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_mlt_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().mlt(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_div_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().div(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_mod_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().mod(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step
    

async def _inplace_operator_step(script:Script, op:operation_node, lh, rh, opname:str, _step):
    l = await _resolve_ih(script, lh, op.onode.parent.children[op.position-1], _step, get_attr=True)
    if isinstance(l, ScriptVariable):
        lvar = l
        f = l.assign
        vs = ()
        takes_ixvar = False
    else:
        lv, ln = l
        lvar = ScriptVariable(await _variable_access([ln], value_root=lv).resolve(script.stack))
        if ln.type is _VA_NAME:
            f, vs = lv.type.setattr, (lv, ln.value)
        elif ln.type is _VA_SUBSCRIPT:
            f, vs = lv.type.setitem, (lv, await ln.value())
        else:
            raise exceptions._TronixRuntimeAssertion("variable access path node has unrecognized type")
        takes_ixvar = True
    r = await _resolve_h(script, rh, op.onode.parent.children[op.position-1], _step)
    try:
        ix:ScriptValue = getattr(lvar.type(), opname)(lvar, r)
    except NotImplementedError as e:
        raise exceptions.TRNotImplemented(
            "operation is not implemented",
            ctx=exceptions.ExceptionContext(op.onode, _step)
        ) from e
    except Exception as e:
        raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
    if ix is None:
        raise exceptions.TRMustEvaluate(
            f"operation must evaluate but resulted in no value",
            ctx=exceptions.ExceptionContext(op.onode, _step)
        )
    elif ix is NotImplemented:
        raise exceptions.TRNotImplemented(
            "operation is not implemented",
            ctx=exceptions.ExceptionContext(op.onode, _step)
        )
    
    if lvar.get().inner is ix.inner:
        return ix
    else:
        if takes_ixvar:
            ix_pass = ScriptVariable(ix)
        else:
            ix_pass = ix
        try:
            x = f(*vs, ix_pass)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation (assign) is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            return ix
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation (assign) is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x

def _generate_iadd_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        return await _inplace_operator_step(script, op, lh, rh, "iadd", _step)
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_isub_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        return await _inplace_operator_step(script, op, lh, rh, "isub", _step)
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_imlt_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        return await _inplace_operator_step(script, op, lh, rh, "imlt", _step)
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_idiv_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        return await _inplace_operator_step(script, op, lh, rh, "idiv", _step)
    script.steps_debug[_step] = op.onode
    return _step
    

def _generate_imod_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        return await _inplace_operator_step(script, op, lh, rh, "imod", _step)
    script.steps_debug[_step] = op.onode
    return _step
    
def _generate_dot_steps(script:Script, op:operation_node, lh, rh):
    async def _step():
        l = await _resolve_nh(lh)
        r = await _resolve_nh(rh)
        return _variable_access([*l.path, *r.path], l.value_root)
    script.steps_debug[_step] = op.onode
    return _step

def _generate_subscript_steps(script:Script, op:operation_node, lh, rh):
    assert rh is None, f"subscript should not be passed a right-hand operand: {rh}"
    pnode = op.onode
    assert isinstance(pnode, ParsingNodeSubscript), ""
    if not pnode.children:
        raise exceptions.TCInvalidOperand(
            "subscript takes a value or evaluable expression, got nothing",
            ctx=exceptions.ExceptionContext(pnode)
        )
    elif len(pnode.children) > 1:
        raise exceptions.TCInvalidOperand(
            f"subscript does not take multiple expressions (got {len(pnode.children)})",
            ctx=exceptions.ExceptionContext(pnode)
        )
    expr = pnode.children[0]
    if not isinstance(expr, (ParsingNodeParentheses, ParsingNodeExpression)):
        raise exceptions.TCInvalidOperand(
            "subcript contents must be a value or result in one",
            ctx=exceptions.ExceptionContext(expr)
        )
    inner_step = _step_evaluation()
    script._generate_expression_steps(expr, rtv=inner_step)

    async def _resolve_inner():
        item_key = await inner_step()
        if isinstance(item_key, ScriptValue):
            item_key = ScriptVariable(item_key)
        elif not isinstance(item_key, ScriptVariable):
            raise exceptions.TRMustEvaluate(
                f"subscript contents must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(expr, _resolve_inner)
            )
        return item_key

    async def _step():
        l = await _resolve_nh(lh)
        return _variable_access([*l.path, _va_path_node(_resolve_inner, _VA_SUBSCRIPT)], l.value_root)
    script.steps_debug[_step] = op.onode
    return _step

def _generate_assign_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must be a variable or attribute", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    
    async def _step():
        l = await _resolve_ih(script, lh, op.onode.parent.children[op.position-1], _step, make_name_if_missing=True, get_attr=True)
        if isinstance(l, ScriptVariable):
            r = await _resolve_vh(script, rh, op.onode.parent.children[op.position+1], _step)
            l.assign(r)
            return r
        else:
            lv, ln = l
            r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
            if ln.type is _VA_NAME:
                f, vs = lv.type.setattr, (lv, ln.value, r)
            elif ln.type is _VA_SUBSCRIPT:
                f, vs = lv.type.setitem, (lv, await ln.value(), r)
            else:
                raise exceptions._TronixRuntimeAssertion("variable access path node has unrecognized type")
            try:
                x = f(*vs)
            except NotImplementedError as e:
                raise exceptions.TRNotImplemented(
                    "operation is not implemented",
                    ctx=exceptions.ExceptionContext(op.onode, _step)
                ) from e
            except Exception as e:
                raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
            if x is None:
                raise exceptions.TRMustEvaluate(
                    f"operation must evaluate but resulted in no value",
                    ctx=exceptions.ExceptionContext(op.onode, _step)
                )
            elif x is NotImplemented:
                raise exceptions.TRNotImplemented(
                    "operation is not implemented",
                    ctx=exceptions.ExceptionContext(op.onode, _step)
                )
            return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_uadd_steps(script:Script, op:operation_node, lh, rh):
    assert lh is None, f"unary operations should not be passed a left-hand operand: {lh}"
    if not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        h = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = h.type().uadd(h)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step
    
def _generate_usub_steps(script:Script, op:operation_node, lh, rh):
    assert lh is None, f"unary operations should not be passed a left-hand operand: {lh}"
    if not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        h = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = h.type().usub(h)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_unot_steps(script:Script, op:operation_node, lh, rh):
    assert lh is None, f"unary operations should not be passed a left-hand operand: {lh}"
    if not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        h = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = h.type().unot(h)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step


def _generate_gt_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().gt(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_lt_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().lt(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_ge_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().ge(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_le_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().le(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_eq_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().eq(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_ne_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"right-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().ne(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_and_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_h(rh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().and_(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

def _generate_or_steps(script:Script, op:operation_node, lh, rh):
    if not _validate_vh(lh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    elif not _validate_vh(rh):
        raise exceptions.TCInvalidOperand(f"left-hand operand must resolve to a value", ctx=exceptions.ExceptionContext(op.onode))
    async def _step():
        l = await _resolve_h(script, lh, op.onode.parent.children[op.position-1], _step)
        r = await _resolve_h(script, rh, op.onode.parent.children[op.position+1], _step)
        try:
            x = l.type().or_(l, r)
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            ) from e
        except Exception as e:
            raise exceptions.wrap(e, ctx=exceptions.ExceptionContext(op.onode, _step))
        if x is None:
            raise exceptions.TRMustEvaluate(
                f"operation must evaluate but resulted in no value",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented(
                "operation is not implemented",
                ctx=exceptions.ExceptionContext(op.onode, _step)
            )
        return x
    script.steps_debug[_step] = op.onode
    return _step

_operator_step_generators:dict[str, Callable[[Script, operation_node, Any, Any], _variable_access|ScriptValue]] = {
    "u[]": _generate_subscript_steps,
    ".": _generate_dot_steps,
    "-u": _generate_usub_steps,
    "+u": _generate_uadd_steps,
    "notu": _generate_unot_steps,
    "*": _generate_mlt_steps,
    "/": _generate_div_steps,
    "%": _generate_mod_steps,
    "+": _generate_add_steps,
    "-": _generate_sub_steps,
    ">": _generate_gt_steps,
    "<": _generate_lt_steps,
    ">=": _generate_ge_steps,
    "<=": _generate_le_steps,
    "==": _generate_eq_steps,
    "!=": _generate_ne_steps,
    "=": _generate_assign_steps,
    "+=": _generate_iadd_steps,
    "-=": _generate_isub_steps,
    "*=": _generate_imlt_steps,
    "/=": _generate_idiv_steps,
    "%=": _generate_imod_steps,
    "and": _generate_and_steps,
    "or": _generate_or_steps
}

