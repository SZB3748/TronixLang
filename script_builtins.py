from . import exceptions, duration_types as durtypes, json_proxy, number_units as numunits, script, utils
from .script import *
from .utils import ScriptFunction

import asyncio
import json
import math
import mimetypes
import string
import sys
from typing import BinaryIO, IO, ItemsView, Iterable, Sequence
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
    attrs.entry("name").getter(utils.SimpleGetAttribute("name")).setter(utils.TypedSetter(str, utils.SimpleSetAttribute("name"))).nodel()
    attrs.entry("value").getter(utils.SimpleGetAttribute("value")).setter(utils.SimpleSetAttribute("value")).nodel()

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
    attrs.entry("first").getter(utils.SimpleGetAttribute("first")).setter(utils.SimpleSetAttribute("first"))
    attrs.entry("second").getter(utils.SimpleGetAttribute("second")).setter(utils.SimpleSetAttribute("second"))
    attrs.entry(0).itemgetter(utils.SimpleGetItem(0)).itemsetter(utils.SimpleSetItem(0)).itemnodel()
    attrs.entry(1).itemgetter(utils.SimpleGetItem(1)).itemsetter(utils.SimpleSetItem(1)).itemnodel()

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
        return int(v.inner)
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
    attrs.entry("keys").readonly(lambda o, n: script.wrap_python_value(_collection_iterator(-1, o.inner.keys())))
    attrs.entry("values").readonly(lambda o, n: script.wrap_python_value(_collection_iterator(-1, o.inner.values())))
    attrs.entry("items").readonly(lambda o, n: script.wrap_python_value(_collection_iterator(-1, o.inner.items(), lambda itold, it, v: _map_item_pair(*v))))

    def repr(self, value):
        return ScriptValue(String, f"{self.name}({", ".join((k:=wrap_python_value(kx)).type.repr(k).inner + ": " + (v:=wrap_python_value(vx)).type.repr(v).inner for kx, vx in value.inner.items())})")

class _rolist_wrapper[T](list[T]):
    def __init__(self, l:list[T]):
        self.__l = l

    def append(self, object:T):
        return self.__l.append(object)
    
    def extend(self, iterable:Iterable[T]):
        return self.__l.extend(iterable)
    
    def insert(self, index:int, object:T):
        return self.__l.insert(index, object)
    
    def remove(self, value:T):
        return self.__l.remove(value)
    
    def pop(self, index:int=-1):
        return self.__l.pop(index)
    
    def clear(self):
        return self.__l.clear()
    
    def index(self, value:T, start:int=0, stop:int=sys.maxsize):
        return self.__l.index(value, start, stop)
    
    def count(self, value:T):
        return self.__l.count(value)
    
    def sort(self, *, key=None, reverse=False):
        return self.__l.sort(key=key, reverse=reverse)
    
    def reverse(self):
        return self.__l.reverse()
    
    def copy(self):
        return self.__l.copy()
    
    def __len__(self):
        return self.__l.__len__()
    
    def __getitem__(self, s:int):
        return self.__l.__getitem__(s)
    
    def __setitem__(self, key:int, value:T):
        return self.__l.__setitem__(key, value)
    
    def __delitem__(self, key:int):
        return self.__l.__delitem__(key)
    
    def __contains__(self, key:T):
        return self.__l.__contains__(key)
    
    def __iter__(self):
        return self.__l.__iter__()
    
    def __reversed__(self):
        return self.__l.__reversed__()
    
    def __add__(self, value):
        return self.__l.__add__(value)
    
    def __mul__(self, value):
        return self.__l.__mul__(value)
    
    def __rmul__(self, value):
        return self.__l.__rmul__(value)
    
    def __iadd__(self, value):
        return self.__l.__iadd__(value)
    
    def __imul__(self, value):
        return self.__l.__imul__(value)
    
    def __repr__(self):
        return self.__l.__repr__()
    
    def __str__(self):
        return self.__l.__str__()
    
    def __eq__(self, value):
        return self.__l.__eq__(value)
    
    def __ne__(self, value):
        return self.__l.__ne__(value)

    def __lt__(self, value):
        return self.__l.__lt__(value)
    
    def __gt__(self, value):
        return self.__l.__gt__(value)
    
    def __le__(self, value):
        return self.__l.__le__(value)
    
    def __ge__(self, value):
        return self.__l.__ge__(value)

_RODICT_DEFAULT_MISSING = object()

class _rodict_wrapper[K,V](dict[K,V]):
    def __init__(self, d:dict[K,V]):
        self.__d = d

    def clear(self):
        return self.__d.clear()
    
    def copy(self):
        return self.__d.copy()
    
    def get(self, key:K, default:V|None=None):
        return self.__d.get(key, default)
    
    def items(self):
        return self.__d.items()
    
    def keys(self):
        return self.__d.keys()
    
    def pop(self, key:K, default:V=_RODICT_DEFAULT_MISSING):
        if default is _RODICT_DEFAULT_MISSING:
            return self.__d.pop(key)
        else:
            return self.__d.pop(key, default)
    
    def popitem(self):
        return self.__d.popitem()
    
    def setdefault(self, key:K, default:V=None):
        return self.__d.setdefault(key, default)

    def update(self, *args, **kwargs):
        return self.__d.update(*args, **kwargs)
    
    def values(self):
        return self.__d.values()
    
    def __getitem__(self, key:K):
        return self.__d.__getitem__(key)
    
    def __setitem__(self, key:K, value:V):
        return self.__d.__setitem__(key, value)
    
    def __delitem__(self, key:K):
        return self.__d.__delitem__(key)
    
    def __missing__(self, key:K):
        return self.__d.__missing__(key)
    
    def __contains__(self, key:K):
        return self.__d.__contains__(key)
    
    def __len__(self):
        return self.__d.__len__()
    
    def __iter__(self):
        return self.__d.__iter__()
    
    def __reversed__(self):
        return self.__d.__reversed__()
    
    def __repr__(self):
        return self.__d.__repr__()
    
    def __str__(self):
        return self.__d.__str__()
    
    def __eq__(self, value):
        return self.__d.__eq__(value)
    
    def __ne__(self, value):
        return self.__d.__ne__(value)
    
    def __ior__(self, value):
        return self.__d.__ior__(value)
    
    def __or__(self, value):
        return self.__d.__or__(value)
    
    def __ror__(self, value):
        return self.__d.__ror__(value)

