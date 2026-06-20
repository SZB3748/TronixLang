from . import exceptions, json_proxy, script, utils
from .script import *
from .utils import ScriptFunction
from .duration_types import *

import asyncio
import json
import mimetypes
import string
import sys
from typing import BinaryIO, IO
import uuid

_TypeTypeAttrs = utils.ScriptAttributeHandler[type,Any](no_subscripting=True)
@_TypeTypeAttrs.enforce_child_attrs()
@_TypeTypeAttrs.attach
class _TypeType(ScriptDataType[type]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _TypeTypeAttrs
    attrs.entry("name").readonly(lambda o, n: script.wrap_python_value(script.DATA_TYPE_TABLE[o.inner].name))
    
    def repr(self, value):
        return ScriptValue(String, f"<type {self.name} at {hex(id(value))}>")

_NullTypeAttrs = utils.ScriptAttributeHandler[None,Any](no_subscripting=True)
@_NullTypeAttrs.enforce_child_attrs()
@_NullTypeAttrs.attach
class _NullType(ScriptDataType[None]):
    def serialize(self, value, type_str=False):
        return None
    
    def deserialize(self, x):
        return None
    
    attrs = _NullTypeAttrs

    def repr(self, value):
        return ScriptValue(String, "null")

_FloatTypeAttrs = utils.ScriptAttributeHandler[float,Any](no_subscripting=True)
@_FloatTypeAttrs.enforce_child_attrs()
@_FloatTypeAttrs.attach
class _FloatType(ScriptDataType[float]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _FloatTypeAttrs
    attrs.entry("integer_ratio").readonly(lambda o, n: script.wrap_python_value(_pair(*o.inner.as_integer_ratio())))
    attrs.entry("is_integer").readonly(lambda o, n: script.wrap_python_value(o.inner.is_integer()))

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

_IntegerTypeAttrs = utils.ScriptAttributeHandler[int,Any](no_subscripting=True)
@_IntegerTypeAttrs.enforce_child_attrs()
@_IntegerTypeAttrs.attach
class _IntegerType(ScriptDataType[int]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _IntegerTypeAttrs

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

_StringTypeAttrs = utils.ScriptAttributeHandler[str, int]()
@_StringTypeAttrs.enforce_child_attrs(*utils.ATTR_ATTACH_ATTRS)
@_StringTypeAttrs.attach
class _StringType(ScriptDataType[str]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    attrs = _StringTypeAttrs
    attrs.wildcard = utils.ScriptValueAttribute("").itemreadonly(utils.SimpleGetItem())
    attrs.entry("capitalized").readonly(utils.MethodGetAttribute("capitalize"))
    attrs.entry("casefolded").readonly(utils.MethodGetAttribute("casefold"))
    attrs.entry("is_alpha_numeric").readonly(utils.MethodGetAttribute("isalnum"))
    attrs.entry("is_alphabetic").readonly(utils.MethodGetAttribute("isalpha"))
    attrs.entry("is_ascii").readonly(utils.MethodGetAttribute("isascii"))
    attrs.entry("is_decimal").readonly(utils.MethodGetAttribute("isdecimal"))
    attrs.entry("is_digit").readonly(utils.MethodGetAttribute("isdigit"))
    attrs.entry("is_lowercase").readonly(utils.MethodGetAttribute("islower"))
    attrs.entry("is_numeric").readonly(utils.MethodGetAttribute("isnumeric"))
    attrs.entry("is_space", "is_whitespace").readonly(utils.MethodGetAttribute("isspace"))
    attrs.entry("is_titlecase").readonly(utils.MethodGetAttribute("istitle"))
    attrs.entry("is_uppercase").readonly(utils.MethodGetAttribute("isupper"))
    attrs.entry("lowercased").readonly(utils.MethodGetAttribute("lower"))
    attrs.entry("caseswapped").readonly(utils.MethodGetAttribute("spawcase"))
    attrs.entry("titlecased").readonly(utils.MethodGetAttribute("title"))
    attrs.entry("uppercased").readonly(utils.MethodGetAttribute("upper"))

    def conv_str(self, value):
        return value

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

_BoolTypeAttrs = utils.ScriptAttributeHandler[bool,Any](_IntegerTypeAttrs)
@_BoolTypeAttrs.enforce_child_attrs()
@_BoolTypeAttrs.attach
class _BoolType(ScriptDataType[bool]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _BoolTypeAttrs

    def conv_bool(self, value):
        return value

    def repr(self, value):
        return ScriptValue(String, "true" if value.inner else "false")

_NameValuePairTypeAttrs = utils.ScriptAttributeHandler(no_subscripting=True)
@_NameValuePairTypeAttrs.enforce_child_attrs()
@_NameValuePairTypeAttrs.attach
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

    attrs = _NameValuePairTypeAttrs
    attrs.entry("name").getter(utils.SimpleGetAttribute()).setter(utils.TypedSetter(str, utils.SimpleSetAttribute())).nodel()
    attrs.entry("value").getter(utils.SimpleGetAttribute()).setter(utils.SimpleSetAttribute()).nodel()

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

_PairTypeAttrs = utils.ScriptAttributeHandler[_pair, int]()
@_PairTypeAttrs.enforce_child_attrs()
@_PairTypeAttrs.attach
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


    attrs = _PairTypeAttrs
    attrs.entry("first").getter(utils.SimpleGetAttribute()).setter(utils.SimpleSetAttribute())
    attrs.entry("second").getter(utils.SimpleGetAttribute()).setter(utils.SimpleSetAttribute())
    attrs.entry(0).itemgetter(utils.SimpleGetItem()).itemsetter(utils.SimpleSetItem()).itemnodel()
    attrs.entry(1).itemgetter(utils.SimpleGetItem()).itemsetter(utils.SimpleSetItem()).itemnodel()

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({(fv:=wrap_python_value(value.inner.first)).type.repr(fv).inner}, {(sv:=wrap_python_value(value.inner.second)).type.repr(sv).inner})")

def pair_alias_subtype(name:str, firstnames:list[str], secondnames:list[str], inner_type:type):
    _attrs = utils.ScriptAttributeHandler[inner_type,Any](_PairTypeAttrs)
    @_attrs.enforce_child_attrs()
    @_attrs.attach
    class _PairSubType(_PairType):
        attrs = _attrs
        attrs.alias(_PairTypeAttrs["first"], *firstnames)
        attrs.alias(_PairTypeAttrs["second"], *secondnames)
    return _PairSubType(name, inner_type, Pair)

def resolve_index_value(obj:ScriptValue, item:ScriptVariable):
    v = item.get()
    if v.type.issubtype(Integer):
        assert isinstance(v.inner, int)
        return v.inner
    elif v.type.issubtype(Pair):
        assert isinstance(v.inner, _pair)
        try:
            begin = int(v.inner.first)
            end = int(v.inner.second)
        except TypeError:
            null_name = utils.script_repr(null)
            raise exceptions.TTypeError(f"{obj.type.name} can only be subscripted by a pair if it is or is convertable to a pair of ({Integer.name}|{null_name}, {Integer.name}|{null_name}), got pair ({script.wrap_python_type(type(v.inner.first)).name}, {script.wrap_python_type(type(v.inner.second)).name})")
        return slice(begin, end)
    else:
        raise exceptions.TTypeError(f"{obj.type.name} must be subscriptied by a {Integer.name} or pair of ({Integer.name}, {Integer.name}), got {utils.script_repr(v)}")

_ListTypeAttrs = utils.ScriptAttributeHandler[list,int](wildcard=utils.ScriptValueAttribute[list, int, Any](""))
@_ListTypeAttrs.enforce_child_attrs(*utils.ATTR_ATTACH_ATTRS)
@_ListTypeAttrs.attach_some(*utils.ATTR_ATTACH_ATTRS)
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
    
    attrs = _ListTypeAttrs
    attrs.entry("length").readonly(lambda o, n: script.wrap_python_value(len(o.inner)))

    def getitem(self, obj, item):
        return script.wrap_python_value(obj.inner[resolve_index_value(obj, item)])

    def setitem(self, obj, item, value):
        x = value.get()
        obj.inner[resolve_index_value(obj, item)] = x.inner
        return x

    def delitem(self, obj, item):
        index = resolve_index_value(obj, item)
        x = script.wrap_python_value(obj.inner[index])
        del obj.inner[index]
        return x

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((v:=wrap_python_value(x)).type.repr(v).inner for x in value.inner)})")
    
_MapTypeAttrs = utils.ScriptAttributeHandler[dict,Any](wildcard=utils.ScriptValueAttribute(""))
@_MapTypeAttrs.enforce_child_attrs()
@_MapTypeAttrs.attach
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

    attrs = _MapTypeAttrs
    attrs.entry("length").readonly(lambda o, n: script.wrap_python_value(len(o.inner)))

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((k:=wrap_python_value(kx)).type.repr(k).inner + ": " + (v:=wrap_python_value(vx)).type.repr(v).inner for kx, vx in value.inner.items())})")

class _rolist_dummy(list):
    pass

class _rodict_dummy(dict):
    pass


_ListReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rolist_dummy,int](_ListTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_ListReadonlyTypeAttrs.enforce_child_attrs()
@_ListReadonlyTypeAttrs.attach
class _ListReadonlyType(_ListType):
    
    attrs = _ListReadonlyTypeAttrs
    attrs.wildcard.noset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).nodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)

_MapReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rodict_dummy,Any](_MapTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_MapReadonlyTypeAttrs.enforce_child_attrs()
@_MapReadonlyTypeAttrs.attach
class _MapReadonlyType(_MapType):

    attrs = _MapReadonlyTypeAttrs
    attrs.wildcard.noset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).nodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)

_UUIDTypeAttrs = utils.ScriptAttributeHandler[uuid.UUID,Any](no_subscripting=True)
@_UUIDTypeAttrs.enforce_child_attrs()
@_UUIDTypeAttrs.attach
class _UUIDType(ScriptDataType[uuid.UUID]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    def serialize(self, value, type_str=False):
        return str(value)
    
    def deserialize(self, x):
        return uuid.UUID(x)
    
class _JsonProxyRootType(ScriptDataType[json_proxy.JsonProxyRoot]):
    
    def getattr(self, obj, name):
        result = obj.inner.getchild(name)
        sm = obj.inner.schema.match_path([name])
        if sm is None:
            return wrap_python_value(result)
        else:
            instance = sm.__new__(sm)
            instance.__setstate__(result)
            return wrap_python_value(instance)
    
    def setattr(self, obj, name, value):
        v = value.get()
        sm = obj.inner.schema.match_path([name])
        if sm is None:
            obj.inner.setchild(name, v.inner)
        elif isinstance(v.inner, sm):
            obj.inner.setchild(name, v.inner.__getstate__())
        else:
            smt = script.wrap_python_type(sm)
            raise exceptions.TTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
        return v
        
    def delattr(self, obj, name):
        result = obj.inner.delchild(name)
        sm = obj.inner.schema.match_path([name])
        if sm is None:
            return wrap_python_value(result)
        else:
            instance = sm.__new__(sm)
            instance.__setstate__(result)
            return wrap_python_value(instance)
    
    def getitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            result = obj.inner.getchild(key.inner)
            sm = obj.inner.schema.match_path([key.inner])
            if sm is None:
                return wrap_python_value(result)
            else:
                instance = sm.__new__(sm)
                instance.__setstate__(result)
                return wrap_python_value(instance)
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def setitem(self, obj, item, value):
        v = value.get()
        key = item.get()
        if key.type.issubtype(String, Integer):
            sm = obj.inner.schema.match_path([key.inner])
            if sm is None:
                obj.inner.setchild(key.inner, v.inner)
            elif isinstance(v.inner, sm):
                obj.inner.setchild(key.inner, v.inner.__getstate__())
            else:
                smt = script.wrap_python_type(sm)
                raise exceptions.TTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
            return v
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def delitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            result = obj.inner.delchild(key.inner)
            sm = obj.inner.schema.match_path([key.inner])
            if sm is None:
                return wrap_python_value(result)
            else:
                instance = sm.__new__(sm)
                instance.__setstate__(result)
                return wrap_python_value(instance)
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
    def repr(self, value):
        data, _ = value.inner.get_data()
        v = wrap_python_value(data)
        return v.type.repr(v)

_JsonProxyNodeTypeAttrs = utils.ScriptAttributeHandler(wildcard=utils.ScriptValueAttribute[json_proxy.JsonProxyNode, str|int, Any](""))
@_JsonProxyNodeTypeAttrs.enforce_child_attrs()
class _JsonProxyNodeType(ScriptDataType[json_proxy.JsonProxyNode]):
    attrs = _JsonProxyNodeTypeAttrs

    def getattr(self, obj, name):
        result = obj.inner.getchild(name)
        sm = obj.inner.root.schema.match_path([name])
        if sm is None:
            return wrap_python_value(result)
        else:
            instance = sm.__new__(sm)
            instance.__setstate__(result)
            return wrap_python_value(instance)
    
    def setattr(self, obj, name, value):
        v = value.get()
        sm = obj.inner.root.schema.match_path([name])
        if sm is None:
            obj.inner.setchild(name, v.inner)
        elif isinstance(v.inner, sm):
            obj.inner.setchild(name, v.inner.__getstate__())
        else:
            smt = script.wrap_python_type(sm)
            raise exceptions.TTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
        return v
        
    def delattr(self, obj, name):
        result = obj.inner.delchild(name)
        sm = obj.inner.root.schema.match_path([name])
        if sm is None:
            return wrap_python_value(result)
        else:
            instance = sm.__new__(sm)
            instance.__setstate__(result)
            return wrap_python_value(instance)
    
    def getitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            result = obj.inner.getchild(key.inner)
            sm = obj.inner.root.schema.match_path([key.inner])
            if sm is None:
                return wrap_python_value(result)
            else:
                instance = sm.__new__(sm)
                instance.__setstate__(result)
                return wrap_python_value(instance)
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def setitem(self, obj, item, value):
        v = value.get()
        key = item.get()
        if key.type.issubtype(String, Integer):
            sm = obj.inner.root.schema.match_path([key.inner])
            if sm is None:
                obj.inner.setchild(key.inner, v.inner)
            elif isinstance(v.inner, sm):
                obj.inner.setchild(key.inner, v.inner.__getstate__())
            else:
                smt = script.wrap_python_type(sm)
                raise exceptions.TTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
            return v
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
    def delitem(self, obj, item):
        key = item.get()
        if key.type.issubtype(String, Integer):
            result = obj.inner.delchild(key.inner)
            sm = obj.inner.root.schema.match_path([key.inner])
            if sm is None:
                return wrap_python_value(result)
            else:
                instance = sm.__new__(sm)
                instance.__setstate__(result)
                return wrap_python_value(instance)
        else:
            raise exceptions.TTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
    def repr(self, value):
        v = wrap_python_value(value.inner.resolve())
        return v.type.repr(v)

class _file_wrapper:
    def __init__(self, file:IO[bytes]):
        self.file = file

_FileTypeAttrs = utils.ScriptAttributeHandler(no_subscripting=True)
@_FileTypeAttrs.enforce_child_attrs()
@_FileTypeAttrs.attach
class _FileType(script.ScriptDataType[_file_wrapper]):

    construct = f_construct = utils.ScriptFunction()

    attrs = _FileTypeAttrs
    attrs.entry("name").readonly(utils.SimpleGetAttribute())
    attrs.entry("mode").readonly(utils.SimpleGetAttribute())
    attrs.entry("fileno").readonly(utils.MethodGetAttribute())

class _DurationBaseType[T:_duration](script.ScriptDataType[T]):

    construct = f_construct = utils.ScriptFunction()

    def repr(self, value):
        return script.ScriptValue(String, repr(value.inner))

    def serialize(self, value, type_str=False):
        return value.inner.x
    
    def deserialize(self, x):
        return self.inner(x)
    

class _NanoSecondsType(_DurationBaseType[_nanoseconds_duration]):
    pass
class _MicroSecondsType(_DurationBaseType[_microseconds_duration]):
    pass
class _MilliSecondsType(_DurationBaseType[_milliseconds_duration]):
    pass
class _SecondsType(_DurationBaseType[_seconds_duration]):
    pass
class _MinutesType(_DurationBaseType[_minutes_duration]):
    pass
class _HoursType(_DurationBaseType[_hours_duration]):
    pass
class _DaysType(_DurationBaseType[_days_duration]):
    pass
class _WeeksType(_DurationBaseType[_weeks_duration]):
    pass


def _complex_duration_setter(d_name:str):
    def setter(o:ScriptValue[_complex_duration], n:str, v:ScriptVariable[int|float|_duration|_complex_duration]):
        d:_duration = getattr(o, d_name)
        x = v.get().inner
        if isinstance(x, (int, float)):
            d.x = x
        elif isinstance(x, _duration):
            d.x = x.x
        else:
            d.x = x._as_duration(type(d)).x
        o.inner.simplify()
        return script.wrap_python_value(d._copy())
    return utils.TypedSetter([int, float, _duration, _complex_duration], setter)


_ComplexDurationTypeAttrs = utils.ScriptAttributeHandler[_complex_duration, Any]()
_ComplexDurationTypeAttrs.enforce_child_attrs()
_ComplexDurationTypeAttrs.attach
class _ComplexDurationType(script.ScriptDataType[_complex_duration]):

    def repr(self, value):
        return script.ScriptValue(String, repr(value.inner))

    def serialize(self, value, type_str=False):
        return [d.x for d in value.inner.iter_durations()]
    
    def deserialize(self, x):
        return self.inner(*x)

    attrs = _ComplexDurationTypeAttrs
    attrs.entry("weeks").getter(lambda o, n: script.wrap_python_value(o.inner.weeks._copy())).setter(_complex_duration_setter("weeks")).nodel()
    attrs.entry("days").getter(lambda o, n: script.wrap_python_value(o.inner.days._copy())).setter(_complex_duration_setter("days")).nodel()
    attrs.entry("hours").getter(lambda o, n: script.wrap_python_value(o.inner.hours._copy())).setter(_complex_duration_setter("hours")).nodel()
    attrs.entry("minutes").getter(lambda o, n: script.wrap_python_value(o.inner.mins._copy())).setter(_complex_duration_setter("mins")).nodel()
    attrs.entry("seconds").getter(lambda o, n: script.wrap_python_value(o.inner.secs._copy())).setter(_complex_duration_setter("secs")).nodel()
    attrs.entry("milliseconds").getter(lambda o, n: script.wrap_python_value(o.inner.ms._copy())).setter(_complex_duration_setter("ms")).nodel()
    attrs.entry("microseconds").getter(lambda o, n: script.wrap_python_value(o.inner.us._copy())).setter(_complex_duration_setter("us")).nodel()
    attrs.entry("nanoseconds").getter(lambda o, n: script.wrap_python_value(o.inner.ns._copy())).setter(_complex_duration_setter("ns")).nodel()

    attrs.entry("as_weeks").readonly(utils.MethodGetAttribute())
    attrs.entry("as_days").readonly(utils.MethodGetAttribute())
    attrs.entry("as_hours").readonly(utils.MethodGetAttribute())
    attrs.entry("as_minutes").readonly(utils.MethodGetAttribute())
    attrs.entry("as_seconds").readonly(utils.MethodGetAttribute())
    attrs.entry("as_milliseconds").readonly(utils.MethodGetAttribute())
    attrs.entry("as_microseconds").readonly(utils.MethodGetAttribute())
    attrs.entry("as_nanoseconds").readonly(utils.MethodGetAttribute())


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
List_readonly = _ListReadonlyType("_list_readonly", _rolist_dummy, List)
Map_readonly = _MapReadonlyType("_map_readonly", _rodict_dummy, Map)
UUID = _UUIDType("UUID", uuid.UUID, BASE_TYPE)
JsonProxyRoot = _JsonProxyRootType("JsonRoot", json_proxy.JsonProxyRoot, BASE_TYPE)
JsonNode = _JsonProxyNodeType("JsonNode", json_proxy.JsonProxyNode, BASE_TYPE)
File = _FileType("File", _file_wrapper, BASE_TYPE)
Duration = _DurationBaseType("Duration", _duration, BASE_TYPE)
Nanoseconds = _NanoSecondsType("nanoseconds", _nanoseconds_duration, Duration)
Microseconds = _MicroSecondsType("microseconds", _microseconds_duration, Duration)
Milliseconds = _MilliSecondsType("milliseconds", _milliseconds_duration, Duration)
Seconds = _SecondsType("seconds", _seconds_duration, Duration)
Minutes = _MinutesType("minutes", _minutes_duration, Duration)
Hours = _HoursType("hours", _hours_duration, Duration)
Weeks = _WeeksType("weeks", _weeks_duration, Duration)
Days = _DaysType("days", _days_duration, Duration)
ComplexDuration = _ComplexDurationType("ComplexDuration", _complex_duration, BASE_TYPE)

_StringTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_ListTypeAttrs.wildcard.itemgetter(List.getitem).itemsetter(List.setitem).itemdeleter(List.delitem)
_MapTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_JsonProxyNodeTypeAttrs.wildcard.reverse_attach(JsonNode)

null = ScriptValue(NullType, None)
true = ScriptValue(Bool, True)
false = ScriptValue(Bool, False)

_builtin_types:list[ScriptDataType] = [Type, Float, Integer, String, Bool, NamePair, Pair, List, Map, UUID, File, Nanoseconds, Microseconds, Milliseconds, Seconds, Minutes, Hours, Weeks, Days]

@_TypeType.f_construct.overload(("value", [AnyType, NamePair]))
def type_construct(self, value:ScriptVariable):
        return script.ScriptValue(self, value.type().inner)

@_FloatType.f_construct.overload(("value", Float, 0.0))
def float_construct_identity(self, value:ScriptVariable[float]):
    return script.ScriptValue(self, value.get().inner)

@_FloatType.f_construct.overload(("value", [Integer,Bool,String]))
def float_construct(self, value:ScriptVariable[int|bool|str]):
    return script.ScriptValue(self, float(value.get().inner))

@_FloatType.f_construct.overload(("value", Duration))
def float_construct_duration(self, value:ScriptVariable[_duration]):
    return script.ScriptValue(self, float(value.get().inner.x))

@_FloatType.f_construct.overload(("value", ComplexDuration))
def float_construct_cduration(self, value:ScriptVariable[_complex_duration]):
    return script.ScriptValue(self, float(value.get().inner.as_seconds().x))

@_IntegerType.f_construct.overload(("value", Integer, 0))
def integer_construct_identity(self, value:ScriptVariable[int]):
    return script.ScriptValue(self, value.get().inner)

@_IntegerType.f_construct.overload(("value", [Bool, String, Float]))
def integer_construct_convert(self, value:ScriptVariable[bool|str|float]):
    return script.ScriptValue(self, int(value.get().inner))

@_IntegerType.f_construct.overload(("value", Duration))
def integer_construct_duration(self, value:ScriptVariable[_duration]):
    return script.ScriptValue(self, int(value.get().inner.x))

@_IntegerType.f_construct.overload(("value", ComplexDuration))
def integer_construct_cduration(self, value:ScriptVariable[_complex_duration]):
    return script.ScriptValue(self, int(value.get().inner.as_seconds().x))

@_IntegerType.f_construct.overload(("value", String), ("base", Integer))
def integer_construct_convert_base(self, value:ScriptVariable[str], base:ScriptVariable[int]):
    return script.ScriptValue(self, int(value.get().inner, base.get().inner))

@_StringType.f_construct.overload(("value", String, ""))
def string_construct_identity(self, value:ScriptVariable[str]):
    return script.ScriptValue(self, value.get().inner)

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
    return script.ScriptValue(self, value.get().inner)

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
    return script.ScriptValue(self, ScriptNameValuePair(name.get().inner, value.get().inner))

@_PairType.f_construct.overload(("first", AnyType), ("second", AnyType))
def pair_construct(self, first:ScriptVariable, second:ScriptVariable):
    return script.ScriptValue(self, _pair(first.get().inner, second.get().inner))

@_ListType.f_construct.overload(dict(name="items", dtypes=[AnyType,NamePair], pack=True))
def list_construct(self, *items:ScriptVariable):
    return script.ScriptValue(self, [v.get().inner for v in items])

@_MapType.f_construct.overload(dict(name="items", dtypes=[Pair,NamePair], pack=True))
def map_construct(self, *items:ScriptVariable[_pair|ScriptNameValuePair]):
    d = {}
    for item in (v.get().inner for v in items):
        if isinstance(item, _pair):
            d[item.first] = item.second
        else:
            d[item.name] = item.value
    return script.ScriptValue(self, d)

@_UUIDType.f_construct.overload(("hex", String))
def uuid_construct(self, hex:ScriptVariable[str]):
    return script.ScriptValue(self, uuid.UUID(hex))

def resolve_file_mode(mode:ScriptVariable[str]):
    m = mode.get().inner.lower()
    if m not in ("read", "write", "append"):
        raise exceptions.TBadValue(f"file mode must be read, write, or append; got {mode.get().inner}")
    return m[0]

@_FileType.f_construct.overload(("path", String), ("mode", String, "read"))
def File_construct(self, path:ScriptVariable[str], mode:ScriptVariable[str]):
    return script.ScriptValue(self, _file_wrapper(open(path.get().inner, resolve_file_mode(mode)+"b")))

@_DurationBaseType.f_construct.overload(("value", [Integer, Float, String, Bool], 0.0))
def DurationBase_construct_number(self:ScriptDataType[_duration], value:ScriptVariable[int|float|str|bool]):
    return script.ScriptValue(self, self.inner(float(value.get().inner)))

@_DurationBaseType.f_construct.overload(("value", [Duration]))
def DurationBase_construct_duration(self:ScriptDataType[_duration], value:ScriptVariable[_duration]):
    d = value.get().inner
    x = d.x * _unitspace_convert(self.inner.FACTOR, self.inner.POWER, d.FACTOR, d.POWER)
    return script.ScriptValue(self, self.inner(x))

@_DurationBaseType.f_construct.overload(("value", [ComplexDuration]))
def DurationBase_construct_complex(self:ScriptDataType[_duration], value:ScriptVariable[_complex_duration]):
    return script.ScriptValue(self, value.get().inner._as_duration(self.inner))

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
f_close = ScriptFunction()
f_append = ScriptFunction()
f_find = ScriptFunction()
f_contains = ScriptFunction()

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

_read_behaviors:dict[str, ReadBehavior] = {}
_write_behaviors:dict[str, tuple[WriteBehavior, list[ScriptDataType]]] = {}

def add_read_behavior(mimetype:str, behavior:ReadBehavior):
    _read_behaviors[mimetype] = behavior

def add_write_behavior(mimetype:str, behavior:WriteBehavior, types:list[ScriptDataType]|None=None):
    _write_behaviors[mimetype] = behavior, ([AnyType] if types is None else types)

def remove_read_behavior(mimetype:str, behavior:ReadBehavior|None=None):
    if behavior is None:
        return _read_behaviors.pop(mimetype, None)
    elif _read_behaviors.get(mimetype, None) is behavior:
        del _read_behaviors[mimetype]
        return behavior

def remove_write_behavior(mimetype:str, behavior:WriteBehavior|None=None):
    if behavior is None:
        return _write_behaviors.pop(mimetype, None)
    elif _write_behaviors.get(mimetype, (None,))[0] is behavior:
        del _write_behaviors[mimetype]
        return behavior

def all_mimetypes_of(prefix:str)->set[str]:
    mimes = set()
    for mime in mimetypes.types_map.values():
        if mime.startswith(prefix):
            mimes.add(mime)
    for mime in mimetypes.common_types.values():
        if mime.startswith(prefix):
            mimes.add(mime)
    return mimes

def _read_file(file:BinaryIO, ext:str, mimetype:str=None):
    if mimetype is None:
        mimetype = mimetypes.guess_type(f"x.{ext}", strict=False)[0]
    behavior = _read_behaviors.get(mimetype, _read_file_plaintext)
    return behavior(file, mimetype)

def _write_file(file:BinaryIO, ext:str, value:ScriptVariable, mimetype:str=None):
    if mimetype is None:
        mimetype = mimetypes.guess_type(f"x.{ext}", strict=False)[0]
    behavior, types = _write_behaviors.get(mimetype, (_write_file_plaintext, [AnyType]))
    if value.type().issubtype(*types):
        return behavior(file, mimetype, value)
    raise exceptions.TTypeError(f"expected to write {repr(ext)} file using value of type: {",".join(t.name for t in types)}; got value {value.type().repr(value)} of type {value.type().name}")

@f_read.overload(("path", String))
def read_file_path(path:ScriptVariable[str]):
    p = path.get().inner
    with open(p, "rb") as f:
        return _read_file(f, p.rsplit(".",1)[-1])

@f_read.overload(("file", File))
def read_file(file:ScriptVariable[_file_wrapper]):
    f = file.get().inner.file
    return _read_file(f, f.name.rsplit(".",1)[-1])

@f_write.overload(("path", String), ("value", AnyType))
def write_file_path(path:ScriptVariable[str], value:ScriptVariable):
    p = path.get().inner
    with open(p, "wb") as f:
        return _write_file(f, p.rsplit(".",1)[-1], value)

@f_write.overload(("file", File), ("value", AnyType))
def write_file(file:ScriptVariable[_file_wrapper], value:ScriptVariable):
    f = file.get().inner.file
    return _write_file(f, f.name.rsplit(".",1)[-2], value)
    
@f_close.overload(("file", File))
def close_file(file:ScriptVariable[_file_wrapper]):
    file.get().inner.file.close()


@f_append.overload(("target", List), ("value", [AnyType, NamePair]))
def list_append_value(target:ScriptVariable[list], value:ScriptVariable):
    v = target.get()
    v.inner.append(value.get().inner)
    return v

_STR_FIND_STOP_DEFAULT = sys.maxsize
@f_find.overload(("target", String), ("value", String), ("start", Integer, 0), ("stop", Integer, _STR_FIND_STOP_DEFAULT))
def str_find_value(target:ScriptVariable[str], value:ScriptVariable[str], start:ScriptVariable[int], stop:ScriptVariable[int]):
    istart = start.get().inner
    istop = stop.get().inner
    if istart == 0:
        istart = None
    if istop == sys.maxsize:
        istop = None
    return script.ScriptValue(Integer, target.get().inner.find(value.get().inner, start=istart, end=istop))

_LIST_FIND_STOP_DEFAULT = sys.maxsize
@f_find.overload(("target", List), ("value", [AnyType, NamePair]), ("start", Integer, 0), ("stop", Integer, _LIST_FIND_STOP_DEFAULT))
def list_find_value(target:ScriptVariable[list], value:ScriptVariable, start:ScriptVariable[int], stop:ScriptVariable[int]):
    t = target.get().inner
    v = value.get().inner
    istart = start.get().inner
    istop = stop.get().inner
    try:
        index = t.index(v, start=istart, stop=istop)
    except ValueError:
        index = -1
    return script.ScriptValue(Integer, index)

@f_find.overload(("target", Map), ("value", [AnyType, NamePair]))
def map_find_value(target:ScriptVariable[dict], value:ScriptVariable):
    v = value.get()
    for key, val in target.get().inner.items():
        mv = script.wrap_python_value(val)
        try:
            x = v.type.eq(v, mv)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("'==' operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"'==' operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("'==' operation is not implemented")
        
        if x.inner:
            return script.wrap_python_value(key)
    
    #TODO error value not found

@f_contains.overload(("target", String), ("value", String))
def str_contains(target:ScriptVariable[str], value:ScriptVariable[str]):
    if value.get().inner in target.get().inner:
        return true
    else:
        return false
    
@f_contains.overload(("target", List), ("value", [AnyType, NamePair]))
def list_contains(target:ScriptVariable[list], value:ScriptVariable):
    if value.get().inner in target.get().inner:
        return true
    else:
        return false

@f_contains.overload(("target", Map), ("value", [AnyType, NamePair]))
def map_contains(target:ScriptVariable[dict], value:ScriptVariable):
    if value.get().inner in target.get().inner:
        return true
    else:
        return false


def activate():
    if not mimetypes.inited:
        mimetypes.init()
    script.DATA_TYPE_TABLE[NullType.inner] = NullType.init()
    script.DATA_TYPE_TABLE[List_readonly.inner] = List_readonly.init()
    script.DATA_TYPE_TABLE[Map_readonly.inner] = Map_readonly.init()
    utils.add_type(Duration, constructor=False)
    utils.add_type(ComplexDuration, constructor=False)
    for dt in _builtin_types:
        utils.add_type(dt)
    utils.add_type(JsonProxyRoot, constructor=False)
    utils.add_type(JsonNode, constructor=False)

    add_read_behavior("application/json", _read_file_json)
    add_write_behavior("application/json", _write_file_json)

    utils.merge_function("isinstance", f_isinstance)
    utils.merge_function("issubtype", f_issubtype)
    utils.merge_function("has", f_has)
    utils.merge_function("hasfunc", f_hasfunc)
    utils.merge_function("log", f_log)
    utils.merge_function("error", f_error)
    utils.merge_function("flush", f_flush)
    utils.merge_function("wait", f_wait)
    utils.merge_function("format_json", f_format_json)
    utils.merge_function("parse_json", f_parse_json)
    utils.merge_function("read", f_read)
    utils.merge_function("write", f_write)
    utils.merge_function("append", f_append)
    utils.merge_function("find", f_find)
    utils.merge_function("contains", f_contains)

def deactivate():
    utils.remove_type(NullType)
    utils.remove_type(List_readonly)
    utils.remove_type(Map_readonly)
    utils.remove_type(Duration)
    utils.remove_type(ComplexDuration)
    for dt in _builtin_types:
        utils.remove_type(dt)
    utils.remove_type(JsonProxyRoot)
    utils.remove_type(JsonNode)

    remove_read_behavior("application/json", _read_file_json)
    remove_write_behavior("application/json", _write_file_json)

    utils.remove_function("isinstance", f_isinstance)
    utils.remove_function("issubtype", f_issubtype)
    utils.remove_function("has", f_has)
    utils.remove_function("hasfunc", f_hasfunc)
    utils.remove_function("log", f_log)
    utils.remove_function("error", f_error)
    utils.remove_function("flush", f_flush)
    utils.remove_function("wait", f_wait)
    utils.remove_function("format_json", f_format_json)
    utils.remove_function("parse_json", f_parse_json)
    utils.remove_function("read", f_read)
    utils.remove_function("write", f_write)
    utils.remove_function("append", f_append)
    utils.remove_function("find", f_find)
    utils.remove_function("contains", f_contains)