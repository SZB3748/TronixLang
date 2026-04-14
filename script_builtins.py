from . import exceptions, script
from .script import *

import string

class _TypeType(ScriptDataType[type]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    def repr(self, value):
        return ScriptValue(String, f"<type {self.name} at {hex(id(value))}>")
    
class _NullType(ScriptDataType[None]):
    def repr(self, value):
        return ScriptValue(String, "null")

class _FloatType(ScriptDataType[float]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

class _IntegerType(ScriptDataType[int]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
        
    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

class _StringType(ScriptDataType[str]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    def conv_str(self, value):
        return value

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))


class _BoolType(ScriptDataType[bool]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    def conv_bool(self, value):
        return value

    def repr(self, value):
        return ScriptValue(String, "true" if value.inner else "false")
    
class _NameValuePairType(ScriptDataType[ScriptNameValuePair]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def repr(self, value):
        n = value.inner.name
        v = value.inner.value
        vt = wrap_python_type(type(v))
        if ":" in n or any(c in string.whitespace for c in n):
            sv = f"{repr(n)}:{vt.repr(v).inner}"
        else:
            sv = f"{n}:{vt.repr(script._convert_script_value(v)).inner}"
        return ScriptValue(String, sv)

class _pair[T,U]:
    def __init__(self, first:T, second:U):
        self._pair:list[T,U] = [first,second]

    def __getitem__(self, index):
        return self._pair[index]
    
    def __setitem__(self, index, value):
        self._pair[index] = value

    @property
    def first(self):
        return self._pair[0]
    
    @first.setter
    def first(self, value:T):
        self._pair[0] = value
    
    @property
    def second(self):
        return self._pair[1]
    
    @second.setter
    def second(self, value:U):
        self._pair[1] = value

class _PairType(ScriptDataType[_pair]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({(fv:=wrap_python_value(value.inner.first)).type.repr(fv).inner}, {(sv:=wrap_python_value(value.inner.second)).type.repr(sv).inner})")
    
class _ListType(ScriptDataType[list]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((v:=wrap_python_value(x)).type.repr(v).inner for x in value.inner)})")
    
class _MapType(ScriptDataType[dict]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((k:=wrap_python_value(kx)).type.repr(k).inner + ": " + (v:=wrap_python_value(vx)).type.repr(v).inner for kx, vx in value.inner.items())})")


AnyType = BASE_TYPE
Type = _TypeType("type", type, BASE_TYPE)
Float = _FloatType("float", float, BASE_TYPE)
Integer = _IntegerType("int", int, BASE_TYPE)
String = _StringType("str", str, BASE_TYPE)
Bool = _BoolType("bool", bool, BASE_TYPE)
NullType = _NullType("nulltype", type(None), BASE_TYPE)
NamePair = _NameValuePairType("namepair", ScriptNameValuePair, BASE_TYPE)
Pair = _PairType("pair", _pair, BASE_TYPE)
List = _ListType("list", list, BASE_TYPE)
Map = _MapType("map", dict, BASE_TYPE)

null = ScriptValue(NullType, None)
true = ScriptValue(Bool, True)
false = ScriptValue(Bool, False)

_builtin_types:set[ScriptDataType] = {Type, Float, Integer, String, Bool, NamePair, Pair, List, Map}

@_TypeType.f_construct.overload(ScriptFunctionParam("value", [AnyType, NamePair]))
def type_construct(self, value:ScriptVariable):
        return ScriptValue(self, value.type().inner)

@_FloatType.f_construct.overload(ScriptFunctionParam("value", [Float], default=0.0))
def float_construct_identity(self, value:ScriptVariable[float]):
    return ScriptValue(self, value.get().inner)

@_FloatType.f_construct.overload(ScriptFunctionParam("value", [Integer,Bool,String]))
def float_construct(self, value:ScriptVariable[int|bool|str]):
    return ScriptValue(self, float(value.get().inner))

@_IntegerType.f_construct.overload(ScriptFunctionParam("value", [Integer], default=0))
def integer_construct_identity(self, value:ScriptVariable[int]):
    return ScriptValue(self, value.get().inner)

@_IntegerType.f_construct.overload(ScriptFunctionParam("value", [Bool, String, Float]))
def integer_construct_convert(self, value:ScriptVariable[bool|str|float]):
    return ScriptValue(self, int(value.get().inner))

@_IntegerType.f_construct.overload(ScriptFunctionParam("value", [String]), ScriptFunctionParam("base", [Integer]))
def integer_construct_convert_base(self, value:ScriptVariable[str], base:ScriptVariable[int]):
    return ScriptValue(self, int(value.get().inner, base.get().inner))

@_StringType.f_construct.overload(ScriptFunctionParam("value", [String], default=""))
def string_construct_identity(self, value:ScriptVariable[str]):
    return ScriptValue(self, value.get().inner)

@_StringType.f_construct.overload(ScriptFunctionParam("value", [AnyType]))
def string_construct(self, value:ScriptVariable):
    v = value.get()
    try:
        x = v.type.conv_str(v)
    except NotImplementedError as e:
        raise exceptions.TNotImplemented(f"str() for {v.type.name} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if x is None:
        raise exceptions.TMustEvaluate(f"str() for {v.type.name} must evaluate but resulted in no value")
    elif x is NotImplemented:
        raise exceptions.TNotImplemented(f"str() for {v.type.name} is not implemented")
    return x

@_BoolType.f_construct.overload(ScriptFunctionParam("value", [Bool]))
def bool_construct_identity(self, value:ScriptVariable[bool]):
    return ScriptValue(self, value.get().inner)

@_BoolType.f_construct.overload(ScriptFunctionParam("value", [AnyType]))
def bool_construct(self, value:ScriptVariable):
    v = value.get()
    try:
        x = v.type.conv_bool(v)
    except NotImplementedError as e:
        raise exceptions.TNotImplemented(f"bool() for {v.type.name} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if x is None:
        raise exceptions.TMustEvaluate(f"bool() for {v.type.name} must evaluate but resulted in no value")
    elif x is NotImplemented:
        raise exceptions.TNotImplemented(f"bool() for {v.type.name} is not implemented")
    return x

@_NameValuePairType.f_construct.overload(ScriptFunctionParam("name", [String]), ScriptFunctionParam("value", [AnyType]))
def nvpair_construct(self, name:ScriptVariable[str], value:ScriptVariable):
    return ScriptValue(self, ScriptNameValuePair(name.get().inner, value.get().inner))

@_PairType.f_construct.overload(ScriptFunctionParam("first", [AnyType]), ScriptFunctionParam("second", [AnyType]))
def pair_construct(self, first:ScriptVariable, second:ScriptVariable):
    return ScriptValue(self, _pair(first.get().inner, second.get().inner))

@_ListType.f_construct.overload(ScriptFunctionParam("items", [AnyType,NamePair], pack=True))
def list_construct(self, *items:ScriptVariable):
    return ScriptValue(self, [v.get().inner for v in items])

@_MapType.f_construct.overload(ScriptFunctionParam("items", [Pair,NamePair], pack=True))
def map_construct(self, *items:ScriptVariable[_pair|ScriptNameValuePair]):
    d = {}
    for item in (v.get().inner for v in items):
        if isinstance(item, _pair):
            d[item.first] = item.second
        else:
            d[item.name] = item.value
    return ScriptValue(self, d)

def _add_type(dt:ScriptDataType):
    script.DATA_TYPE_TABLE[dt.inner] = dt
    script.SCRIPT_FUNCTION_TABLE[dt.name] = dt.construct
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(Type, dt.inner))

f_isinstance = ScriptFunction()
f_issubtype = ScriptFunction()
f_has = ScriptFunction()
f_hasfunc = ScriptFunction()
f_log = ScriptFunction()
f_error = ScriptFunction()

@f_isinstance.overload(ScriptFunctionParam("value", [AnyType,NamePair]), ScriptFunctionParam("type", [Type]))
def function_isinstance(value:ScriptVariable, t:ScriptVariable[type]):
    return ScriptValue(Bool, value.type().issubtype(script.DATA_TYPE_TABLE[t.get().inner]))

@f_isinstance.overload(ScriptFunctionParam("value", [AnyType,NamePair]), ScriptFunctionParam("types", [Type], pack=True))
def function_isinstance2(value:ScriptVariable, *types:ScriptVariable[type]):
    return ScriptValue(Bool, value.type().issubtype(*(script.DATA_TYPE_TABLE[vr.get().inner] for vr in types)))

@f_isinstance.overload(ScriptFunctionParam("x", [Type]), ScriptFunctionParam("type", [Type]))
def function_isinstance(x:ScriptVariable[type], t:ScriptVariable[type]):
    return ScriptValue(Bool, script.DATA_TYPE_TABLE[x.get().inner].issubtype(script.DATA_TYPE_TABLE[t.get().inner]))

@f_isinstance.overload(ScriptFunctionParam("x", [Type]), ScriptFunctionParam("types", [Type], pack=True))
def function_isinstance2(x:ScriptVariable[type], *types:ScriptVariable[type]):
    return ScriptValue(Bool, script.DATA_TYPE_TABLE[x.get().inner].issubtype(*(script.DATA_TYPE_TABLE[vr.get().inner] for vr in types)))

@f_has.overload(ScriptFunctionParam("name", [String]), pass_ctx=True)
def function_has(ctx:ScriptContext, name:ScriptVariable[str]):
    return ScriptValue(Bool, ctx.stack.find_name(name.get().inner) is not None)

@f_has.overload(ScriptFunctionParam("names", [String], pack=True), pass_ctx=True)
def function_has_plural(ctx:ScriptContext, *names:ScriptVariable[str]):
    return ScriptValue(List, [ctx.stack.find_name(name.get().inner) is not None for name in names])

@f_has.overload(ScriptFunctionParam("names", [List]), pass_ctx=True)
def function_has_plural(ctx:ScriptContext, *names:ScriptVariable[str]):
    return ScriptValue(List, [ctx.stack.find_name(name.get().inner) is not None for name in names])

@f_hasfunc.overload(ScriptFunctionParam("name", [String]))
def function_hasfunc(name:ScriptVariable[str]):
    return ScriptValue(Bool, name in script.SCRIPT_FUNCTION_TABLE)

@f_log.overload(ScriptFunctionParam("x", [AnyType], pack=True), ScriptFunctionParam("sep", [String], default=" "), ScriptFunctionParam("end", [String], default="\n"))
def function_log(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    print(*((xv:=xi.get()).type.conv_str(xv).inner for xi in x), sep=sep.get().inner, end=end.get().inner)

@f_error.overload(ScriptFunctionParam("x", [AnyType], pack=True), ScriptFunctionParam("sep", [String], default=" "), ScriptFunctionParam("end", [String], default=""))
def function_error(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    raise exceptions.TUserException(f"{sep.get().inner.join((xv:=xi.get()).type.conv_str(xv).inner for xi in x)}{end.get().inner}")

def activate():
    script.DATA_TYPE_TABLE[NullType.inner] = NullType
    for dt in _builtin_types:
        _add_type(dt)
    script.SCRIPT_FUNCTION_TABLE["isinstance"] = f_isinstance
    script.SCRIPT_FUNCTION_TABLE["issubtype"] = f_issubtype
    script.SCRIPT_FUNCTION_TABLE["has"] = f_has
    script.SCRIPT_FUNCTION_TABLE["hasfunc"] = f_hasfunc
    script.SCRIPT_FUNCTION_TABLE["log"] = f_log
    script.SCRIPT_FUNCTION_TABLE["error"] = f_error