_ROLIST_EMPTY = _rolist_wrapper([])
_RODICT_EMPTY = _rodict_wrapper({})

class ListOf(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "list_of"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, "|,")
        return cls(*(script.parse_script_type_annotation(part) for part in parts))
    
    def __init__(self, *types:script.ScriptDataType|script.ScriptTypeAnnotation|type|str):
        if not types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        self.types = list(types)
        self._resolved = False

    def _resolve_types(self):
        if not self._resolved:
            for i, t in enumerate(self.types):
                if isinstance(t, str):
                    self.types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.types[i] = script.wrap_python_type(t)
            self._resolved = True
        return self.types

    def __eq__(self, other):
        if isinstance(other, ListOf):
            return len(self._resolve_types()) == len(other._resolve_types()) and all(t in other.types for t in self.types)
        return other == List
    
    def compare(self, other):
        if isinstance(other, ScriptValue):
            if not other.type.issubtype(List):
                return False
            assert isinstance(other.inner, list)
            l = other.inner
        elif not isinstance(other, list):
            return False
        else:
            l = other
        dts_l = []
        ann:list[ScriptTypeAnnotation] = []
        for t in self._resolve_types():
            if isinstance(t, script.ScriptDataType):
                dts_l.append(t.inner)
            else:
                ann.append(t)
        dts:tuple[type,...] = tuple(dts_l)
        for item in l:
            if not (dts and isinstance(item, dts) or any(a.compare(item) for a in ann)):
                return False
        return True
    
    def format_data(self):
        return " | ".join(t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self._resolve_types())
    

class MapOf(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "map_of"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, ",")
        if len(parts) > 2:
            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} takes arguments for key and (optionally) value (got {len(parts)})")
        return cls(*(script.split_type_annotation_contents(part, "|") for part in parts))
    
    def __init__(self, key_types:ScriptDataType|ScriptTypeAnnotation|str|type|list[ScriptDataType|ScriptTypeAnnotation|str|type],
                 value_types:ScriptDataType|ScriptTypeAnnotation|str|type|list[ScriptDataType|ScriptTypeAnnotation|str|type]|None=None):
        self.key_types = [key_types] if isinstance(key_types, (script.ScriptDataType, script.ScriptTypeAnnotation, type, str)) else list(key_types)
        self.value_types = [script.BASE_TYPE] if value_types is None else [value_types] if isinstance(value_types, (script.ScriptDataType, script.ScriptTypeAnnotation, type, str)) else list(value_types)
        self._resolved_keys = False
        self._resolved_values = False
        if not self.key_types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        if not self.value_types:
            self.value_types.append(script.BASE_TYPE)

    def _resolve_keys(self):
        if not self._resolved_keys:
            for i, t in enumerate(self.key_types):
                if isinstance(t, str):
                    self.key_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.key_types[i] = script.wrap_python_type(t)
            self._resolved_keys = True
        return self.key_types

    def _resolve_values(self):
        if not self._resolved_values:
            for i, t in enumerate(self.value_types):
                if isinstance(t, str):
                    self.value_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.value_types[i] = script.wrap_python_type(t)
            self._resolved_values = True
        return self.value_types

    def __eq__(self, other):
        if isinstance(other, MapOf):
            return (len(self._resolved_keys()) == len(other._resolved_keys()) and all(t in other.key_types for t in self.key_types) and
                    len(self._resolve_values()) == len(other._resolve_values()) and all(t in other.value_types for t in self.value_types))
        return other == Map
    
    def compare(self, other):
        if isinstance(other, ScriptValue):
            if not other.type.issubtype(Map):
                return False
            assert isinstance(other.inner, dict)
            d = other.inner
        elif not isinstance(other, dict):
            return False
        else:
            d = other
        kdts_l = []
        kann:list[ScriptTypeAnnotation] = []
        vdts_l = []
        vann:list[ScriptTypeAnnotation] = []
        for t in self._resolve_keys():
            if isinstance(t, script.ScriptDataType):
                kdts_l.append(t.inner)
            else:
                kann.append(t)
        for t in self._resolve_values():
            if isinstance(t, script.ScriptDataType):
                vdts_l.append(t.inner)
            else:
                vann.append(t)
        kdts:tuple[type,...] = tuple(kdts_l)
        vdts:tuple[type,...] = tuple(vdts_l)

        for key, value in d.items():
            if not ((kdts and isinstance(key, kdts) or any(a.compare(key) for a in kann)) and (vdts and isinstance(value, vdts) or any(a.compare(value) for a in vann))):
                return False
        return True
    
    def format_data(self):
        keystr = "|".join(t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self._resolve_keys())
        valstr = "|".join(t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self._resolve_values())
        return f"{keystr}, {valstr}"

