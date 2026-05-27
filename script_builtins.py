from . import exceptions, json_proxy, script, utils
from .script import *
from .utils import ScriptFunction

import asyncio
import json
import mimetypes
import string
from typing import BinaryIO
import uuid

class _TypeType(ScriptDataType[type]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    def repr(self, value):
        return ScriptValue(String, f"<type {self.name} at {hex(id(value))}>")
    
class _NullType(ScriptDataType[None]):
    def serialize(self, value, type_str=False):
        return None
    
    def deserialize(self, x):
        return None

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

    def serialize(self, value, type_str=False):
        return dict(name=value.inner.name, value=utils.serialize_value(script.wrap_python_value(value.inner.value), type_str=type_str))

    def deserialize(self, x):
        v = self.inner.__new__(self.inner)
        v.name = x["name"]
        v.value = utils.deserialize_value(x["value"]).inner
        return v

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

    def serialize(self, value, type_str=False):
        return dict(
            first=utils.serialize_value(value.inner.first, type_str=type_str),
            second=utils.serialize_value(value.inner.second, type_str=type_str)
        )
    
    def deserialize(self, x):
        v = self.inner.__new__(self.inner)
        v.first = utils.deserialize_value(x["first"]).inner
        v.second = utils.deserialize_value(x["second"]).inner
        return v


    def repr(self, value):
        return ScriptValue(String, f"{self.name}({(fv:=wrap_python_value(value.inner.first)).type.repr(fv).inner}, {(sv:=wrap_python_value(value.inner.second)).type.repr(sv).inner})")
    
class _ListType(ScriptDataType[list]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def serialize(self, value, type_str=False):
        x = [utils.serialize_value(xi, type_str=type_str) for xi in value.inner]
        return x
    
    def deserialize(self, x):
        l = self.inner.__new__(self.inner)
        l.__init__()
        return l.extend(utils.deserialize_value(xi).inner for xi in x)

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((v:=wrap_python_value(x)).type.repr(v).inner for x in value.inner)})")
    
class _MapType(ScriptDataType[dict]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def serialize(self, value, type_str=False):
        return [(utils.serialize_value(k, type_str=type_str), utils.serialize_value(v, type_str=type_str)) for k,v in value.inner.items()]
    
    def deserialize(self, x):
        d = self.inner.__new__(self.inner)
        d.__init__()
        for k,v in x:
            d[utils.deserialize_value(k).inner] = utils.deserialize_value(v).inner
        return d

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((k:=wrap_python_value(kx)).type.repr(k).inner + ": " + (v:=wrap_python_value(vx)).type.repr(v).inner for kx, vx in value.inner.items())})")

class _rodict_dummy(dict):
    pass

class _MapReadonlyType(_MapType):

    def setitem(self, obj, name, value):
        raise TypeError(f"{self.name} object is read-only")
        
    def delitem(self, obj, name):
        raise TypeError(f"{self.name} object is read-only")