class PairOf(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "pair_of"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, ",")
        if len(parts) > 2:
            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} takes either one or two arguments (got {len(parts)})")
        return cls(*(script.split_type_annotation_contents(part, "|") for part in parts))

    def __init__(self, first_types:ScriptDataType|ScriptTypeAnnotation|str|type|list[ScriptDataType|ScriptTypeAnnotation|str|type],
                 second_types:ScriptDataType|ScriptTypeAnnotation|str|type|list[ScriptDataType|ScriptTypeAnnotation|str|type]|None=None):
        self.first_types = [first_types] if isinstance(first_types, (script.ScriptDataType, script.ScriptTypeAnnotation, type, str)) else list(first_types)
        self.second_types = first_types.copy() if second_types is None else [second_types] if isinstance(second_types, (script.ScriptDataType, script.ScriptTypeAnnotation, type, str)) else list(second_types)
        self._resolved_first = False
        self._resolved_second = False
        if not self.first_types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        if not self.second_types:
            self.second_types = self.first_types.copy()

    def _resolve_first(self):
        if not self._resolved_first:
            for i, t in enumerate(self.first_types):
                if isinstance(t, str):
                    self.first_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.first_types[i] = script.wrap_python_type(t)
            self._resolved_first = True
        return self.first_types
    
    def _resolve_second(self):
        if not self._resolved_second:
            for i, t in enumerate(self.second_types):
                if isinstance(t, str):
                    self.second_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.second_types[i] = script.wrap_python_type(t)
            self._resolved_second = True
        return self.second_types

    def __eq__(self, other):
        if isinstance(other, PairOf):
            return (len(self._resolve_first()) == len(other._resolve_first()) and all(t in other.first_types for t in self.first_types) and
                    len(self._resolve_second()) == len(other._resolve_second()) and all(t in other.second_types for t in self.second_types))
        return other == Pair

    def compare(self, other):
        if isinstance(other, ScriptValue):
            if not other.type.issubtype(Pair):
                return False
            assert isinstance(other.inner, _pair)
            p = other.inner
        elif not isinstance(other, _pair):
            return False
        else:
            p = other

        fdts_l = []
        fann:list[ScriptTypeAnnotation] = []
        sdts_l = []
        sann:list[ScriptTypeAnnotation] = []
        for t in self._resolve_first():
            if isinstance(t, script.ScriptDataType):
                fdts_l.append(t.inner)
            else:
                fann.append(t)
        for t in self._resolve_second():
            if isinstance(t, script.ScriptDataType):
                sdts_l.append(t.inner)
            else:
                sann.append(t)
        fdts:tuple[type,...] = tuple(fdts_l)
        sdts:tuple[type,...] = tuple(sdts_l)

        return (fdts and isinstance(p.first, fdts) or any(a.compare(p.first) for a in fann)) and (sdts and isinstance(p.second, sdts) or any(a.compare(p.second) for a in sann))

    def format_data(self):
        firststr = "|".join(t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self._resolve_first())
        secondstr = "|".join(t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self._resolve_second())
        return f"{firststr}, {secondstr}"
    

_ListReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rolist_wrapper,int](_ListTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_ListReadonlyTypeAttrs.enforce_child_attrs()
@_ListReadonlyTypeAttrs.attach
class _ListReadonlyType(_ListType):
    
    attrs = _ListReadonlyTypeAttrs
    attrs.wildcard.noset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).nodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)

_MapReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rodict_wrapper,Any](_MapTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_MapReadonlyTypeAttrs.enforce_child_attrs()
@_MapReadonlyTypeAttrs.attach
class _MapReadonlyType(_MapType):

    attrs = _MapReadonlyTypeAttrs
    attrs.wildcard.noset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).nodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)


class _iterator[T](int):

    @classmethod
    def from_bytes(cls, bytes, byteorder="big", *, signed=False):
        return cls(super().from_bytes(bytes, byteorder, signed=signed))

    def __new__(cls, value:int=0, *args, **kwargs):
        if value is NotImplemented:
            raise NotImplementedError
        return super().__new__(cls, value)

    def _copy(self, value:int):
        cls = type(self)
        new = cls.__new__(cls, value)
        new.__dict__.update(self.__dict__)
        return new

    async def next(self)->Self|None:
        return NotImplemented

    async def get(self)->T:
        return NotImplemented

    def __index__(self):
        return int(self)

    def __float__(self):
        return float(self)

    def __str__(self):
        return "%d" % int(self)

    def __repr__(self):
        return f"<{type(self).__name__} {int(self)} at {hex(id(self)).upper()}>"

    def __bool__(self):
        return bool(self)

    def __hash__(self):
        return hash(int(self))

    def __trunc__(self):
        return self._copy(super(_iterator, self).__trunc__())

    def __round__(self, ndigits = ...):
        return self._copy(super(_iterator, self).__round__(ndigits))

    def __abs__(self):
        return self._copy(super(_iterator, self).__abs__())

    def __neg__(self):
        return self._copy(super(_iterator, self).__neg__())

    def __pos__(self):
        return self._copy(super(_iterator, self).__pos__())

    def __add__(self, value):
        return self._copy(super(_iterator, self).__add__(value))

    def __sub__(self, value):
        return self._copy(super(_iterator, self).__sub__(value))

    def __mul__(self, value):
        return self._copy(super(_iterator, self).__mul__(value))

    def __truediv__(self, value):
        return self._copy(super(_iterator, self).__truediv__(value))

    def __floordiv__(self, value):
        return self._copy(super(_iterator, self).__floordiv__(value))

    def __pow__(self, value):
        return self._copy(super(_iterator, self).__pow__(value))

    def __mod__(self, value):
        return self._copy(super(_iterator, self).__mod__(value))

    def __radd__(self, value):
        return self._copy(super(_iterator, self).__radd__(value))

    def __rsub__(self, value):
        return self._copy(super(_iterator, self).__rsub__(value))

    def __rmul__(self, value):
        return self._copy(super(_iterator, self).__rmul__(value))

    def __rtruediv__(self, value):
        return self._copy(super(_iterator, self).__rtruediv__(value))

    def __rfloordiv__(self, value):
        return self._copy(super(_iterator, self).__rfloordiv__(value))

    def __eq__(self, value):
        if isinstance(value, _iterator):
            return int(self) == int(value)
        return int(self) == value
    
    def __ne__(self, value):
        if isinstance(value, _iterator):
            return int(self) != int(value)
        return int(self) != value
    
    def __gt__(self, value):
        if isinstance(value, _iterator):
            return int(self) > int(value)
        return int(self) > value

    def __ge__(self, value):
        if isinstance(value, _iterator):
            return int(self) >= int(value)
        return int(self) >= value
    
    def __lt__(self, value):
        if isinstance(value, _iterator):
            return int(self) < int(value)
        return int(self) < value

    def __le__(self, value):
        if isinstance(value, _iterator):
            return int(self) <= int(value)
        return int(self) <= value

    def __invert__(self):
        return self._copy(super(_iterator, self).__invert__())

    def __and__(self, value):
        return self._copy(super(_iterator, self).__and__(value))

    def __or__(self, value):
        return self._copy(super(_iterator, self).__or__(value))

    def __xor__(self, value):
        return self._copy(super(_iterator, self).__xor__(value))

    def __rand__(self, value):
        return self._copy(super(_iterator, self).__rand__(value))

    def __ror__(self, value):
        return self._copy(super(_iterator, self).__ror__(value))

    def __rxor__(self, value):
        return self._copy(super(_iterator, self).__rxor__(value))

    def __lshift__(self, value):
        return self._copy(super(_iterator, self).__lshift__(value))

    def __rshift__(self, value):
        return self._copy(super(_iterator, self).__rshift__(value))

    def __rlshift__(self, value):
        return self._copy(super(_iterator, self).__rlshift__(value))

    def __rrshift__(self, value):
        return self._copy(super(_iterator, self).__rrshift__(value))

class _range_iterator[T](_iterator[T]):
    def __init__(self, value:int, start:int, stop:int, step:int):
        self.start = start
        self.stop = stop
        self.step = step

    def in_range(self, v:int):
        if self.step >= 0:
            return v >= self.start and v < self.stop
        else:
            return v <= self.start and v > self.stop

    async def next(self):
        n = self + self.step
        if n.in_range(n):
            return n
        else:
            return None

    async def get(self):
        return int(self)

class _iterable_iterator[T](_iterator[T]):
    def __init__(self, value:int, iterable:Iterable[T], callback:Callable[[Self, Self, Any], Any]|None=None):
        self._iterator = iter(iterable)
        self._last = int(value)
        self._last_value:Any = None
        self.callback = callback

    async def next(self):
        n = self + 1
        if n._last > self:
            raise TypeError("cannot reverse iterate with this iterator")
        try:
            while n._last < n:
                v = next(n._iterator)
                if callable(self.callback):
                    n._last_value = self.callback(self, n, v)
                else:
                    n._last_value = v
                n._last += 1
        except StopIteration:
            return None
        return n

    async def get(self):
        return self._last_value

class _collection_iterator[T](_iterable_iterator[T]):
    def __init__(self, value, iterable:Iterable, callback:Callable[[Self, Any], T]|None=None):
        super().__init__(value, iterable)
        self._collection = iterable
        self.callback = callback

    def __contains__(self, item):
        return item in self._collection
        
class _sequence_iterator[T](_range_iterator[T]):
    def __init__(self, value:int, start:int, stop:int, step:int, sequence:Sequence[T]):
        super().__init__(value, start, stop, step)
        self.sequence = sequence

    def in_range(self, v:int):
        if self.step >= 0:
            return v >= self.start and v < min(self.stop, len(self.sequence))
        else:
            return v <= self.start and v > min(self.stop, len(self.sequence))

    async def get(self):
        if self >= 0 and self < len(self.sequence):
            return self.sequence[self]

class _map_item_pair[K,V](_pair[K,V]):
    pass


_IteratorTypeAttrs = utils.ScriptAttributeHandler[_iterator, Any]()
@_IteratorTypeAttrs.enforce_child_attrs()
@_IteratorTypeAttrs.attach
class _IteratorType[T:_iterator](ScriptDataType[T]):

    attrs = _IteratorTypeAttrs

def make_iterator_type[X:_iterator](name:str, it_t:type[X], parent:type[_IteratorType])->type[_IteratorType[X]]:
    _attrs = utils.ScriptAttributeHandler[it_t, Any](parent.attrs)
    @_attrs.enforce_child_attrs()
    @_attrs.attach
    class _subt[T](parent[it_t[T]]):
        attrs = _attrs
    _subt.__name__ = name
    return _subt