class _UUIDType(ScriptDataType[uuid.UUID]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def serialize(self, value, type_str=False):
        return str(value)
    
    def deserialize(self, x):
        return uuid.UUID(x)

    def getattr(self, obj, name):
        raise AttributeError(repr(name))
    
    def setattr(self, obj, name, value):
        raise TypeError(f"{self.name} object is read-only")
        
    def delattr(self, obj, name):
        raise TypeError(f"{self.name} object is read-only")
    
class _JsonProxyRootType(ScriptDataType[json_proxy.JsonProxyRoot]):
    
    def getattr(self, obj, name):
        root = json_proxy.JsonProxyNode([], obj.inner, None)
        return wrap_python_value(root.getchild(name))
    
    def setattr(self, obj, name, value):
        v = value.get()
        root = json_proxy.JsonProxyNode([], obj.inner, None)
        root.setchild(name, v.inner)
        return v
        
    def delattr(self, obj, name):
        root = json_proxy.JsonProxyNode([], obj.inner, None)
        return wrap_python_value(root.delchild(name))
    
    def getitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            root = json_proxy.JsonProxyNode([], obj.inner, None)
            return wrap_python_value(root.getchild(key.inner))
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def setitem(self, obj, item, value):
        v = value.get()
        key = item.get()
        if key.type.issubtype(String, Integer):
            root = json_proxy.JsonProxyNode([], obj.inner, None)
            root.setchild(key.inner, v.inner)
            return v
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def delitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            root = json_proxy.JsonProxyNode([], obj.inner, None)
            return wrap_python_value(root.delchild(key.inner))
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
    def repr(self, value):
        data, _ = value.inner.get_data()
        v = wrap_python_value(data)
        return v.type.repr(v)

    
class _JsonProxyNodeType(ScriptDataType[json_proxy.JsonProxyNode]):
    def getattr(self, obj, name):
        return wrap_python_value(obj.inner.getchild(name))
    
    def setattr(self, obj, name, value):
        v = value.get()
        obj.inner.setchild(name, v.inner)
        return v
        
    def delattr(self, obj, name):
        return wrap_python_value(obj.inner.delchild(name))
    
    def getitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            return wrap_python_value(obj.inner.getchild(key.inner))
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def setitem(self, obj, item, value):
        v = value.get()
        key = item.get()
        if key.type.issubtype(String, Integer):
            obj.inner.setchild(key.inner, v.inner)
            return v
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def delitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            return wrap_python_value(obj.inner.delchild(key.inner))
        else:
            raise exceptions.TTypeError(f"{self.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
    def repr(self, value):
        v = wrap_python_value(value.inner.resolve())
        return v.type.repr(v)

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
Map_readonly = _MapReadonlyType("_map_readonly", _rodict_dummy, Map)
UUID = _UUIDType("UUID", uuid.UUID, BASE_TYPE)
JsonProxyRoot = _JsonProxyRootType("JsonRoot", json_proxy.JsonProxyRoot, BASE_TYPE)
JsonNode = _JsonProxyNodeType("JsonNode", json_proxy.JsonProxyNode, BASE_TYPE)

null = ScriptValue(NullType, None)
true = ScriptValue(Bool, True)
false = ScriptValue(Bool, False)

_builtin_types:list[ScriptDataType] = [Type, Float, Integer, String, Bool, NamePair, Pair, List, Map, UUID]

@_TypeType.f_construct.overload(("value", [AnyType, NamePair]))
def type_construct(self, value:ScriptVariable):
        return ScriptValue(self, value.type().inner)

@_FloatType.f_construct.overload(("value", Float, 0.0))
def float_construct_identity(self, value:ScriptVariable[float]):
    return ScriptValue(self, value.get().inner)

@_FloatType.f_construct.overload(("value", [Integer,Bool,String]))
def float_construct(self, value:ScriptVariable[int|bool|str]):
    return ScriptValue(self, float(value.get().inner))

@_IntegerType.f_construct.overload(("value", Integer, 0))
def integer_construct_identity(self, value:ScriptVariable[int]):
    return ScriptValue(self, value.get().inner)

@_IntegerType.f_construct.overload(("value", [Bool, String, Float]))
def integer_construct_convert(self, value:ScriptVariable[bool|str|float]):
    return ScriptValue(self, int(value.get().inner))

@_IntegerType.f_construct.overload(("value", String), ("base", Integer))
def integer_construct_convert_base(self, value:ScriptVariable[str], base:ScriptVariable[int]):
    return ScriptValue(self, int(value.get().inner, base.get().inner))

@_StringType.f_construct.overload(("value", String, ""))
def string_construct_identity(self, value:ScriptVariable[str]):
    return ScriptValue(self, value.get().inner)

@_StringType.f_construct.overload(("value", [AnyType, NamePair]))
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

@_BoolType.f_construct.overload(("value", Bool))
def bool_construct_identity(self, value:ScriptVariable[bool]):
    return ScriptValue(self, value.get().inner)

@_BoolType.f_construct.overload(("value", [AnyType, NamePair]))
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

@_NameValuePairType.f_construct.overload(("name", String), ("value", AnyType))
def nvpair_construct(self, name:ScriptVariable[str], value:ScriptVariable):
    return ScriptValue(self, ScriptNameValuePair(name.get().inner, value.get().inner))

@_PairType.f_construct.overload(("first", AnyType), ("second", AnyType))
def pair_construct(self, first:ScriptVariable, second:ScriptVariable):
    return ScriptValue(self, _pair(first.get().inner, second.get().inner))

@_ListType.f_construct.overload(dict(name="items", dtypes=[AnyType,NamePair], pack=True))
def list_construct(self, *items:ScriptVariable):
    return ScriptValue(self, [v.get().inner for v in items])

@_MapType.f_construct.overload(dict(name="items", dtypes=[Pair,NamePair], pack=True))
def map_construct(self, *items:ScriptVariable[_pair|ScriptNameValuePair]):
    d = {}
    for item in (v.get().inner for v in items):
        if isinstance(item, _pair):
            d[item.first] = item.second
        else:
            d[item.name] = item.value
    return ScriptValue(self, d)

@_UUIDType.f_construct.overload(("hex", String))
def uuid_construct(self, hex:ScriptVariable[str]):
    return ScriptValue(self, uuid.UUID(hex))

f_isinstance = ScriptFunction()
f_issubtype = ScriptFunction()
f_has = ScriptFunction()
f_hasfunc = ScriptFunction()
f_log = ScriptFunction()
f_error = ScriptFunction()
f_flush = ScriptFunction()
f_wait = ScriptFunction()
f_format_json = ScriptFunction()
f_parse_json = ScriptFunction()
f_read = ScriptFunction()
f_write = ScriptFunction()

@f_isinstance.overload(("value", [AnyType,NamePair]), ("type", Type))
def function_isinstance(value:ScriptVariable, t:ScriptVariable[type]):
    return ScriptValue(Bool, value.type().issubtype(script.DATA_TYPE_TABLE[t.get().inner]))

@f_isinstance.overload(("value", [AnyType,NamePair]), dict(name="types", dtypes=[Type], pack=True))
def function_isinstance2(value:ScriptVariable, *types:ScriptVariable[type]):
    return ScriptValue(Bool, value.type().issubtype(*(script.DATA_TYPE_TABLE[vr.get().inner] for vr in types)))

@f_isinstance.overload(("x", Type), ("type", Type))
def function_isinstance(x:ScriptVariable[type], t:ScriptVariable[type]):
    return ScriptValue(Bool, script.DATA_TYPE_TABLE[x.get().inner].issubtype(script.DATA_TYPE_TABLE[t.get().inner]))

@f_isinstance.overload(("x", Type), dict(name="types", dtypes=[Type], pack=True))
def function_isinstance2(x:ScriptVariable[type], *types:ScriptVariable[type]):
    return ScriptValue(Bool, script.DATA_TYPE_TABLE[x.get().inner].issubtype(*(script.DATA_TYPE_TABLE[vr.get().inner] for vr in types)))

@f_has.overload(("name", String), pass_ctx=True)
def function_has(ctx:ScriptContext, name:ScriptVariable[str]):
    return ScriptValue(Bool, ctx.stack.find_name(name.get().inner) is not None)

@f_has.overload(dict(name="names", dtypes=[String], pack=True), pass_ctx=True)
def function_has_plural(ctx:ScriptContext, *names:ScriptVariable[str]):
    return ScriptValue(List, [ctx.stack.find_name(name.get().inner) is not None for name in names])

@f_has.overload(("names", List), pass_ctx=True)
def function_has_plural(ctx:ScriptContext, *names:ScriptVariable[str]):
    return ScriptValue(List, [ctx.stack.find_name(name.get().inner) is not None for name in names])

@f_has.overload(("node", [JsonNode, JsonProxyRoot]), ("name", String))
def function_has(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], name:ScriptVariable[str]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(Bool, name.get().inner in data)

@f_has.overload(("node", [JsonNode, JsonProxyRoot]), dict(name="names", dtypes=[String], pack=True))
def function_has_plural(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], *names:ScriptVariable[str]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(List, [name.get().inner in data for name in names])

@f_has.overload(("node", [JsonNode, JsonProxyRoot]), ("names", List))
def function_has_plural(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], *names:ScriptVariable[str]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(List, [name.get().inner in data for name in names])

@f_hasfunc.overload(("name", String))
def function_hasfunc(name:ScriptVariable[str]):
    return ScriptValue(Bool, name in script.SCRIPT_FUNCTION_TABLE)

@f_log.overload(dict(name="x", dtypes=[AnyType], pack=True), ("sep", String, " "), ("end", String, "\n"))
def function_log(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    print(*((xv:=xi.get()).type.conv_str(xv).inner for xi in x), sep=sep.get().inner, end=end.get().inner)

@f_error.overload(dict(name="x", dtypes=[AnyType], pack=True), ("sep", String, " "), ("end", String, ""))
def function_error(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    raise exceptions.TUserException(f"{sep.get().inner.join((xv:=xi.get()).type.conv_str(xv).inner for xi in x)}{end.get().inner}")

@f_flush.overload(("flushable", JsonProxyRoot))
def function_flush_json_proxy_root(flushable:ScriptVariable[json_proxy.JsonProxyRoot]):
    root = flushable.get().inner
    root.merge_changes()
    return true

@f_wait.overload(("seconds", [Integer, Float]))
async def function_wait(seconds:ScriptVariable[int|float]):
    await asyncio.sleep(seconds.get().inner)

@f_format_json.overload(("value", AnyType), ("serialize", Bool, True))
def function_format_json(value:ScriptVariable[Any], serialize:ScriptVariable[bool]):
    v = value.get()
    x = v.inner
    if serialize.get().inner or not (x is None or isinstance(x, (str, int, float, bool, list, dict))):
        x = v.type.serialize(v)
    
    return ScriptValue(String, json.dumps(x))

@f_parse_json.overload(("json_string", String))
def function_parse_json(value:ScriptVariable[str]):
    return script.wrap_python_value(json.loads(value.get().inner))

def _read_file_plaintext(file:BinaryIO, mimetype:str):
    return script.ScriptValue(String, file.read().decode("utf-8"))
    
def _write_file_plaintext(file:BinaryIO, mimetype:str, var:ScriptVariable):
    value = var.get()
    file.write(value.type.conv_str(value).inner.encode("utf-8"))

def _read_file_json(file:BinaryIO, mimetype:str):
    return script.wrap_python_value(json.load(file))
    
def _write_file_json(file:BinaryIO, mimetype:str, var:ScriptVariable, options:dict[str]={}):
    options.setdefault("indent", 4)
    json.dump(var.get().inner, file, **options)

ReadBehavior = Callable[[BinaryIO, str], script.ScriptValue]
WriteBehavior = Callable[[BinaryIO, str, ScriptVariable], None|ScriptValue]

_default_read_behaviors:dict[str, ReadBehavior] = {}
_default_write_behaviors:dict[str, tuple[WriteBehavior, list[ScriptDataType]]] = {}

def add_read_behavior(mimetype:str, behavior:ReadBehavior):
    _default_read_behaviors[mimetype] = behavior

def add_write_behavior(mimetype:str, behavior:WriteBehavior, types:list[ScriptDataType]|None=None):
    _default_write_behaviors[mimetype] = behavior, ([AnyType] if types is None else types)

def _read_file(file:BinaryIO, ext:str, mimetype:str=None):
    if mimetype is None:
        mimetype = mimetypes.guess_type(f"x.{ext}", strict=False)
    behavior = _default_read_behaviors.get(mimetype, _read_file_plaintext)
    return behavior(file, mimetype)

def _write_file(file:BinaryIO, ext:str, value:ScriptVariable, mimetype:str=None):
    if mimetype is None:
        mimetype = mimetypes.guess_type(f"x.{ext}", strict=False)
    behavior, types = _default_write_behaviors.get(mimetype, (_write_file_plaintext, [AnyType]))
    if value.type().issubtype(*types):
        return behavior(file, mimetype, value)
    raise exceptions.TTypeError(f"expected to write {repr(ext)} file using value of type: {",".join(t.name for t in types)}; got value {value.type().repr(value)} of type {value.type().name}")

@f_read.overload(("path", String))
def read_file_path(path:ScriptVariable[str]):
    p = path.get().inner
    with open(p, "rb") as f:
        return _read_file(f, p.rsplit(".",1)[-1])

@f_write.overload(("path", String), ("value", AnyType))
def write_file_path(path:ScriptVariable[str], value:ScriptVariable):
    p = path.get().inner
    with open(p, "wb") as f:
        return _write_file(f, p.rsplit(".",1)[-1], value)

def activate():
    script.DATA_TYPE_TABLE[NullType.inner] = NullType
    script.DATA_TYPE_TABLE[Map_readonly.inner] = Map_readonly
    for dt in _builtin_types:
        utils.add_type(dt)
    utils.add_type(JsonProxyRoot, constructor=False)
    utils.add_type(JsonNode, constructor=False)

    add_read_behavior("application/json", _read_file_json)
    add_write_behavior("application/json", _write_file_json)

    script.SCRIPT_FUNCTION_TABLE["isinstance"] = f_isinstance
    script.SCRIPT_FUNCTION_TABLE["issubtype"] = f_issubtype
    script.SCRIPT_FUNCTION_TABLE["has"] = f_has
    script.SCRIPT_FUNCTION_TABLE["hasfunc"] = f_hasfunc
    script.SCRIPT_FUNCTION_TABLE["log"] = f_log
    script.SCRIPT_FUNCTION_TABLE["error"] = f_error
    script.SCRIPT_FUNCTION_TABLE["flush"] = f_flush
    script.SCRIPT_FUNCTION_TABLE["wait"] = f_wait
    script.SCRIPT_FUNCTION_TABLE["format_json"] = f_format_json
    script.SCRIPT_FUNCTION_TABLE["parse_json"] = f_parse_json
    script.SCRIPT_FUNCTION_TABLE["read"] = f_read
    script.SCRIPT_FUNCTION_TABLE["write"] = f_write