_RangeIteratorType = make_iterator_type("_RangeIteratorType", _range_iterator, _IteratorType)
_RangeIteratorTypeAttrs = _RangeIteratorType.attrs
_RangeIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] from {value.inner.start} until {value.inner.stop} (step {value.inner.step})>")
_IterableIteratorType = make_iterator_type("_IterableIteratorType", _iterable_iterator, _IteratorType)
_IterableIteratorTypeAttrs = _IterableIteratorType.attrs
_IterableIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] : {utils.script_repr(script.wrap_python_value(value.inner._last_value))} of {utils.script_repr(script.wrap_python_value(value.inner._iterator))}>")
_CollectionIteratorType = make_iterator_type("_CollectionIterator", _collection_iterator, _IterableIteratorType)
_CollectionIteratorTypeAttrs = _CollectionIteratorType.attrs
_CollectionIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] : {utils.script_repr(script.wrap_python_value(value.inner._last_value))} of {script.wrap_python_type(type(value.inner._collection)).name}>")
_SequenceIteratorType = make_iterator_type("_SequenceIteratorType", _sequence_iterator, _RangeIteratorType)
_SequenceIteratorTypeAttrs = _SequenceIteratorType.attrs
_SequenceIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] from {value.inner.start} until {min(value.inner.stop, len(value.inner.sequence))} (step {value.inner.step}) of {script.wrap_python_type(type(value.inner.sequence)).name}>")

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

_FileTypeAttrs = utils.ScriptAttributeHandler[_file_wrapper, Any](no_subscripting=True)
@_FileTypeAttrs.enforce_child_attrs()
@_FileTypeAttrs.attach
class _FileType(script.ScriptDataType[_file_wrapper]):

    construct = f_construct = utils.ScriptFunction()

    attrs = _FileTypeAttrs
    attrs.entry("name").readonly(lambda o,n: null if not isinstance((name := o.inner.file.name), str) else script.wrap_python_value(name))
    attrs.entry("mode").readonly(lambda o,n: script.wrap_python_value(o.inner.file.mode))
    attrs.entry("fileno").readonly(lambda o,n: script.wrap_python_value(o.inner.file.fileno()))

class _DurationBaseType[T:durtypes._duration](script.ScriptDataType[T]):

    construct = f_construct = utils.ScriptFunction()

    def repr(self, value):
        return script.ScriptValue(String, repr(value.inner))

    def serialize(self, value, type_str=False):
        return value.inner.x
    
    def deserialize(self, x):
        return self.inner(x)
    

class _NanoSecondsType(_DurationBaseType[durtypes._nanoseconds_duration]):
    pass
class _MicroSecondsType(_DurationBaseType[durtypes._microseconds_duration]):
    pass
class _MilliSecondsType(_DurationBaseType[durtypes._milliseconds_duration]):
    pass
class _SecondsType(_DurationBaseType[durtypes._seconds_duration]):
    pass
class _MinutesType(_DurationBaseType[durtypes._minutes_duration]):
    pass
class _HoursType(_DurationBaseType[durtypes._hours_duration]):
    pass
class _DaysType(_DurationBaseType[durtypes._days_duration]):
    pass
class _WeeksType(_DurationBaseType[durtypes._weeks_duration]):
    pass


def _complex_duration_setter(d_name:str):
    def setter(o:ScriptValue[durtypes._complex_duration], n:str, v:ScriptVariable[int|float|durtypes._duration|durtypes._complex_duration]):
        d:durtypes._duration = getattr(o, d_name)
        x = v.get().inner
        if isinstance(x, (int, float)):
            d.x = x
        elif isinstance(x, durtypes._duration):
            d.x = x.x
        else:
            d.x = x._as_duration(type(d)).x
        o.inner.simplify()
        return script.wrap_python_value(d._copy())
    return utils.TypedSetter([int, float, durtypes._duration, durtypes._complex_duration], setter)


_ComplexDurationTypeAttrs = utils.ScriptAttributeHandler[durtypes._complex_duration, Any]()
_ComplexDurationTypeAttrs.enforce_child_attrs()
_ComplexDurationTypeAttrs.attach
class _ComplexDurationType(script.ScriptDataType[durtypes._complex_duration]):

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


class _PercentType(script.ScriptDataType[numunits.percent]):
    f_construct = construct = utils.ScriptFunction()

    def repr(self, value):
        return script._convert_script_value(repr(value.inner))

class _DegreesType(script.ScriptDataType[numunits.degrees]):
    f_construct = construct = utils.ScriptFunction()

    def repr(self, value):
        return script._convert_script_value(repr(value.inner))

class _RadiansType(script.ScriptDataType[numunits.radians]):
    f_construct = construct = utils.ScriptFunction()

    def repr(self, value):
        return script._convert_script_value(repr(value.inner))

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
MapItem = pair_alias_subtype("map_item", ["key"], ["value"], _map_item_pair)
List_readonly = _ListReadonlyType("_list_readonly", _rolist_wrapper, List)
Map_readonly = _MapReadonlyType("_map_readonly", _rodict_wrapper, Map)
Iterator = _IteratorType("iterator", _iterator, Integer)
RangeIterator = _RangeIteratorType("range_iterator", _range_iterator, Iterator)
IterableIterator = _IterableIteratorType("iterable_iterator", _iterable_iterator, Iterator)
CollectionIterator = _CollectionIteratorType("collection_iterator", _collection_iterator, IterableIterator)
SequenceIterator = _SequenceIteratorType("sequence_iterator", _sequence_iterator, RangeIterator)
UUID = _UUIDType("UUID", uuid.UUID, BASE_TYPE)
JsonProxyRoot = _JsonProxyRootType("JsonRoot", json_proxy.JsonProxyRoot, BASE_TYPE)
JsonNode = _JsonProxyNodeType("JsonNode", json_proxy.JsonProxyNode, BASE_TYPE)
File = _FileType("File", _file_wrapper, BASE_TYPE)
Duration = _DurationBaseType("Duration", durtypes._duration, BASE_TYPE)
Nanoseconds = _NanoSecondsType("nanoseconds", durtypes._nanoseconds_duration, Duration)
Microseconds = _MicroSecondsType("microseconds", durtypes._microseconds_duration, Duration)
Milliseconds = _MilliSecondsType("milliseconds", durtypes._milliseconds_duration, Duration)
Seconds = _SecondsType("seconds", durtypes._seconds_duration, Duration)
Minutes = _MinutesType("minutes", durtypes._minutes_duration, Duration)
Hours = _HoursType("hours", durtypes._hours_duration, Duration)
Weeks = _WeeksType("weeks", durtypes._weeks_duration, Duration)
Days = _DaysType("days", durtypes._days_duration, Duration)
ComplexDuration = _ComplexDurationType("ComplexDuration", durtypes._complex_duration, BASE_TYPE)
Percent = _PercentType("percent", numunits.percent, BASE_TYPE)
Degrees = _DegreesType("degrees", numunits.degrees, BASE_TYPE)
Radians = _RadiansType("radians", numunits.radians, BASE_TYPE)

_StringTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_ListTypeAttrs.wildcard.itemgetter(List.getitem).itemsetter(List.setitem).itemdeleter(List.delitem)
_MapTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_JsonProxyNodeTypeAttrs.wildcard.reverse_attach(JsonNode)

null = script.ScriptValue(NullType, None)
true = script.ScriptValue(Bool, True)
false = script.ScriptValue(Bool, False)
PI = script.ScriptValue(Float, math.pi)

_builtin_types:list[ScriptDataType] = [
    Type, Float, Integer, String, Bool, NamePair, Pair, List, Map, UUID, File,
    Nanoseconds, Microseconds, Milliseconds, Seconds, Minutes, Hours, Weeks, Days,
    Percent, Degrees, Radians
]

@_TypeType.f_construct.overload(("value", [AnyType, NamePair]))
def type_construct(self, value:ScriptVariable):
    return script.ScriptValue(self, value.type().inner)

@_FloatType.f_construct.overload(("value", Float, 0.0))
def float_construct_identity(self, value:ScriptVariable[float]):
    return script.ScriptValue(self, value.get().inner)

@_FloatType.f_construct.overload(("value", [Integer,Bool,String,Percent,Degrees,Radians,Duration,ComplexDuration,Iterator]))
def float_construct(self, value:ScriptVariable[int|bool|str|numunits.percent|numunits.degrees|numunits.radians|durtypes._duration|durtypes._complex_duration]):
    return script.ScriptValue(self, float(value.get().inner))

@_IntegerType.f_construct.overload(("value", Iterator, 0))
def integer_construct_iterator(self, value:ScriptVariable[_iterator]):
    return script.ScriptValue(self, int(value.get().inner))

@_IntegerType.f_construct.overload(("value", Integer, 0))
def integer_construct_identity(self, value:ScriptVariable[int]):
    return script.ScriptValue(self, value.get().inner)

@_IntegerType.f_construct.overload(("value", [Bool,String,Float,Percent,Degrees,Radians,Duration,ComplexDuration]))
def integer_construct_convert(self, value:ScriptVariable[bool|str|float|numunits.percent|numunits.degrees|numunits.radians|durtypes._duration|durtypes._complex_duration]):
    return script.ScriptValue(self, int(value.get().inner))

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
def DurationBase_construct_number(self:ScriptDataType[durtypes._duration], value:ScriptVariable[int|float|str|bool]):
    return script.ScriptValue(self, self.inner(float(value.get().inner)))

@_DurationBaseType.f_construct.overload(("value", [Duration]))
def DurationBase_construct_duration(self:ScriptDataType[durtypes._duration], value:ScriptVariable[durtypes._duration]):
    d = value.get().inner
    x = d.x * durtypes._unitspace_convert(self.inner.FACTOR, self.inner.POWER, d.FACTOR, d.POWER)
    return script.ScriptValue(self, self.inner(x))

@_DurationBaseType.f_construct.overload(("value", [ComplexDuration]))
def DurationBase_construct_complex(self:ScriptDataType[durtypes._duration], value:ScriptVariable[durtypes._complex_duration]):
    return script.ScriptValue(self, value.get().inner._as_duration(self.inner))

@_PercentType.f_construct.overload(("value", [Integer, Float, String]))
def percent_construct(self:ScriptDataType[numunits.percent], value:ScriptVariable[float|int]):
    return script.ScriptValue(self, numunits.percent(float(value.get().inner) / 100))

@_PercentType.f_construct.overload(("value", Percent))
def percent_construct_identity(self:ScriptDataType[numunits.percent], value:ScriptVariable[numunits.percent]):
    return script.ScriptValue(self, numunits.percent(value.get().inner.value))

@_PercentType.f_construct.overload(("value", Bool))
def percent_construct_bool(self:ScriptDataType[numunits.percent], value:ScriptVariable[bool]):
    return script.ScriptValue(self, numunits.percent(1.0 if value.get().inner else 0.0))

@_PercentType.f_construct.overload(("value", Degrees))
def percent_construct_degrees(self:ScriptDataType[numunits.percent], value:ScriptVariable[numunits.degrees]):
    return script.ScriptValue(self, numunits.percent(value.get().inner.value / 360))

@_PercentType.f_construct.overload(("value", Radians))
def percent_construct_degrees(self:ScriptDataType[numunits.percent], value:ScriptVariable[numunits.radians]):
    return script.ScriptValue(self, numunits.percent(value.get().inner.value / math.tau)) #tau == 2pi

@_DegreesType.f_construct.overload(("value", [Integer, Float, String, Bool]))
def degrees_construct(self:ScriptDataType[numunits.degrees], value:ScriptVariable[int|float|str]):
    return script.ScriptValue(Degrees, numunits.degrees(float(value.get().inner)))

@_DegreesType.f_construct.overload(("value", Degrees))
def degrees_construct_identity(self:ScriptDataType[numunits.degrees], value:ScriptVariable[numunits.degrees]):
    return script.ScriptValue(Degrees, numunits.degrees(value.get().inner.value))

@_DegreesType.f_construct.overload(("value", Radians))
def degrees_construct_radians(self:ScriptDataType[numunits.degrees], value:ScriptVariable[numunits.radians]):
    return script.ScriptValue(Degrees, numunits.degrees(math.degrees(value.get().inner.value)))

@_DegreesType.f_construct.overload(("value", Percent))
def radians_construct_percent(self:ScriptDataType[numunits.degrees], value:ScriptVariable[numunits.percent]):
    return script.ScriptValue(Degrees, numunits.degrees(value.get().inner.value * 360))

@_RadiansType.f_construct.overload(("value", [Integer, Float, String, Bool]))
def radians_construct(self:ScriptDataType[numunits.radians], value:ScriptVariable[int|float|str]):
    return script.ScriptValue(Radians, numunits.radians(float(value.get().inner)))

@_RadiansType.f_construct.overload(("value", Radians))
def radians_construct_identity(self:ScriptDataType[numunits.radians], value:ScriptVariable[numunits.radians]):
    return script.ScriptValue(Radians, numunits.radians(value.get().inner.value))

@_RadiansType.f_construct.overload(("value", Degrees))
def radians_construct_degrees(self:ScriptDataType[numunits.radians], value:ScriptVariable[numunits.degrees]):
    return script.ScriptValue(Radians, numunits.radians(math.radians(value.get().inner.value)))

@_RadiansType.f_construct.overload(("value", Percent))
def radians_construct_percent(self:ScriptDataType[numunits.radians], value:ScriptVariable[numunits.percent]):
    return script.ScriptValue(Radians, numunits.radians(value.get().inner.value * math.tau))


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
f_iterate_over = ScriptFunction()
f_iterate_over_range = ScriptFunction()
f_get = ScriptFunction()
f_next = ScriptFunction()
f_reset = ScriptFunction()
f_delete = ScriptFunction()
f_delete_attribute = ScriptFunction()

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
def function_has_plural_pack(ctx:ScriptContext, *names:ScriptVariable[str]):
    return ScriptValue(List, [ctx.stack.find_name(name.get().inner) is not None for name in names])

@f_has.overload(("names", ListOf(String)), pass_ctx=True)
def function_has_plural(ctx:ScriptContext, names:ScriptVariable[list]):
    return ScriptValue(List, [ctx.stack.find_name(name) is not None for name in names.get().inner])

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
def function_has_plural(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], names:ScriptVariable[list]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(List, [name in data for name in names])

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

@f_wait.overload(("duration", Duration))
async def function_wait_duration(duration:ScriptVariable[durtypes._duration]):
    d = duration.get().inner
    seconds = d.x * durtypes._unitspace_convert(durtypes._seconds_duration.FACTOR, durtypes._seconds_duration.POWER, d.FACTOR, d.POWER)
    await asyncio.sleep(seconds)

@f_wait.overload(("duration", ComplexDuration))
async def function_wait_complex_duration(duration:ScriptVariable[durtypes._complex_duration]):
    cd = duration.get().inner
    await asyncio.sleep(cd.as_seconds().x)

@f_format_json.overload(("value", AnyType), ("serialize", Bool, True))
def function_format_json(value:ScriptVariable[Any], serialize:ScriptVariable[bool]):
    v = value.get()
    x = v.inner
    if serialize.get().inner or not (x is None or isinstance(x, (str, int, float, bool, list, dict))):
        x = v.type.serialize(v)
    
    return ScriptValue(String, json.dumps(x, ensure_ascii=False))

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
    options.setdefault("ensure_ascii", False)
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
    if v.type.issubtype(List_readonly):
        raise exceptions.TTypeError("given list is read-only")
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
    
    raise LookupError(utils.script_repr(v))

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

@f_contains.overload(("target", SequenceIterator), ("value", [AnyType, NamePair]))
def sequence_iter_contains(target:ScriptVariable[_sequence_iterator], value:ScriptVariable):
    if value.get().inner in target.get().inner.sequence:
        return true
    else:
        return false

@f_contains.overload(("target", RangeIterator), ("value", [AnyType, NamePair]))
def range_iter_contains(target:ScriptVariable[_range_iterator], value:ScriptVariable):
    if target.get().inner.in_range(value.get().inner):
        return true
    else:
        return false

@f_contains.overload(("target", CollectionIterator), ("value", [AnyType, NamePair]))
def collection_iter_contains(target:ScriptVariable[_collection_iterator], value:ScriptVariable):
    if value.get().inner in target.get().inner:
        return true
    else:
        return false

_STR_ITERATE_STOP_DEFAULT = sys.maxsize
@f_iterate_over.overload(("target", String), ("start", Integer, 0), ("stop", Integer, _STR_ITERATE_STOP_DEFAULT), ("step", Integer, 1))
def str_iterate_over(target:ScriptVariable[str], start:ScriptVariable[int], stop:ScriptVariable[int], step:ScriptVariable[int]):
    v = start.get().inner
    s = step.get().inner
    return script.wrap_python_value(_sequence_iterator(v-s, v, stop.get().inner, s, target.get().inner))

_LIST_ITERATE_STOP_DEFAULT = sys.maxsize
@f_iterate_over.overload(("target", List), ("start", Integer, 0), ("stop", Integer, _LIST_ITERATE_STOP_DEFAULT), ("step", Integer, 1))
def list_literate_over(target:ScriptVariable[list], start:ScriptVariable[int], stop:ScriptVariable[int], step:ScriptVariable[int]):
    v = start.get().inner
    s = step.get().inner
    return script.wrap_python_value(_sequence_iterator(v-s, v, stop.get().inner, s, target.get().inner))

@f_iterate_over.overload(("target", Map))
def map_literate_over(target:ScriptVariable[dict]):
    return script.wrap_python_value(_collection_iterator(-1, target.get().inner.keys()))

@f_iterate_over.overload(("target", Iterator))
def iterator_iterate_over(target:ScriptVariable[_iterator]):
    return target.get()

@f_iterate_over_range.overload(("start", Integer, 0), ("stop", Integer, _LIST_ITERATE_STOP_DEFAULT), ("step", Integer, 1))
def iterate_over_range(start:ScriptVariable[int], stop:ScriptVariable[int], step:ScriptVariable[int]):
    v = start.get().inner
    s = step.get().inner
    return script.wrap_python_value(_range_iterator(v-s, v, stop.get().inner, s))

@f_get.overload(("iterator", Iterator))
async def iterator_get(iterator:ScriptVariable[_iterator]):
    return script.wrap_python_value(await iterator.get().inner.get())

@f_next.overload(("iterator", Iterator))
async def iterator_next(iterator:ScriptVariable[_iterator]):
    it = iterator.get().inner
    try:
        n = await it.next()
    except NotImplementedError as e:
        raise exceptions.TNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented")
    elif n is None:
        return false
    else:
        iterator.assign(script.wrap_python_value(n))
        return true

@f_next.overload(("iterator", Iterator), ("out", (AnyType, NamePair)))
async def iterator_out_next(iterator:ScriptVariable[_iterator], out:ScriptVariable):
    it = iterator.get().inner
    try:
        n = await it.next()
    except NotImplementedError as e:
        raise exceptions.TNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented")
    elif n is None:
        return false
    try:
        v = await n.get()
    except NotImplementedError as e:
        raise exceptions.TNotImplemented(f"iterator {utils.script_repr(iterator.get())} does not yield values") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TNotImplemented(f"iterator {utils.script_repr(iterator.get())} does not yield values")
    iterator.assign(script.wrap_python_value(n))
    out.assign(script.wrap_python_value(v))
    return true

@f_reset.overload(("target", RangeIterator))
def range_iterator_reset(target:ScriptVariable[_range_iterator]):
    v = target.get().inner
    n = script.wrap_python_value(v._copy(v.start-v.step))
    target.assign(n)
    return n

@f_reset.overload(("target", CollectionIterator))
def collection_iterator_reset(target:ScriptVariable[_collection_iterator]):
    v = target.get().inner
    n = script.wrap_python_value(type(v)(-1, v._collection))
    target.assign(n)
    return n

@f_delete.overload(("name", String), pass_ctx=True)
def delete_name(ctx:ScriptContext, name:ScriptVariable[str]):
    n = name.get().inner
    v = ctx.stack.pop_name(n)
    if v is None:
        raise exceptions.TMissingName(f"Could not find name to delete: {repr(n)}")
    return v

@f_delete.overload(("value", [AnyType, NamePair]), ("key_or_index", [AnyType, NamePair]))
def delete_item(value:ScriptVariable, key_or_index:ScriptVariable):
    x = value.get()
    return x.type.delitem(x, key_or_index)

@f_delete_attribute.overload(("value", [AnyType, NamePair]), ("name", String))
def delete_attribute(value:ScriptVariable, name:ScriptVariable[str]):
    x = value.get()
    return x.type.delattr(x, name.get().inner)

def activate():
    if not mimetypes.inited:
        mimetypes.init()
    script.DATA_TYPE_TABLE[NullType.inner] = NullType.init()
    script.DATA_TYPE_TABLE[List_readonly.inner] = List_readonly.init()
    script.DATA_TYPE_TABLE[Map_readonly.inner] = Map_readonly.init()
    utils.DATA_TYPE_TABLE[MapItem.inner] = MapItem.init()
    utils.add_type(Iterator, constructor=False)
    utils.add_type(RangeIterator, constructor=False)
    utils.add_type(IterableIterator, constructor=False)
    utils.add_type(CollectionIterator, constructor=False)
    utils.add_type(SequenceIterator, constructor=False)
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
    utils.merge_function("iterate_over", f_iterate_over)
    utils.merge_function("iterate_over_range", f_iterate_over_range)
    utils.merge_function("get", f_get)
    utils.merge_function("next", f_next)
    utils.merge_function("reset", f_reset)
    utils.merge_function("delete", f_delete)
    utils.merge_function("delete_attribute", f_delete_attribute)

def deactivate():
    utils.remove_type(NullType)
    utils.remove_type(List_readonly)
    utils.remove_type(Map_readonly)
    utils.remove_type(MapItem)
    utils.remove_type(Iterator)
    utils.remove_type(RangeIterator)
    utils.remove_type(IterableIterator)
    utils.remove_type(CollectionIterator)
    utils.remove_type(SequenceIterator)
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
    utils.remove_function("iterate_over", f_iterate_over)
    utils.remove_function("iterate_over_range", f_iterate_over_range)
    utils.remove_function("get", f_get)
    utils.remove_function("next", f_next)
    utils.remove_function("reset", f_reset)
    utils.remove_function("delete", f_delete)
    utils.remove_function("delete_attribute", f_delete_attribute)
