from .script import *
from . import exceptions, duration_types as durtypes, json_proxy, number_units as numunits, script, utils
from .utils import ScriptFunction

import asyncio
from datetime import datetime, timedelta
import json
import math
import mimetypes
import string
import sys
from typing import BinaryIO, IO, Iterable, Literal, Sequence
import uuid


_TypeTypeAttrs = utils.ScriptAttributeHandler[type,Any]()
@_TypeTypeAttrs.enforce_child_attrs()
@_TypeTypeAttrs.attach
class _TypeType(ScriptDataType[type]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _TypeTypeAttrs
    attrs.wildcard = utils.ScriptValueAttribute[type,Any,Any]("")\
                            .getter(attrs.handle_type_get).setter(attrs.handle_type_set).deleter(attrs.handle_type_del)\
                            .itemgetter(attrs.handle_type_getitem).itemsetter(attrs.handle_type_setitem).itemdeleter(attrs.handle_type_delitem)
    attrs.entry("name").readonly(lambda o, n: script.wrap_python_value(script.DATA_TYPE_TABLE[o.inner].name))
    
    def repr(self, value):
        return script.ScriptValue(String, f"<type {script.DATA_TYPE_TABLE[value.inner].name} at {hex(id(value))}>")

_TypeAnnotationTypeAttrs = utils.ScriptAttributeHandler[ScriptTypeAnnotation,Any](no_subscripting=True)
@_TypeAnnotationTypeAttrs.enforce_child_attrs()
@_TypeAnnotationTypeAttrs.attach
class _TypeAnnotationType(ScriptDataType[ScriptTypeAnnotation]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _TypeAnnotationTypeAttrs
    attrs.entry("annotation_name").readonly(lambda o,n: script.wrap_python_value(o.inner.ANNOTATION_NAME))

    def repr(self, value):
        return script.ScriptValue(String, f"<type annotation {script.format_script_type_annotation(value.inner)}>")

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
        return script.ScriptValue(String, "null")

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
        return script.ScriptValue(String, repr(value.inner))

_IntegerTypeAttrs = utils.ScriptAttributeHandler[int,Any](no_subscripting=True)
@_IntegerTypeAttrs.enforce_child_attrs()
@_IntegerTypeAttrs.attach
class _IntegerType(ScriptDataType[int]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _IntegerTypeAttrs

    def repr(self, value):
        return script.ScriptValue(String, repr(value.inner))

_StringTypeAttrs = utils.ScriptAttributeHandler[str, int]()
@_StringTypeAttrs.enforce_child_attrs(*utils.ATTR_ATTACH_ATTRS)
@_StringTypeAttrs.attach
class _StringType(ScriptDataType[str]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct
    
    attrs = _StringTypeAttrs


    attrs.type_entry("WHITESPACE").readonly(utils.ValueGetAttribute(string.whitespace))
    attrs.type_entry("LOWERCASE").readonly(utils.ValueGetAttribute(string.ascii_lowercase))
    attrs.type_entry("UPPERCASE").readonly(utils.ValueGetAttribute(string.ascii_uppercase))
    attrs.type_entry("LETTERS").readonly(utils.ValueGetAttribute(string.ascii_letters))
    attrs.type_entry("DIGITS").readonly(utils.ValueGetAttribute(string.digits))
    attrs.type_entry("SYMBOLS").readonly(utils.ValueGetAttribute(string.punctuation))
    attrs.type_entry("PRINTABLE").readonly(utils.ValueGetAttribute(string.printable))

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
        return script.ScriptValue(String, repr(value.inner))

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
        return script.ScriptValue(String, "true" if value.inner else "false")

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
        return script.ScriptValue(String, sv)

class _pair[T,U]:
    def __init__(self, first:T, second:U):
        self.first = first
        self.second = second

    def __getitem__(self, index:int):
        if index == 0 or index == -1:
            return self.first
        elif index == 1 or index == -2:
            return self.second
        raise IndexError("pair index out of range")
    
    def __setitem__(self, index:int, value):
        if index == 0 or index == -1:
            self.first:T = value
        elif index == 1 or index == -2:
            self.second:U = value
        raise IndexError("pair index out of range")

    def __iter__(self):
        yield self.first
        yield self.second

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
        return script.ScriptValue(String, f"{self.name}({(fv:=wrap_python_value(value.inner.first)).type.repr(fv).inner}, {(sv:=wrap_python_value(value.inner.second)).type.repr(sv).inner})")

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
            raise exceptions.TRTypeError(f"{obj.type.name} can only be subscripted by a pair if it is or is convertable to a pair of ({Integer.name}|{null_name}, {Integer.name}|{null_name}), got pair ({script.wrap_python_type(type(v.inner.first)).name}, {script.wrap_python_type(type(v.inner.second)).name})")
        return slice(begin, end)
    else:
        raise exceptions.TRTypeError(f"{obj.type.name} must be subscriptied by a {Integer.name} or pair of ({Integer.name}, {Integer.name}), got {utils.script_repr(v)}")

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
        return script.ScriptValue(String, f"{self.name}({", ".join((v:=wrap_python_value(x)).type.repr(v).inner for x in value.inner)})")
    
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
        return script.ScriptValue(String, f"{self.name}({", ".join((k:=wrap_python_value(kx)).type.repr(k).inner + ": " + (v:=wrap_python_value(vx)).type.repr(v).inner for kx, vx in value.inner.items())})")

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
        elif isinstance(other, script.ScriptDataType):
            return other.issubtype(List)
        else:
            return False
    
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
        return " | ".join(script.format_script_type_annotation(t) for t in self._resolve_types())
    

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

    def _resolve_keys(self)->list[script.ScriptDataType|script.ScriptTypeAnnotation]:
        if not self._resolved_keys:
            for i, t in enumerate(self.key_types):
                if isinstance(t, str):
                    self.key_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.key_types[i] = script.wrap_python_type(t)
            self._resolved_keys = True
        return self.key_types

    def _resolve_values(self)->list[script.ScriptDataType|script.ScriptTypeAnnotation]:
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
        elif isinstance(other, script.ScriptDataType):
            return other.issubtype(Map)
        else:
            return False
    
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
        keystr = "|".join(script.format_script_type_annotation for t in self._resolve_keys())
        valstr = "|".join(script.format_script_type_annotation for t in self._resolve_values())
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

    def _resolve_first(self)->list[script.ScriptDataType|script.ScriptTypeAnnotation]:
        if not self._resolved_first:
            for i, t in enumerate(self.first_types):
                if isinstance(t, str):
                    self.first_types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.first_types[i] = script.wrap_python_type(t)
            self._resolved_first = True
        return self.first_types
    
    def _resolve_second(self)->list[script.ScriptDataType|script.ScriptTypeAnnotation]:
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
        elif isinstance(other, script.ScriptDataType):
            return other.issubtype(Pair)
        else:
            return False

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
        firststr = "|".join(script.format_script_type_annotation(t) for t in self._resolve_first())
        secondstr = "|".join(script.format_script_type_annotation(t) for t in self._resolve_second())
        return f"{firststr}, {secondstr}"

class IteratorOf(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "iterator_of"

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
        if isinstance(other, IteratorOf):
            return len(self._resolve_types()) == len(other._resolve_types()) and all(t in other.types for t in self.types)
        elif isinstance(other, script.ScriptDataType):
            return other.issubtype(Iterator)
        else:
            return False
    
    def compare(self, other):
        if isinstance(other, ScriptValue):
            if not other.type.issubtype(Iterator):
                return False
            assert isinstance(other.inner, _iterator)
            it = other.inner
        elif not isinstance(other, _iterator):
            return False
        else:
            it = other
        dts_l = []
        ann:list[ScriptTypeAnnotation] = []
        for t in self._resolve_types():
            if isinstance(t, script.ScriptDataType):
                dts_l.append(t.inner)
            else:
                ann.append(t)
        dts:tuple[type,...] = tuple(dts_l)
        
        try:
            it_iter = it.python_iterate()
        except NotImplementedError as e:
            return False
        except Exception as e:
            raise exceptions.wrap(e)
        if it_iter is NotImplemented or it_iter is None:
            return False
        for item in it_iter:
            if not (dts and isinstance(item, dts) or any(a.compare(item) for a in ann)):
                return False
        return True
    
    def format_data(self):
        return " | ".join(script.format_script_type_annotation(t) for t in self._resolve_types())
    

class NotType(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "not_type"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, ",|")
        return cls(*(script.parse_script_type_annotation(part) for part in parts))

    def __init__(self, *types:script.ScriptDataType|script.ScriptTypeAnnotation|type|str):
        if not types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        self.types = list(types)
        self._resolved = False

    def _resolve_types(self)->list[ScriptDataType|ScriptTypeAnnotation]:
        if not self._resolved:
            for i, t in enumerate(self.types):
                if isinstance(t, str):
                    self.types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.types[i] = script.wrap_python_type(t)
            self._resolved = True
        return self.types

    def __eq__(self, other):
        if isinstance(other, NotType):
            return len(self._resolve_types()) == len(other._resolve_types()) and all(t in other.types for t in self.types)
        elif isinstance(other, script.ScriptDataType):
            return not other.issubtype(*self._resolve_types())
        elif isinstance(other, ScriptTypeAnnotation):
            return all(other != t for t in self._resolve_types())
        else:
            return False

    def compare(self, other):
        if isinstance(other, ScriptValue):
            x = other.inner
        else:
            x = other
        for t in self._resolve_types():
            if isinstance(t, script.ScriptDataType):
                if isinstance(x, t.inner):
                    return False
            elif t.compare(x):
                return False
        return True

    def format_data(self):
        return ", ".join(script.format_script_type_annotation(t) for t in self._resolve_types())

class AllTypes(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "all_types"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, ",")
        return cls(*(script.parse_script_type_annotation(part) for part in parts))

    def __init__(self, *types:script.ScriptDataType|script.ScriptTypeAnnotation|type|str):
        if not types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        self.types = list(types)
        self._resolved = False

    def _resolve_types(self)->list[ScriptDataType|ScriptTypeAnnotation]:
        if not self._resolved:
            for i, t in enumerate(self.types):
                if isinstance(t, str):
                    self.types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.types[i] = script.wrap_python_type(t)
            self._resolved = True
        return self.types

    def __eq__(self, other):
        if isinstance(other, AllTypes):
            return len(self._resolve_types()) == len(other._resolve_types()) and all(t in other.types for t in self.types)
        elif isinstance(other, script.ScriptDataType):
            return all(other.issubtype(t) for t in self._resolve_types())
        elif isinstance(other, ScriptTypeAnnotation):
            return all(other == t for t in self._resolve_types())
        else:
            return False

    def compare(self, other):
        if isinstance(other, ScriptValue):
            x = other.inner
        else:
            x = other
        for t in self._resolve_types():
            if isinstance(t, script.ScriptDataType):
                if not isinstance(x, t.inner):
                    return False
            elif not t.compare(x):
                return False
        return True

    def format_data(self):
        return ", ".join(script.format_script_type_annotation(t) for t in self._resolve_types())

class AnyTypes(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "any_types"

    @classmethod
    def parse(cls, data:str)->Self:
        parts = script.split_type_annotation_contents(data, ",|")
        return cls(*(script.parse_script_type_annotation(part) for part in parts))

    def __init__(self, *types:script.ScriptDataType|script.ScriptTypeAnnotation|type|str):
        if not types:
            raise ValueError(f"{self.ANNOTATION_NAME} must be given one or more types or type annotations")
        self.types = list(types)
        self._resolved = False

    def _resolve_types(self)->list[ScriptDataType|ScriptTypeAnnotation]:
        if not self._resolved:
            for i, t in enumerate(self.types):
                if isinstance(t, str):
                    self.types[i] = script.parse_script_type_annotation(t)
                elif isinstance(t, type):
                    self.types[i] = script.wrap_python_type(t)
            self._resolved = True
        return self.types

    def __eq__(self, other):
        if isinstance(other, AnyTypes):
            return len(self._resolve_types()) == len(other._resolve_types()) and all(t in other.types for t in self.types)
        elif isinstance(other, script.ScriptDataType):
            return any(other.issubtype(t) for t in self._resolve_types())
        elif isinstance(other, ScriptTypeAnnotation):
            return any(other == t for t in self._resolve_types())
        else:
            return False

    def compare(self, other):
        if isinstance(other, script.ScriptValue):
            x = other.inner
        else:
            x = other
        for t in self._resolve_types():
            if isinstance(t, script.ScriptDataType):
                if isinstance(x, t.inner):
                    return True
            elif t.compare(x):
                return True
        return False

    def format_data(self):
        return ", ".join(script.format_script_type_annotation(t) for t in self._resolve_types())

class WholeNumber(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "whole_number"

    __slots__ = ()
    _instance = None

    @classmethod
    def parse(cls, data):
        if data:
            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} takes no arguments")
        return cls()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def __eq__(self, other):
        if isinstance(other, WholeNumber):
            return True
        elif isinstance(other, script.ScriptDataType):
            return other.issubtype(Integer, Float)
        else:
            return False

    def compare(self, other):
        if isinstance(other, script.ScriptValue):
            x = other.inner
        else:
            x = other
        if isinstance(x, int):
            return True
        elif isinstance(x, float):
            return x.is_integer()
        else:
            return False

    def format_data(self):
        return ""

_ListReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rolist_wrapper,int](_ListTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_ListReadonlyTypeAttrs.enforce_child_attrs()
@_ListReadonlyTypeAttrs.attach
class _ListReadonlyType(_ListType):
    
    attrs = _ListReadonlyTypeAttrs
    attrs.wildcard.itemnoset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).itemnodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)

_MapReadonlyTypeAttrs = utils.ScriptAttributeHandler[_rodict_wrapper,Any](_MapTypeAttrs, wildcard=utils.ScriptValueAttribute(""))
@_MapReadonlyTypeAttrs.enforce_child_attrs()
@_MapReadonlyTypeAttrs.attach
class _MapReadonlyType(_MapType):

    attrs = _MapReadonlyTypeAttrs
    attrs.wildcard.itemnoset(utils._DEFAULT_ITEM_READONLY_NO_ACCESS).itemnodel(utils._DEFAULT_ITEM_READONLY_NO_ACCESS)


class _iterator[T](numunits._functional_integer):

    @classmethod
    def from_bytes(cls, bytes, byteorder="big", *, signed=False):
        return cls(super().from_bytes(bytes, byteorder, signed=signed))

    async def next(self)->Self|None:
        return NotImplemented

    async def get(self)->T:
        return NotImplemented

    async def reset(self)->Self|None:
        return NotImplemented

    def python_iterate(self)->Iterable[T]:
        raise NotImplementedError

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

    def python_iterate(self):
        yield from range(self.start, self.stop, self.step)

    async def next(self):
        n:_range_iterator = self + self.step
        if n.in_range(n):
            return n
        else:
            return None

    async def get(self):
        return int(self)

    async def reset(self)->Self:
        return self._copy(int(self.start-self.step))

class _iterable_iterator[T](_iterator[T]):
    def __init__(self, value:int, iterable:Iterable[T], callback:Callable[[Self, Self, Any], Any]|None=None):
        self._iterator = iter(iterable)
        self._last = int(value)
        self._last_value:Any = None
        self.callback = callback

    async def next(self):
        n:_iterable_iterator = self + 1
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

class _iterator_iterator[T](_iterator[T]):
    def __init__(self, value:int, iterator:_iterator[T], stop:int, step:int):
        self._last = iterator
        self.start = iterator
        self.stop = stop
        self.step = step

    def python_iterate(self):
        x = self._last.python_iterate()
        if x is None or x is NotImplemented:
            return x
        yield from x

    def in_range(self, v:int):
        if self.step >= 0:
            return v >= self._last and v < self.stop
        else:
            return v <= self._last and v > self.stop

    async def next(self):
        n = self + self.step
        if n == 0:
            inn = await n._last.next()
            if inn is None or inn is NotImplemented:
                return inn
            n._last = inn
        else:
            inn = n._last
            for _ in range(self.step):
                inn = await inn.next()
                if inn is None or inn is NotImplemented:
                    return inn
            n._last = inn
        if n.in_range(n):
            return n
        else:
            return None

    async def get(self):
        return await self._last.get()

    async def reset(self):
        return type(self)(int(self.start), self.start, self.stop, self.step)

class _collection_iterator[T](_iterable_iterator[T]):
    def __init__(self, value, iterable:Iterable, callback:Callable[[Self, Self, Any], T]|None=None):
        super().__init__(value, iterable, callback)
        self._collection = iterable

    def __contains__(self, item):
        return item in self._collection

    def python_iterate(self):
        if self.callback is None:
            yield from self._collection
        else:
            for x in self._collection:
                yield self.callback(self, self, x)

    async def reset(self):
        return type(self)(-1, self._collection)
        
class _sequence_iterator[T](_range_iterator[T]):
    def __init__(self, value:int, start:int, stop:int, step:int, sequence:Sequence[T]):
        super().__init__(value, start, stop, step)
        self.sequence = sequence

    def in_range(self, v:int):
        if self.step >= 0:
            return v >= self.start and v < min(self.stop, len(self.sequence))
        else:
            return v <= self.start and v > min(self.stop, len(self.sequence))

    def python_iterate(self):
        for i in range(self.start, self.stop, self.step):
            yield self.sequence[i]

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
_RangeIteratorTypeAttrs:utils.ScriptAttributeHandler[_range_iterator,Any] = _RangeIteratorType.attrs
_RangeIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] from {value.inner.start} until {value.inner.stop} (step {value.inner.step})>")
_IterableIteratorType = make_iterator_type("_IterableIteratorType", _iterable_iterator, _IteratorType)
_IterableIteratorTypeAttrs:utils.ScriptAttributeHandler[_iterable_iterator,Any] = _IterableIteratorType.attrs
_IterableIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] : {utils.script_repr(script.wrap_python_value(value.inner._last_value))} of {utils.script_repr(script.wrap_python_value(value.inner._iterator))}>")
_IteratorIteratorType = make_iterator_type("_IteratorIteratorType", _iterator_iterator, _IteratorType)
_IteratorIteratorTypeAttrs:utils.ScriptAttributeHandler[_iterator_iterator,Any] = _IteratorIteratorType.attrs
_IteratorIteratorTypeAttrs.entry("inner").readonly(lambda o,n: script.wrap_python_value(o.inner._last))
_IteratorIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] over {utils.script_repr(script.wrap_python_value(value.inner._last))} (step {value.inner.step})>")
_CollectionIteratorType = make_iterator_type("_CollectionIterator", _collection_iterator, _IterableIteratorType)
_CollectionIteratorTypeAttrs:utils.ScriptAttributeHandler[_collection_iterator,Any] = _CollectionIteratorType.attrs
_CollectionIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] : {utils.script_repr(script.wrap_python_value(value.inner._last_value))} of {script.wrap_python_type(type(value.inner._collection)).name}>")
_SequenceIteratorType = make_iterator_type("_SequenceIteratorType", _sequence_iterator, _RangeIteratorType)
_SequenceIteratorTypeAttrs:utils.ScriptAttributeHandler[_sequence_iterator,Any] = _SequenceIteratorType.attrs
_SequenceIteratorType.repr = lambda self, value: script.wrap_python_value(f"<{value.type.name} [{int(value.inner)}] from {value.inner.start} until {min(value.inner.stop, len(value.inner.sequence))} (step {value.inner.step}) of {script.wrap_python_type(type(value.inner.sequence)).name}>")


_DatetimeTypeAttrs = utils.ScriptAttributeHandler[datetime, Any]()
@_DatetimeTypeAttrs.enforce_child_attrs()
@_DatetimeTypeAttrs.attach
class _DatetimeType(ScriptDataType[datetime]):

    f_construct:ScriptFunction[Self] = ScriptFunction()
    construct = f_construct

    attrs = _DatetimeTypeAttrs
    attrs.entry("year").readonly(lambda o,n: script.wrap_python_value(o.inner.year))
    attrs.entry("month").readonly(lambda o,n: script.wrap_python_value(o.inner.month))
    attrs.entry("day").readonly(lambda o,n: script.wrap_python_value(o.inner.day))
    attrs.entry("hour").readonly(lambda o,n: script.wrap_python_value(o.inner.hour))
    attrs.entry("minute").readonly(lambda o,n: script.wrap_python_value(o.inner.minute))
    attrs.entry("second").readonly(lambda o,n: script.wrap_python_value(o.inner.second))
    attrs.entry("microsecond").readonly(lambda o,n: script.wrap_python_value(o.inner.microsecond))

    def repr(self, value):
        attrs:list[tuple[str,float]] = [(name,v)for name in ("year","month","day","hour","minute","second","microsecond") if (v:=getattr(value.inner, name))]
        return script.ScriptValue(String, f"<datetime {", ".join(f"{name}={v}" for name,v in attrs)}>")

    def add(self, lhs, rhs):
        r = rhs.get()
        if r.type.issubtype(Duration):
            x:durtypes._duration = r.inner
            delta = timedelta(seconds=x.x * durtypes._unitspace_convert(durtypes._seconds_duration.FACTOR, durtypes._seconds_duration.POWER, x.FACTOR, x.POWER))
        elif r.type.issubtype(ComplexDuration):
            y:durtypes._complex_duration = r.inner
            delta = timedelta(seconds=y.as_seconds().x)
        else:
            return super().add(lhs, rhs)
        return script.wrap_python_value(lhs.get().inner + delta)

    def sub(self, lhs, rhs):
        r = rhs.get()
        if r.type.issubtype(Duration):
            x:durtypes._duration = r.inner
            delta = timedelta(seconds=x.x * durtypes._unitspace_convert(durtypes._seconds_duration.FACTOR, durtypes._seconds_duration.POWER, x.FACTOR, x.POWER))
        elif r.type.issubtype(ComplexDuration):
            y:durtypes._complex_duration = r.inner
            delta = timedelta(seconds=y.as_seconds().x)
        elif r.type.issubtype(Datetime):
            z:datetime = r.inner
            return script.wrap_python_value(durtypes._complex_duration(secs=(lhs.get().inner - z).total_seconds()).simplify())
        else:
            return super().sub(lhs, rhs)
        return script.wrap_python_value(lhs.get().inner - delta)

    def iadd(self, lhs, rhs):
        return self.add(lhs, rhs)

    def isub(self, lhs, rhs):
        return self.sub(lhs, rhs)
    

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


class _color:
    def to_rgba(self)->tuple[int,int,int,int]:
        raise NotImplementedError

    def to_hsla(self)->tuple[float,float,float,int]:
        raise NotImplementedError
    
    def to_hsva(self)->tuple[float,float,float,int]:
        raise NotImplementedError

    def to_cmyka(self)->tuple[int,int,int,int]:
        raise NotImplementedError

    def _to_this(self)->tuple:
        raise NotImplementedError

    def _to_that(self, t:"type[_color]"):
        if issubclass(t, _color_hsla):
            return self.to_hsla()
        elif issubclass(t, _color_hsva):
            return self.to_hsva()
        elif issubclass(t, _color_cmyka):
            return self.to_cmyka()
        else:
            return self.to_rgba()


    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError(f"must use int to subscript color for component item, got {type(key).__name__}")
        return self._to_this()[key]

    def __iter__(self):
        return iter(self._to_this())

    def __add__(self, other):
        return type(self)(*(x+other for x in self._to_this()))
    def __sub__(self, other):
        return type(self)(*(x-other for x in self._to_this()))
    def __mul__(self, other):
        return type(self)(*(x*other for x in self._to_this()))
    def __truediv__(self, other):
        return type(self)(*(x/other for x in self._to_this()))
    def __floordiv__(self, other):
        return type(self)(*(x//other for x in self._to_this()))
    def __mod__(self, other):
        return type(self)(*(x%other for x in self._to_this()))
    def __hash__(self):
        return hash(self._to_this())
    def __round__(self, ndigits=None):
        return type(self)(*(round(x,ndigits=ndigits) for x in self._to_this()))
    def __radd__(self, other):
        return type(self)(*(other+x for x in self._to_this()))
    def __rsub__(self, other):
        return type(self)(*(other-x for x in self._to_this()))
    def __rmul__(self, other):
        return type(self)(*(other*x for x in self._to_this()))
    def __rtruediv__(self, other):
        return type(self)(*(0 if x == 0 else other/x for x in self._to_this()))
    def __rfloordiv__(self, other):
        return type(self)(*(0 if x == 0 else other//x for x in self._to_this()))
    def __rmod__(self, other):
        return type(self)(*(0 if x == 0 else other%x for x in self._to_this()))
    def __eq__(self, value):
        if isinstance(value, _color):
            return self._to_this() == value._to_that(type(self))
        else:
            return all(a==value for a in self._to_this())
    def __ne__(self, value):
        if isinstance(value, _color):
            return self._to_this() != value._to_that(type(self))
        else:
            return all(a!=value for a in self._to_this())
    def __lt__(self, value):
        if isinstance(value, _color):
            return all(a<b for a,b in zip(self._to_this(), value._to_that(type(self))))
        else:
            return all(a<value for a in self._to_this())
    def __le__(self, value):
        if isinstance(value, _color):
            return all(a<=b for a,b in zip(self._to_this(), value._to_that(type(self))))
        else:
            return all(a<=value for a in self._to_this())
    def __gt__(self, value):
        if isinstance(value, _color):
            return all(a>b for a,b in zip(self._to_this(), value._to_that(type(self))))
        else:
            return all(a>value for a in self._to_this())
    def __ge__(self, value):
        if isinstance(value, _color):
            return all(a>=b for a,b in zip(self._to_this(), value._to_that(type(self))))
        else:
            return all(a>=value for a in self._to_this())
    

class _color_name(_color):

    #CITE: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/named-color
    NAME_MAP:dict[str, tuple[int,int,int,int]] = dict(
        black=(0, 0, 0, 255),
        silver=(192, 192, 192, 255),
        gray=(128, 128, 128, 255),
        grey=(128, 128, 128, 255),
        white=(255, 255, 255, 255),
        maroon=(128, 0, 0, 255),
        red=(255, 0, 0, 255),
        purple=(128, 0, 128, 255),
        fuchsia=(255, 0, 255, 255),
        magenta=(255, 0, 255, 255),
        green=(0, 128, 0, 255),
        lime=(0, 255, 0, 255),
        olive=(128, 128, 0, 255),
        yellow=(255, 255, 0, 255),
        navy=(0, 0, 128, 255),
        blue=(0, 0, 255, 255),
        teal=(128, 0, 128, 255),
        aqua=(255, 0, 255, 255),
        cyan=(0, 255, 255, 255),
        pink=(255, 192, 203, 255),
        aliceblue=(240, 248, 255, 255),
        antiquewhite=(250, 235, 215, 255),
        aquamarine=(127, 255, 212, 255),
        azure=(240, 255, 255, 255),
        beige=(245, 245, 220, 255),
        transparent= (0, 0, 0, 0),
        bisque=(255, 228, 196, 255),
        blanchedalmond=(255, 235, 205, 255),
        blueviolet=(138, 43, 226, 255),
        brown=(165, 42, 42, 255),
        burlywood=(222, 184, 135, 255),
        cadetblue=(95, 158, 160, 255),
        chartreuse=(127, 255, 0, 255),
        chocolate=(210, 105, 30, 255),
        coral=(255, 127, 80, 255),
        cornflowerblue=(100, 149, 237, 255),
        cornsilk=(255, 248, 220, 255),
        crimson=(220, 20, 60, 255),
        darkblue=(0, 0, 139, 255),
        darkcyan=(0, 139, 139, 255),
        darkgoldenrod=(184, 134, 11, 255),
        darkgray=(169, 169, 169, 255),
        darkgreen=(0, 100, 0, 255),
        darkgrey=(169, 169, 169, 255),
        darkkhaki=(189, 183, 107, 255),
        darkmagenta=(139, 0, 139, 255),
        darkolivegreen=(85, 107, 47, 255),
        darkorange=(255, 140, 0, 255),
        darkorchid=(153, 50, 204, 255),
        darkred=(139, 0, 0, 255),
        darksalmon=(233, 150, 122, 255),
        darkseagreen=(143, 188, 143, 255),
        darkslateblue=(72, 61, 139, 255),
        darkslategray=(47, 79, 79, 255),
        darkslategrey=(47, 79, 79, 255),
        darkturquoise=(0, 206, 209, 255),
        darkviolet=(148, 0, 211, 255),
        deeppink=(255, 20, 147, 255),
        deepskyblue=(0, 191, 255, 255),
        dimgray=(105, 105, 105, 255),
        dimgrey=(105, 105, 105, 255),
        dodgerblue=(30, 144, 255, 255),
        firebrick=(178, 34, 34, 255),
        floralwhite=(255, 250, 240, 255),
        forestgreen=(34, 139, 34, 255),
        gainsboro=(220, 220, 220, 255),
        ghostwhite=(248, 248, 255, 255),
        gold=(255, 215, 0, 255),
        goldenrod=(218, 165, 32, 255),
        greenyellow=(173, 255, 47, 255),
        honeydew=(240, 255, 240, 255),
        hotpink=(255, 105, 180, 255),
        indianred=(205, 92, 92, 255),
        indigo=(75, 0, 130, 255),
        ivory=(255, 255, 240, 255),
        khaki=(240, 230, 140, 255),
        lavender=(230, 230, 250, 255),
        lavenderblush=(255, 240, 245, 255),
        lawngreen=(124, 252, 0, 255),
        lemonchiffon=(255, 250, 205, 255),
        lightblue=(173, 216, 230, 255),
        lightcoral=(240, 128, 128, 255),
        lightcyan=(224, 255, 255, 255),
        lightgoldenrodyellow=(250, 250, 210, 255),
        lightgray=(211, 211, 211, 255),
        lightgreen=(144, 238, 144, 255),
        lightgrey=(211, 211, 211, 255),
        lightpink=(255, 182, 193, 255),
        lightsalmon=(255, 160, 122, 255),
        lightseagreen=(32, 178, 170, 255),
        lightskyblue=(135, 206, 250, 255),
        lightslategray=(119, 136, 153, 255),
        lightslategrey=(119, 136, 153, 255),
        lightsteelblue=(176, 196, 222, 255),
        lightyellow=(255, 255, 224, 255),
        limegreen=(50, 205, 50, 255),
        linen=(250, 240, 230, 255),
        mediumaquamarine=(102, 205, 170, 255),
        mediumblue=(0, 0, 205, 255),
        mediumorchid=(186, 85, 211, 255),
        mediumpurple=(147, 112, 219, 255),
        mediumseagreen=(60, 179, 113, 255),
        mediumslateblue=(123, 104, 238, 255),
        mediumspringgreen=(0, 250, 154, 255),
        mediumturquoise=(72, 209, 204, 255),
        mediumvioletred=(199, 21, 133, 255),
        midnightblue=(25, 25, 112, 255),
        mintcream=(245, 255, 250, 255),
        mistyrose=(255, 228, 225, 255),
        moccasin=(255, 228, 181, 255),
        navajowhite=(255, 222, 173, 255),
        oldlace=(253, 245, 230, 255),
        olivedrab=(107, 142, 35, 255),
        orange=(255, 165, 0, 255),
        orangered=(255, 69, 0, 255),
        orchid=(218, 112, 214, 255),
        palegoldenrod=(238, 232, 170, 255),
        palegreen=(152, 251, 152, 255),
        paleturquoise=(175, 238, 238, 255),
        palevioletred=(219, 112, 147, 255),
        papayawhip=(255, 239, 213, 255),
        peachpuff=(255, 218, 185, 255),
        peru=(205, 133, 63, 255),
        plum=(221, 160, 221, 255),
        powderblue=(176, 224, 230, 255),
        rebeccapurple=(102, 51, 153, 255),
        rosybrown=(188, 143, 143, 255),
        royalblue=(65, 105, 225, 255),
        saddlebrown=(139, 69, 19, 255),
        salmon=(250, 128, 114, 255),
        sandybrown=(244, 164, 96, 255),
        seagreen=(46, 139, 87, 255),
        seashell=(255, 245, 238, 255),
        sienna=(160, 82, 45, 255),
        skyblue=(135, 206, 235, 255),
        slateblue=(106, 90, 205, 255),
        slategray=(112, 128, 144, 255),
        slategrey=(112, 128, 144, 255),
        snow=(255, 250, 250, 255),
        springgreen=(0, 255, 127, 255),
        steelblue=(70, 130, 180, 255),
        tan=(210, 180, 140, 255),
        thistle=(216, 191, 216, 255),
        tomato=(255, 99, 71, 255),
        turquoise=(64, 224, 208, 255),
        violet=(238, 130, 238, 255),
        wheat=(245, 222, 179, 255),
        whitesmoke=(245, 245, 245, 255),
        yellowgreen=(154, 205, 50, 255),
    )

    @classmethod
    def get(cls, name:str, a:int=numunits.color_component_rgba.UPPER):
        if name in cls.NAME_MAP:
            return cls(name, a=a)

    def __init__(self, name:str, a:int=numunits.color_component_rgba.UPPER):
        self.name = name
        self.a = a

    def __str__(self):
        return self.name

    def to_rgba(self):
        r,g,b,a = self.NAME_MAP[self.name.lower()]
        return r, g, b, int(self.a)*a//255

    def to_hsla(self):
        return _color_rgba._hsla(*self.to_rgba())
    
    def to_hsva(self):
        return _color_rgba._hsva(*self.to_rgba())
    
    def to_cmyka(self):
        return _color_rgba._cmyka(*self.to_rgba())

    _to_this = to_rgba
        

class _color_rgba(_color):
    def __init__(self, r:int, g:int, b:int, a:int=numunits.color_component_rgba.UPPER):
        self.r = numunits.color_component_rgba(r)
        self.g = numunits.color_component_rgba(g)
        self.b = numunits.color_component_rgba(b)
        self.a = numunits.color_component_rgba(a)

    def to_rgba(self):
        return self.r, self.g, self.b, self.a

    @staticmethod
    def _hsla(r, g, b, a:numunits.color_component_rgba):
        r = int(r)/255
        g = int(g)/255
        b = int(b)/255
        xmax = max(r,g,b)
        xmin = min(r,g,b)
        d = xmax-xmin
        l = (xmax + xmin) / 2
        if abs(d) < 1E-14:
            s = 0.0
        elif l <= 0.5:
            s = d / (xmax + xmin)
        else:
            s = d / (2 - xmax - xmin)
        if d == 0:
            h = 0.0
        elif xmax == r:
            h = 60.0 * ((g - b)/d % 6)
        elif xmax == g:
            h = 60.0 * ((b - r)/d + 2)
        else: #xmax == b
            h = 60.0 * ((r - g)/d + 4)
        return h,s,l,a
    
    @staticmethod
    def _hsva(r, g, b, a:numunits.color_component_rgba):
        r = int(r)/255
        g = int(g)/255
        b = int(b)/255
        xmax = max(r,g,b)
        xmin = min(r,g,b)
        d = xmax-xmin
        v = xmax
        if xmax < 1E-14:
            s = 0.0
        else:
            s = d / xmax
        if d == 0:
            h = 0.0
        elif xmax == r:
            h = 60.0 * ((g - b)/d % 6)
        elif xmax == g:
            h = 60.0 * ((b - r)/d + 2)
        else: #xmax == b
            h = 60.0 * ((r - g)/d + 4)
        return h, s, v, a
        
    def _cmyka(r, g, b, a:numunits.color_component_rgba):
        r = int(r)/255
        g = int(g)/255
        b = int(b)/255
        k = 1-max(r,g,b)
        kcomp = 1-k
        if kcomp:
            c = (1 - r - k)/kcomp
            m = (1 - g - k)/kcomp
            y = (1 - b - k)/kcomp
        else:
            c = m = y = 0
        return (
            numunits.color_component_cmyk(min(c*100, 100)),
            numunits.color_component_cmyk(min(m*100, 100)),
            numunits.color_component_cmyk(min(y*100, 100)),
            numunits.color_component_cmyk(min(k*100, 100)),
            a
        )
    
    def to_hsla(self):
        return self._hsla(self.r, self.g, self.b, self.a)

    def to_hsva(self):
        return self._hsva(self.r, self.g, self.b, self.a)

    def to_cmyka(self):
        return self._cmyka(self.r, self.g, self.b, self.a)

    _to_this = to_rgba


class _color_hsla(_color):
    def __init__(self, h:numunits.degrees, s:numunits.percent, l:numunits.percent, a:int=numunits.color_component_rgba.UPPER):
        self.h = numunits.degrees(float(h))
        self.s = numunits.percent(float(s))
        self.l = numunits.percent(float(l))
        self.a = numunits.color_component_rgba(a)

    def to_rgba(self):
        hv = self.h.value
        C = (1 - abs(2 * self.l.value - 1)) * self.s.value
        X = C * (1 - abs((hv/60) % 2 - 1))
        m = self.l.value - C / 2
        if hv >= 0 and hv < 60:
            r = C
            g = X
            b = 0
        elif hv >= 60 and hv < 120:
            r = X
            g = C
            b = 0
        elif hv >= 120 and hv < 180:
            r = 0
            g = C
            b = X
        elif hv >= 180 and hv < 240:
            r = 0
            g = X
            b = C
        elif hv >= 240 and hv < 300:
            r = X
            g = 0
            b = C
        elif hv >= 300 and hv < 360:
            r = C
            g = 0
            b = X

        return (
            numunits.color_component_rgba(min(int((r+m)*255), 255)),
            numunits.color_component_rgba(min(int((g+m)*255), 255)),
            numunits.color_component_rgba(min(int((b+m)*255), 255)),
            self.a
        )

    def to_hsla(self):
        return (self.h.value, self.s.value, self.l.value, self.a)

    def to_hsva(self):
        lv = self.l.value
        sv = self.s.value
        v = lv + sv * min(lv, 1-lv)
        s = 0.0 if abs(v) < 1E-14 else 2 * (1 - lv/v)
        return (self.h.value, s, v, self.a)

    def to_cmyka(self):
        return _color_rgba._cmyka(*self.to_rgba)

    _to_this = to_hsla

class _color_hsva(_color):
    def __init__(self, h:numunits.degrees, s:numunits.percent, v:numunits.percent, a:int=numunits.color_component_rgba.UPPER):
        self.h = numunits.degrees(float(h))
        self.s = numunits.percent(float(s))
        self.v = numunits.percent(float(v))
        self.a = numunits.color_component_rgba(a)

    def to_rgba(self):
        hv = self.h.value
        C = self.v * self.s
        X = C * (1 - abs((hv/60) % 2 - 1))
        m = self.v.value - C
        if hv >= 0 and hv < 60:
            r = C
            g = X
            b = 0
        elif hv >= 60 and hv < 120:
            r = X
            g = C
            b = 0
        elif hv >= 120 and hv < 180:
            r = 0
            g = C
            b = X
        elif hv >= 180 and hv < 240:
            r = 0
            g = X
            b = C
        elif hv >= 240 and hv < 300:
            r = X
            g = 0
            b = C
        elif hv >= 300 and hv < 360:
            r = C
            g = 0
            b = X

        return (
            numunits.color_component_rgba(min(int((r+m)*255), 255)),
            numunits.color_component_rgba(min(int((g+m)*255), 255)),
            numunits.color_component_rgba(min(int((b+m)*255), 255)),
            self.a
        )

    def to_hsla(self):
        vv = self.v.value
        sv = self.s.value
        l = vv * (1 - sv/2)
        s = 0.0 if abs(l) < 1E-14 or abs(l-1) < 1E-14 else (vv - l)/min(l, 1-l)
        return (self.h.value, s, l, self.a)

    def to_hsva(self):
        return self.h.value, self.s.value, self.v.value, self.a

    def to_cmyka(self):
        return _color_rgba._cmyka(*self.to_rgba())

    _to_this = to_hsva


class _color_cmyka(_color):
    def __init__(self, c:int, m:int, y:int, k:int, a:int=numunits.color_component_rgba.UPPER):
        self.c = numunits.color_component_cmyk(c)
        self.m = numunits.color_component_cmyk(m)
        self.y = numunits.color_component_cmyk(y)
        self.k = numunits.color_component_cmyk(k)
        self.a = numunits.color_component_rgba(a)

    def to_rgba(self):
        kcomp = 1 - int(self.k)
        return (
            numunits.color_component_rgba(min(int((1 - int(self.c)/100)*kcomp*255), 255)),
            numunits.color_component_rgba(min(int((1 - int(self.m)/100)*kcomp*255), 255)),
            numunits.color_component_rgba(min(int((1 - int(self.y)/100)*kcomp*255), 255)),
            self.a
        )

    def to_hsla(self):
        return _color_rgba._hsla(*self.to_rgba())
    
    def to_hsva(self):
        return _color_rgba._hsva(*self.to_rgba())

    def to_cmyka(self):
        return self.c, self.m, self.y, self.y, self.a

    _to_this = to_cmyka


class _ColorComponentType(ScriptDataType[numunits.color_component]):
    def repr(self, value):
        return script.ScriptValue(String, f"<{value.type.name} {int(value.inner)}>")


def _typeattr_named_color(cname:str):
    c = _color_name(cname)
    def f(o:script.ScriptValue[type[_color]], n:str):
        if o.inner in (_color, _color_name):
            return script.wrap_python_value(c)
        return script.wrap_python_value(o.inner(*c._to_that(o.inner)))
    return f

_ColorBaseTypeAttrs = utils.ScriptAttributeHandler[_color,Any](no_type_subscripting=True)
@_ColorBaseTypeAttrs.enforce_child_attrs()
@_ColorBaseTypeAttrs.attach
class _ColorBaseType(ScriptDataType[_color]):

    f_construct = construct = utils.ScriptFunction()
    
    attrs = _ColorBaseTypeAttrs
    for cname in _color_name.NAME_MAP.keys():
        attrs.type_entry(cname).readonly(_typeattr_named_color(cname))
    del cname #make sure this isn't kept as a class attribute
    attrs.entry("length").readonly(lambda o,n: script.wrap_python_value(len(o.inner._to_this())))


_ColorNameTypeAttrs = utils.ScriptAttributeHandler[_color_name, Any](_ColorBaseTypeAttrs)
@_ColorNameTypeAttrs.enforce_child_attrs()
@_ColorNameTypeAttrs.attach
class _ColorNameType(ScriptDataType[_color_name]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _ColorNameTypeAttrs

    def repr(self, value):
        return script.ScriptValue(String, f"{self.name}({value.inner.name})")

    def conv_str(self, value):
        return script.ScriptValue(String, value.inner.name)

_ColorRGBTypeAttrs = utils.ScriptAttributeHandler[_color_rgba, Any](_ColorBaseTypeAttrs)
@_ColorRGBTypeAttrs.enforce_child_attrs()
@_ColorRGBTypeAttrs.attach
class _ColorRGBType(ScriptDataType[_color_rgba]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _ColorRGBTypeAttrs
    attrs.entry("r","red").readonly(utils.SimpleGetAttribute("r"))
    attrs.entry("g","green").readonly(utils.SimpleGetAttribute("g"))
    attrs.entry("b","blue").readonly(utils.SimpleGetAttribute("b"))
    attrs.entry("a","alpha").readonly(utils.SimpleGetAttribute("a"))

    def repr(self, value):
        return script.ScriptValue(String, f"{self.name}({int(value.inner.r)}, {int(value.inner.g)}, {int(value.inner.b)}, alpha={int(value.inner.a)})")

_ColorHSLTypeAttrs = utils.ScriptAttributeHandler[_color_hsla, Any](_ColorBaseTypeAttrs)
@_ColorHSLTypeAttrs.enforce_child_attrs()
@_ColorHSLTypeAttrs.attach
class _ColorHSLType(ScriptDataType[_color_hsla]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _ColorHSLTypeAttrs
    attrs.entry("h","hue").readonly(utils.SimpleGetAttribute("h"))
    attrs.entry("s","saturation").readonly(utils.SimpleGetAttribute("s"))
    attrs.entry("l","lightness").readonly(utils.SimpleGetAttribute("l"))
    attrs.entry("a","alpha").readonly(utils.SimpleGetAttribute("a"))

    def repr(self, value):
        return script.ScriptValue(String, f"{self.name}({round(value.inner.h.value, 12)}°, {round(float(value.inner.s)*100, 12)}%, {round(float(value.inner.l)*100, 12)}%, alpha={int(value.inner.a)})")

_ColorHSVTypeAttrs = utils.ScriptAttributeHandler[_color_hsva, Any](_ColorBaseTypeAttrs)
@_ColorHSVTypeAttrs.enforce_child_attrs()
@_ColorHSVTypeAttrs.attach
class _ColorHSVType(ScriptDataType[_color_hsva]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _ColorHSVTypeAttrs
    attrs.entry("h","hue").readonly(utils.SimpleGetAttribute("h"))
    attrs.entry("s","saturation").readonly(utils.SimpleGetAttribute("s"))
    attrs.entry("v","value").readonly(utils.SimpleGetAttribute("v"))
    attrs.entry("a","alpha").readonly(utils.SimpleGetAttribute("a"))

    def repr(self, value):
        return script.ScriptValue(String, f"{self.name}({round(value.inner.h.value, 12)}°, {round(float(value.inner.s)*100, 12)}%, {round(float(value.inner.v)*100, 12)}%, alpha={int(value.inner.a)})")

_ColorCMYKTypeAttrs = utils.ScriptAttributeHandler[_color_cmyka, Any](_ColorBaseTypeAttrs)
@_ColorCMYKTypeAttrs.enforce_child_attrs()
@_ColorCMYKTypeAttrs.attach
class _ColorCMYKType(ScriptDataType[_color_cmyka]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _ColorCMYKTypeAttrs
    attrs.entry("c","cyan").readonly(utils.SimpleGetAttribute("c"))
    attrs.entry("m","magenta").readonly(utils.SimpleGetAttribute("m"))
    attrs.entry("y","yellow").readonly(utils.SimpleGetAttribute("y"))
    attrs.entry("k","key","b","black").readonly(utils.SimpleGetAttribute("k"))
    attrs.entry("a","alpha").readonly(utils.SimpleGetAttribute("a"))

    def repr(self, value):
        return script.ScriptValue(String, f"{self.name}({int(value.inner.c)}, {int(value.inner.m)}, {int(value.inner.y)}, {int(value.inner.k)}, alpha={int(value.inner.a)})")

    
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
            raise exceptions.TRTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
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
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
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
                raise exceptions.TRTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
            return v
        else:
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
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
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
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
            raise exceptions.TRTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
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
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
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
                raise exceptions.TRTypeError(f"expected object of type {smt.name}, got object of type {v.type.name}")
            return v
        else:
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
    
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
            raise exceptions.TRTypeError(f"{obj.type.name}[...] expected {String.name} or {Integer.name}, got {key.type.name}")
        
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

    def add(self, lhs, rhs):
        r = rhs.get()
        if r.type.issubtype(Datetime):
            x = lhs.get().inner
            delta = timedelta(seconds=x.x * durtypes._unitspace_convert(durtypes._seconds_duration.FACTOR, durtypes._seconds_duration.POWER, x.FACTOR, x.POWER))
            return script.wrap_python_value(r.inner + delta)
        else:
            super().add(lhs, rhs)
    

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

    def add(self, lhs, rhs):
        r = rhs.get()
        if r.type.issubtype(Datetime):
            y = lhs.get().inner
            delta = timedelta(seconds=y.as_seconds().x)
            return script.wrap_python_value(r.inner + delta)
        else:
            super().add(lhs, rhs)


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

_FunctionParameterTypeAttrs = utils.ScriptAttributeHandler[utils.ScriptFunctionParam, Any]()
@_FunctionParameterTypeAttrs.enforce_child_attrs()
@_FunctionParameterTypeAttrs.attach
class _FunctionParameterType(script.ScriptDataType[utils.ScriptFunctionParam]):

    f_construct = construct = utils.ScriptFunction()

    attrs = _FunctionParameterTypeAttrs
    attrs.entry("name").readonly(utils.SimpleGetAttribute("name"))
    attrs.entry("types").readonly(lambda o,n: _rolist_wrapper(list(o.inner.resolve_types())))
    attrs.entry("default").readonly(lambda o,n: script.wrap_python_value(o.inner.default))
    attrs.entry("pack").readonly(utils.SimpleGetAttribute("pack"))

AnyType = BASE_TYPE
Type = _TypeType("type", type, BASE_TYPE)
TypeAnnotation = _TypeAnnotationType("type_annoation", ScriptTypeAnnotation, BASE_TYPE)
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
List_readonly = _ListReadonlyType("readonly_list", _rolist_wrapper, List)
Map_readonly = _MapReadonlyType("readonly_map", _rodict_wrapper, Map)
Iterator = _IteratorType("iterator", _iterator, Integer)
RangeIterator = _RangeIteratorType("range_iterator", _range_iterator, Iterator)
IterableIterator = _IterableIteratorType("iterable_iterator", _iterable_iterator, Iterator)
IteratorIterator = _IteratorIteratorType("iterator_iterator", _iterator_iterator, Iterator)
CollectionIterator = _CollectionIteratorType("collection_iterator", _collection_iterator, IterableIterator)
SequenceIterator = _SequenceIteratorType("sequence_iterator", _sequence_iterator, RangeIterator)
Datetime = _DatetimeType("datetime", datetime, BASE_TYPE)
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
FunctionParameter = _FunctionParameterType("FunctionParameter", utils.ScriptFunctionParam, BASE_TYPE)
ColorComponent = _ColorComponentType("color_component", numunits.color_component, Integer)
ColorComponentRGBA = _ColorComponentType("rgba_color_component", numunits.color_component_rgba, ColorComponent)
ColorComponentCMYK = _ColorComponentType("cmyk_color_component", numunits.color_component_cmyk, ColorComponent)
Color = _ColorBaseType("color", _color, BASE_TYPE)
NamedColor = _ColorNameType("named_color", _color_name, Color)
ColorRGB = _ColorRGBType("color_rgb", _color_rgba, Color)
ColorHSL = _ColorHSLType("color_hsl", _color_hsla, Color)
ColorHSV = _ColorHSVType("color_hsv", _color_hsva, Color)
ColorCMYK = _ColorCMYKType("color_cmyk", _color_cmyka, Color)

_StringTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_ListTypeAttrs.wildcard.itemgetter(List.getitem).itemsetter(List.setitem).itemdeleter(List.delitem)
_MapTypeAttrs.wildcard.itemgetter(BASE_TYPE.getitem).itemsetter(BASE_TYPE.setitem).itemdeleter(BASE_TYPE.delitem)
_JsonProxyNodeTypeAttrs.wildcard.reverse_attach(JsonNode)

null = script.ScriptValue(NullType, None)
true = script.ScriptValue(Bool, True)
false = script.ScriptValue(Bool, False)
PI = script.ScriptValue(Float, math.pi)

_builtin_types:list[ScriptDataType] = [
    Type, TypeAnnotation, Float, Integer, String, Bool, NamePair, Pair, List, Map, UUID, Datetime,
    File, Nanoseconds, Microseconds, Milliseconds, Seconds, Minutes, Hours, Weeks,
    Days, Percent, Degrees, Radians, FunctionParameter, Color, ColorRGB, ColorHSL, ColorHSV,
    ColorCMYK, NamedColor
]

@_TypeType.f_construct.overload(("value", [AnyType, NamePair]))
def type_construct(self, value:ScriptVariable):
    return script.ScriptValue(self, value.type().inner)

@_TypeAnnotationType.f_construct.overload(dict(name="values", dtypes=[AnyType, NamePair], pack=True))
def type_annotation_type_construct(self:_TypeAnnotationType, *values:ScriptVariable):
    return script.wrap_python_value(self.inner(*(value.get().inner for value in values)))

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
        raise exceptions.TRNotImplemented(f"str() for {v.type.name} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if x is None:
        raise exceptions.TRMustEvaluate(f"str() for {v.type.name} must evaluate but resulted in no value")
    elif x is NotImplemented:
        raise exceptions.TRNotImplemented(f"str() for {v.type.name} is not implemented")
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
        raise exceptions.TRNotImplemented(f"bool() for {v.type.name} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if x is None:
        raise exceptions.TRMustEvaluate(f"bool() for {v.type.name} must evaluate but resulted in no value")
    elif x is NotImplemented:
        raise exceptions.TRNotImplemented(f"bool() for {v.type.name} is not implemented")
    return x

@_NameValuePairType.f_construct.overload(("name", String), ("value", AnyType))
def nvpair_construct(self, name:ScriptVariable[str], value:ScriptVariable):
    return script.ScriptValue(self, ScriptNameValuePair(name.get().inner, value.get().inner))

@_PairType.f_construct.overload(("first", AnyType), ("second", AnyType))
def pair_construct(self, first:ScriptVariable, second:ScriptVariable):
    return script.ScriptValue(self, _pair(first.get().inner, second.get().inner))

@_PairType.f_construct.overload(("npair", NamePair))
def pair_construct_nvpair(self:_PairType, npair:ScriptVariable[script.ScriptNameValuePair]):
    nv = npair.get().inner
    return script.ScriptValue(self, self.inner(nv.name, nv.value))

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

@_DatetimeType.f_construct.overload(("year", [Integer,Float]), ("month", [Integer,Float]), ("day", [Integer,Float]),
                                    ("hour", [Integer,Float]), ("minute", [Integer,Float]), ("second", [Integer,Float]), ("microsecond", [Integer,Float]))
def datetime_construct(self, year:ScriptVariable[int|float], month:ScriptVariable[int|float], day:ScriptVariable[int|float],
                       hour:ScriptVariable[int|float], minute:ScriptVariable[int|float], second:ScriptVariable[int|float], microsecond:ScriptVariable[int|float]):
    return script.ScriptValue(Datetime, datetime(year.get().inner, month.get().inner, day.get().inner, hour.get().inner, minute.get().inner, second.get().inner, microsecond.get().inner))

@_UUIDType.f_construct.overload(("hex", String))
def uuid_construct(self, hex:ScriptVariable[str]):
    return script.ScriptValue(self, uuid.UUID(hex))

def resolve_file_mode(mode:ScriptVariable[str]):
    m = mode.get().inner.lower()
    if m not in ("read", "write", "append"):
        raise exceptions.TRBadValue(f"file mode must be read, write, or append; got {mode.get().inner}")
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

@_PercentType.f_construct.overload(("value", ColorComponent))
def percent_construct_color_component(self:ScriptDataType[numunits.percent], value:ScriptVariable[numunits.color_component]):
    v = value.get().inner
    vrange = v.UPPER - v.LOWER
    return script.wrap_python_value(self.inner((v-v.LOWER)/vrange))

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

_FUNC_PARAM_NO_DEFAULT = object()
@_FunctionParameterType.f_construct.overload(("name", String), ("data_types", [String, Type, TypeAnnotation, ListOf(String, Type, TypeAnnotation)], ScriptValue(Type, object)), ("default", AnyType, _FUNC_PARAM_NO_DEFAULT), ("pack", Bool, false))
def FunctionParameter_construct(self:ScriptDataType[utils.ScriptFunctionParam], name:ScriptVariable[str], data_types:ScriptVariable[type|ScriptTypeAnnotation|str|list[type|ScriptTypeAnnotation|str]], default:ScriptVariable, pack:ScriptVariable[bool]):
    dtv = data_types.get()
    if dtv.type.issubtype(List):
        dts = [script.DATA_TYPE_TABLE[dt] if isinstance(dt, type) else dt for dt in dtv.inner]
    elif dtv.type.issubtype(Type):
        dts = []
    else:
        dts = [dtv.inner]
    return script.wrap_python_value(utils.ScriptFunctionParam(
        name.get().inner, dts,
        utils._PARAM_NO_DEFAULT if (df := default.get().inner) is _FUNC_PARAM_NO_DEFAULT else df,
        pack.get().inner
    ))


_PATTERN_INT = r"[0-9]+"
_PATTERN_FLOAT = r"[0-9]*\.[0-9]+"
_PATTERN_COLOR_COMPONENT = f"(?:^\\s*|\\s*[\\/,]?\\s*)(?:(?P<float>{_PATTERN_FLOAT})|(?P<int>{_PATTERN_INT}))\\s*(?:(?P<percent>%)|(?P<degrees>deg|°))?\\s*"
_RE_COLOR_COMPONENT = re.compile(_PATTERN_COLOR_COMPONENT)

def _re_color_alpha(s:str, k:int):
    m = _RE_COLOR_COMPONENT.match(s, k)
    if m is None:
        return
    k += m.end()-k
    f = m["float"]
    i = m["int"]
    p = m["percent"]
    d = m["degrees"]
    if d:
        ... #TODO error alpha component cannot be given in degrees
    if p:
        if f is None:
            iv = int(i)
            if iv < 0  or iv > 100:
                ... #TODO error component percentage not in range (must be between 0% and 100%, inclusive)
            return numunits.color_component_rgba.from_percent(iv/100)
        else:
            #p = (v-lower)/(upper-lower)
            #v = p*(upper-lower)+lower
            fv = float(f)
            if fv<1E-14 or (fv-100)>1E-14:
                ... #TODO error component percentage not in range (must be between 0.0% and 100.0%, inclusive)
            return numunits.color_component_rgba.from_percent(fv/100)
    elif f is None:
        iv = int(i)
        if iv < numunits.color_component_rgba.LOWER or iv > numunits.color_component_rgba.UPPER:
            ... #TODO error component value not in range (must be between lower and upper, inclusive)
        return numunits.color_component_rgba(iv)
    else:
        fv = float(f)
        if fv < 0 or fv > 1:
            ... #TODO error component percentage not in range (must be between 0.0 and 1.0, inclusive)
        return numunits.color_component_rgba.from_percent(fv)

def _rgb_construct(s:str):
    k = 0
    parsed = []
    for j in range(3):
        m = _RE_COLOR_COMPONENT.match(s, k)
        if m is None:
            ... #TODO error missing color components
            assert False, str(j)
        k += m.end()-k

        f = m["float"]
        i = m["int"]
        p = m["percent"]
        d = m["degrees"]
        if d:
            ... #TODO error RGB components cannot be given in degrees
        if p:
            if f is None:
                iv = int(i)
                if iv < 0  or iv > 100:
                    ... #TODO error component percentage not in range (must be between 0% and 100%, inclusive)
                parsed.append(numunits.color_component_rgba.from_percent(iv/100))
            else:
                fv = float(f)
                if fv<1E-14 or (fv-100)>1E-14:
                    ... #TODO error component percentage not in range (must be between 0.0% and 100.0%, inclusive)
                parsed.append(numunits.color_component_rgba.from_percent(fv/100))
        elif f is None:
            iv = int(i)
            if iv < numunits.color_component_rgba.LOWER or iv > numunits.color_component_rgba.UPPER:
                ... #TODO error component value not in range (must be between lower and upper, inclusive)
            parsed.append(iv)
        else:
            fv = float(f)
            if fv < 0 or iv > 1:
                ... #TODO error component percentage not in range (must be between 0.0 and 1.0, inclusive)
            parsed.append(numunits.color_component_rgba.from_percent(fv))

    alpha = _re_color_alpha(s, k)
    if alpha is not None:
        parsed.append(alpha)
    
    return _color_rgba(*parsed)

def _hue_sat_func(t:type[_color_hsla|_color_hsva]):
    def _hue_sat_construct(s:str):
        parsed = []
        k = 0
        m = _RE_COLOR_COMPONENT.match(s)
        if m is None:
            ... #TODO error hue value is needed
        k += m.end()-k
        f = m["float"]
        i = m["int"]
        p = m["percent"]
        d = m["degrees"]

        if p:
            #mod 36000 allows for more accuracy to be kept when clamping to [0, 360) range
            if f is None:
                v = int(i) * 360 % 36000 / 100
            else:
                v = float(f) * 360 % 36000 / 100
            parsed.append(numunits.degrees(v))
        elif f is None:
            parsed.append(numunits.degrees(int(i) % 360))
        elif i is None:
            ... #TODO error must specify value for hue component
        else:
            parsed.append(numunits.degrees(float(f) % 360))

        for _ in range(2):
            m = _RE_COLOR_COMPONENT.match(s, k)
            if m is None:
                ... #TODO error missing color components
            k += m.end()-k
    
            f = m["float"]
            i = m["int"]
            p = m["percent"]
            d = m["degrees"]

            if d:
                ... #TODO error component cannot be given in degrees
            elif f is None:
                parsed.append(numunits.percent(int(i)/100))
            else:
                parsed.append(numunits.percent(float(f)/100))

        alpha = _re_color_alpha(s, k)
        if alpha is not None:
            parsed.append(alpha)
        return t(*parsed)
    return _hue_sat_construct


def _cmyk_construct(s:str):
    k = 0
    parsed = []
    for j in range(4):
        m = _RE_COLOR_COMPONENT.match(s, k)
        if m is None:
            ... #TODO error missing color components
        k += m.end()-k

        f = m["float"]
        i = m["int"]
        p = m["percent"]
        d = m["degrees"]
        if d:
            ... #TODO error CMKY components cannot be given in degrees
        elif f is None:
            iv = int(i)
            if iv < numunits.color_component_cmyk.LOWER  or iv > numunits.color_component_cmyk.UPPER:
                ... #TODO error component value not in range (must be between lower and upper, inclusive)
            parsed.append(numunits.color_component_cmyk(iv))
        else:
            fv = float(f)
            if fv<1E-14 or (fv-100)>1E-14:
                ... #TODO error component percentage not in range (must be between 0.0% and 100.0%, inclusive)
            parsed.append(numunits.color_component_cmyk(fv))

    alpha = _re_color_alpha(s, k)
    if alpha is not None:
        parsed.append(alpha)
    
    return _color_cmyka(*parsed)

            
    

_color_fmap = dict(
    rgb=_rgb_construct,
    hsl=_hue_sat_func(_color_hsla),
    hsv=_hue_sat_func(_color_hsva),
    cmyk=_cmyk_construct,
    rgba=_rgb_construct,
    hsla=_hue_sat_func(_color_hsla),
    hsva=_hue_sat_func(_color_hsva),
    cmyka=_cmyk_construct,
)
@_ColorBaseType.f_construct.overload(("formatted", String))
def Color_construct(self:ScriptDataType[_color], formatted:ScriptVariable[str]):
    fs = formatted.get().inner.strip().lower()
    startp = fs.find("(")
    if startp != -1:
        endp = fs.rfind(")")
        if endp == -1 or endp!=len(fs)-1:
            ... #TODO error bad color string
        name = fs[0:startp]
        args = fs[startp+1:endp]
        f = _color_fmap.get(name,None)
        if f is None:
            ... #TODO error bad color format name
        if not args:
            ... #TODO error missing color components
        return script.wrap_python_value(f(args))
    elif ")" in fs:
        ... #TODO error bad color string
    
    if fs.startswith("#"):
        fs = fs[1:]
    else:
        cname = _color_name.get("".join(c for c in fs if not c.isspace()))
        if cname is not None:
            return script.wrap_python_value(cname)
    lfs = len(fs)
    if lfs not in (3, 4, 6, 8):
        ... #TODO error bad color string
    if any(c not in "0123456789abcdef" for c in fs):
        ... #TODO error bad color string
    x = int(fs, 16)
    if x:
        if lfs <= 4:
            return script.wrap_python_value(_color_rgba(*(int(c*2,16) for c in fs)))
        else:
            return script.wrap_python_value(_color_rgba(*(int(fs[i:i+2],16) for i in range(0, len(fs), 2))))
    else:
        return script.wrap_python_value(_color_rgba(0, 0, 0, 255 * (len(fs)%4)))

@_ColorNameType.f_construct.overload(("name", String), ("alpha", WholeNumber(), numunits.color_component_rgba.UPPER))
def ColorName_construct(self, name:ScriptVariable[str], alpha:ScriptVariable):
    return script.wrap_python_value(_color_name(name.get().inner, alpha.get().inner))

def _resolve_color_component[T:numunits.color_component](c:ScriptVariable, ctype:type[T]):
    x = c.get()
    if x.type.issubtype(Percent):
        return ctype.from_percent(float(x.inner), clamp=False)
    else:
        return int(x.inner)

@_ColorNameType.f_construct.overload(("red", [WholeNumber(), Percent]), ("green", [WholeNumber(), Percent]), ("blue", [WholeNumber(), Percent]), ("alpha", [WholeNumber(), Percent], numunits.color_component_rgba.UPPER))
def ColorName_from_rgba(self, red:script.ScriptVariable, green:script.ScriptVariable, blue:script.ScriptVariable, alpha:script.ScriptVariable):
    r = _resolve_color_component(red, numunits.color_component_rgba)
    g = _resolve_color_component(green, numunits.color_component_rgba)
    b = _resolve_color_component(blue, numunits.color_component_rgba)
    a = _resolve_color_component(alpha, numunits.color_component_rgba)
    if not (r or g or b or a):
        return script.wrap_python_value(_color_name("transparent"))
    for name, (nr, ng, nb, na) in _color_name.NAME_MAP.items():
        if r == nr and g == ng and b == nb:
            return script.wrap_python_value(_color_name(name, (numunits.color_component_rgba.UPPER*(a+0.5)//na) if na else numunits.color_component_rgba.UPPER)) #estimates the value which when blended with na will result in a
    raise exceptions.TRBadValue("given color components do not correspond to a named color")

@_ColorRGBType.f_construct.overload(("red", [WholeNumber(), Percent]), ("green", [WholeNumber(), Percent]), ("blue", [WholeNumber(), Percent]), ("alpha", [WholeNumber(), Percent], numunits.color_component_rgba.UPPER))
def ColorRGB_construct(self, red:script.ScriptVariable, green:script.ScriptVariable, blue:script.ScriptVariable, alpha:script.ScriptVariable):
    r = _resolve_color_component(red, numunits.color_component_rgba)
    g = _resolve_color_component(green, numunits.color_component_rgba)
    b = _resolve_color_component(blue, numunits.color_component_rgba)
    a = _resolve_color_component(alpha, numunits.color_component_rgba)
    return script.wrap_python_value(_color_rgba(r, g, b, a))

@_ColorHSLType.f_construct.overload(("hue", [Integer, Float, Degrees, Radians, Percent]), ("saturation", [Integer, Float, Percent]), ("lightness", [Integer, Float, Percent]), ("alpha", WholeNumber(), numunits.color_component_rgba.UPPER))
def ColorHSL_construct(self, hue:ScriptVariable[int|float|numunits.degrees|numunits.radians|numunits.percent], saturation:ScriptVariable[int|float|numunits.percent], lightness:ScriptVariable[int|float|numunits.percent], alpha:ScriptVariable):
    h = hue.get()
    if h.type.issubtype(Percent):
        hd = float(h.inner) * 360 % 360
    elif h.type.issubtype(Radians):
        hd = math.degrees(float(h.inner))
    else:
        hd = float(h.inner)
    return script.wrap_python_value(_color_hsla(hd, saturation.get().inner, lightness.get().inner, alpha.get().inner))

@_ColorHSVType.f_construct.overload(("hue", [Integer, Float, Degrees, Radians, Percent]), ("saturation", [Integer, Float, Percent]), ("value", [Integer, Float, Percent]), ("alpha", WholeNumber(), numunits.color_component_rgba.UPPER))
def ColorHSV_construct(self, hue:ScriptVariable[int|float|numunits.degrees|numunits.radians|numunits.percent], saturation:ScriptVariable[int|float|numunits.percent], value:ScriptVariable[int|float|numunits.percent], alpha:ScriptVariable):
    h = hue.get()
    if h.type.issubtype(Percent):
        hd = float(h.inner) * 360 % 360
    elif h.type.issubtype(Radians):
        hd = math.degrees(float(h.inner))
    else:
        hd = float(h.inner)
    return script.wrap_python_value(_color_hsla(hd, saturation.get().inner, value.get().inner, alpha.get().inner))

@_ColorCMYKType.f_construct.overload(("cyan", [WholeNumber(), Percent]), ("magenta", [WholeNumber(), Percent]), ("yellow", [WholeNumber(), Percent]), ("key", [WholeNumber(), Percent]), ("alpha", [WholeNumber(), Percent], numunits.color_component_rgba.UPPER))
def ColorCMYK_construct(self, cyan:ScriptVariable, magenta:ScriptVariable, yellow:ScriptVariable, key:ScriptVariable, alpha:ScriptVariable):
    c = _resolve_color_component(cyan, numunits.color_component_cmyk)
    m = _resolve_color_component(magenta, numunits.color_component_cmyk)
    y = _resolve_color_component(yellow, numunits.color_component_cmyk)
    k = _resolve_color_component(key, numunits.color_component_cmyk)
    a = _resolve_color_component(alpha, numunits.color_component_rgba)
    return script.wrap_python_value(_color_cmyka(c, m, y, k, a))

f_list_from = ScriptFunction()
f_map_from = ScriptFunction()
f_is = ScriptFunction()
f_issubtype = ScriptFunction()
f_has = ScriptFunction()
f_hasfunc = ScriptFunction()
f_print = ScriptFunction()
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
f_now = ScriptFunction()
f_round = ScriptFunction()
f_format = ScriptFunction()
f_split = ScriptFunction()
f_join = ScriptFunction()
f_trim = ScriptFunction()

trait_Appendable = utils.ScriptTrait("append", 0, [AnyType], dict(dtypes=[AnyType]))
trait_Container = utils.ScriptTrait("contains", 0, [AnyType], dict(dtypes=[AnyType]))
trait_Iterable = utils.ScriptTrait("iterate_over", 0, [AnyType])
trait_CanFind = utils.ScriptTrait("find", 0, [AnyType], dict(dtypes=[AnyType]))
trait_CanDelete = utils.ScriptTrait("delete", 0, [AnyType], dict(dtypes=[AnyType]))
trait_Roundable = utils.ScriptTrait("round", 0, [AnyType])
trait_Formattable = utils.ScriptTrait("format", 0, [AnyType])
trait_Splittable = utils.ScriptTrait("split", 0, [AnyType])
trait_CanJoinOn = utils.ScriptTrait("join", 0, [AnyType])
trait_Trimmable = utils.ScriptTrait("trim", 0, [AnyType])

@f_list_from.overload(("target", List))
def list_from_list(target:ScriptVariable[list]):
    return target.get()

@f_list_from.overload(("target", Map))
def list_from_map(target:ScriptVariable[dict]):
    return script.wrap_python_value(list(target.get().inner.items()))

@f_list_from.overload(("target", String))
def list_from_string(target:ScriptVariable[str]):
    return script.wrap_python_value(list(target.get().inner))

@f_list_from.overload(("target", Iterator))
async def list_from_iterator(target:ScriptVariable[_iterator]):
    l = []
    n = target.get().inner
    while True:
        try:
            n = await n.next()
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(target.get())} is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if n is NotImplemented:
            raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(target.get())} is not implemented")
        elif n is None:
            break
        try:
            v = await n.get()
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(target.get())} does not yield values") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if v is NotImplemented:
            raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(target.get())} does not yield values")
        if isinstance(v, script.ScriptValue):
            v = v.inner
        l.append(v)
    return script.wrap_python_value(l)

@f_map_from.overload(("target", Map))
def map_from_map(target:ScriptVariable[dict]):
    return target.get()

@f_map_from.overload(("target", ListOf(Pair, NamePair)))
def map_from_list(target:ScriptVariable[list[_pair|ScriptNameValuePair]]):
    return dict(tuple(x) for x in target.get().inner)

@f_map_from.overload(("target", IteratorOf(Pair, NamePair)))
async def map_from_iterator(target:ScriptVariable[_iterator[_pair|ScriptNameValuePair]]):
    d = {}
    n = target.get().inner
    while True:
        try:
            n = await n.next()
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(target.get())} is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if n is NotImplemented:
            raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(target.get())} is not implemented")
        elif n is None:
            break
        try:
            v = await n.get()
        except NotImplementedError as e:
            raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(target.get())} does not yield values") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if v is NotImplemented:
            raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(target.get())} does not yield values")
        d[v[0]] = v[1]
    return script.wrap_python_value(d)


@f_is.overload(("value", [AnyType,NamePair]), ("type", Type))
def function_is(value:ScriptVariable, t:ScriptVariable[type]):
    return ScriptValue(Bool, value.type().issubtype(script.DATA_TYPE_TABLE[t.get().inner]))

@f_is.overload(("value", [AnyType,NamePair]), ("type", TypeAnnotation))
def function_is_annotation(value:ScriptVariable, t:ScriptVariable[ScriptTypeAnnotation]):
    return ScriptValue(Bool, value.get().isinstance(t.get().inner))

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
        raise exceptions.TRTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(Bool, name.get().inner in data)

@f_has.overload(("node", [JsonNode, JsonProxyRoot]), dict(name="names", dtypes=[String], pack=True))
def function_has_plural(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], *names:ScriptVariable[str]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TRTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(List, [name.get().inner in data for name in names])

@f_has.overload(("node", [JsonNode, JsonProxyRoot]), ("names", List))
def function_has_plural(node:ScriptVariable[json_proxy.JsonProxyNode|json_proxy.JsonProxyRoot], names:ScriptVariable[list]):
    if isinstance(node, json_proxy.JsonProxyRoot):
        data, _ = node.get().inner.get_data()
    else:
        data = node.get().inner.resolve()
    if not isinstance(data, dict):
        raise exceptions.TRTypeError(f"expected node data to be of type {Map.name}, but got {DATA_TYPE_TABLE[type(data)].name}")
    return ScriptValue(List, [name in data for name in names])

@f_hasfunc.overload(("name", String), pass_ctx=True)
def function_hasfunc(ctx:ScriptContext, name:ScriptVariable[str]):
    return ScriptValue(Bool, name in ctx.script.function_table)

@f_print.overload(dict(name="x", dtypes=[AnyType], pack=True), ("sep", String, " "), ("end", String, "\n"))
def function_print(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    print(*(utils.script_repr(xi.get()) for xi in x), sep=sep.get().inner, end=end.get().inner)

@f_error.overload(dict(name="x", dtypes=[AnyType], pack=True), ("sep", String, " "), ("end", String, ""))
def function_error(*x:ScriptVariable, sep:ScriptVariable[str], end:ScriptVariable[str]):
    raise exceptions.TRUserException(f"{sep.get().inner.join((xv:=xi.get()).type.conv_str(xv).inner for xi in x)}{end.get().inner}")

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
    raise exceptions.TRTypeError(f"expected to write {repr(ext)} file using value of type: {",".join(t.name for t in types)}; got value {value.type().repr(value)} of type {value.type().name}")

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
        raise exceptions.TRTypeError("given list is read-only")
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
        index = t.index(v, istart, istop)
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
            raise exceptions.TRNotImplemented("'==' operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TRMustEvaluate(f"'==' operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TRNotImplemented("'==' operation is not implemented")
        
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

_ITERATOR_ITERATE_STOP_DEFAULT = sys.maxsize
@f_iterate_over.overload(("start", Iterator), ("stop", Integer, _ITERATOR_ITERATE_STOP_DEFAULT), ("step", Integer, 1))
def iterate_over_iterator(start:ScriptVariable[_iterator], stop:ScriptVariable[int], step:ScriptVariable[int]):
    v = start.get().inner
    s = step.get().inner
    return script.wrap_python_value(_iterator_iterator(-s, v, stop.get().inner, s))
    

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
        raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented")
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
        raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TRNotImplemented(f"next() for {utils.script_repr(iterator.get())} is not implemented")
    elif n is None:
        return false
    try:
        v = await n.get()
    except NotImplementedError as e:
        raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(iterator.get())} does not yield values") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if v is NotImplemented:
        raise exceptions.TRNotImplemented(f"iterator {utils.script_repr(iterator.get())} does not yield values")
    iterator.assign(script.wrap_python_value(n))
    out.assign(script.wrap_python_value(v))
    return true

@f_reset.overload(("target", Iterator))
async def iterator_reset(target:ScriptVariable[_iterator]):
    it = target.get()
    try:
        n = await it.inner.reset()
    except NotImplementedError as e:
        raise exceptions.TRNotImplemented(f"reset() for {utils.script_repr(it)} is not implemented") from e
    except Exception as e:
        raise exceptions.wrap(e)
    if n is NotImplemented:
        raise exceptions.TRNotImplemented(f"reset() for {utils.script_repr(it)} is not implemented")
    elif n is None:
        return false
    n = script.wrap_python_value()
    target.assign(n)
    return n

@f_delete.overload(("name", String), pass_ctx=True)
def delete_name(ctx:ScriptContext, name:ScriptVariable[str]):
    n = name.get().inner
    v = ctx.stack.pop_name(n)
    if v is None:
        raise exceptions.TRMissingName(f"Could not find name to delete: {repr(n)}", n)
    return v

@f_delete.overload(("value", [AnyType, NamePair]), ("key_or_index", [AnyType, NamePair]))
def delete_item(value:ScriptVariable, key_or_index:ScriptVariable):
    x = value.get()
    return x.type.delitem(x, key_or_index)

@f_delete_attribute.overload(("value", [AnyType, NamePair]), ("name", String))
def delete_attribute(value:ScriptVariable, name:ScriptVariable[str]):
    x = value.get()
    return x.type.delattr(x, name.get().inner)

@f_now.overload()
def function_now():
    return script.wrap_python_value(datetime.now())

@f_round.overload((""))
def function_round():
    ...

@f_format.overload((""))
def function_format():
    ...

def activate():
    global Trait, List_Of, Map_Of, Pair_Of, Iterator_Of, Not_Type, All_Types, Any_Types, Whole_Number
    if not mimetypes.inited:
        mimetypes.init()
    script.DATA_TYPE_TABLE[type] = Type
    script.DATA_TYPE_TABLE[NullType.inner] = NullType.init()
    script.DATA_TYPE_TABLE[List_readonly.inner] = List_readonly.init()
    script.DATA_TYPE_TABLE[Map_readonly.inner] = Map_readonly.init()
    utils.DATA_TYPE_TABLE[MapItem.inner] = MapItem.init()
    utils.add_type(ColorComponent, constructor=False)
    utils.add_type(ColorComponentRGBA, constructor=False)
    utils.add_type(ColorComponentCMYK, constructor=False)
    utils.add_type(Iterator, constructor=False)
    utils.add_type(RangeIterator, constructor=False)
    utils.add_type(IterableIterator, constructor=False)
    utils.add_type(IteratorIterator, constructor=False)
    utils.add_type(CollectionIterator, constructor=False)
    utils.add_type(SequenceIterator, constructor=False)
    utils.add_type(Duration, constructor=False)
    utils.add_type(ComplexDuration, constructor=False)
    for dt in _builtin_types:
        utils.add_type(dt)
    utils.add_type(JsonProxyRoot, constructor=False)
    utils.add_type(JsonNode, constructor=False)
    Trait = utils.add_python_type(utils.ScriptTrait, override_names=utils.ScriptTrait.ANNOTATION_NAME)
    List_Of = utils.add_python_type(ListOf, override_names=ListOf.ANNOTATION_NAME)
    Map_Of = utils.add_python_type(MapOf, override_names=MapOf.ANNOTATION_NAME)
    Pair_Of = utils.add_python_type(PairOf, override_names=PairOf.ANNOTATION_NAME)
    Iterator_Of = utils.add_python_type(IteratorOf, override_names=IteratorOf.ANNOTATION_NAME)
    Not_Type = utils.add_python_type(NotType, override_names=NotType.ANNOTATION_NAME)
    All_Types = utils.add_python_type(AllTypes, override_names=AllTypes.ANNOTATION_NAME)
    Any_Types = utils.add_python_type(AnyTypes, override_names=AnyTypes.ANNOTATION_NAME)
    Whole_Number = utils.add_python_type(WholeNumber, override_names=WholeNumber.ANNOTATION_NAME)

    add_read_behavior("application/json", _read_file_json)
    add_write_behavior("application/json", _write_file_json)

    utils.merge_function("list_from", f_list_from)
    utils.merge_function("map_from", f_map_from)
    utils.merge_function("is", f_is)
    utils.merge_function("issubtype", f_issubtype)
    utils.merge_function("has", f_has)
    utils.merge_function("hasfunc", f_hasfunc)
    utils.merge_function("print", f_print)
    utils.merge_function("error", f_error)
    utils.merge_function("flush", f_flush)
    utils.merge_function("wait", f_wait)
    utils.merge_function("format_json", f_format_json)
    utils.merge_function("parse_json", f_parse_json)
    utils.merge_function("read", f_read)
    utils.merge_function("write", f_write)
    trait_Appendable.merge_function(f_append)
    trait_CanFind.merge_function(f_find)
    trait_Container.merge_function(f_contains)
    trait_Iterable.merge_function(f_iterate_over)
    utils.merge_function("iterate_over_range", f_iterate_over_range)
    utils.merge_function("get", f_get)
    utils.merge_function("next", f_next)
    utils.merge_function("reset", f_reset)
    trait_CanDelete.merge_function(f_delete)
    utils.merge_function("delete_attribute", f_delete_attribute)
    utils.merge_function("now", f_now)
    trait_Roundable.merge_function(f_round)
    trait_Formattable.merge_function(f_format)

    utils.add_global("Appendable", trait_Appendable)
    utils.add_global("Container", trait_Container)
    utils.add_global("Iterable", trait_Iterable)
    utils.add_global("CanFind", trait_CanFind)
    utils.add_global("CanDelete", trait_CanDelete)
    utils.add_global("Roundable", trait_Roundable)
    utils.add_global("Formattable", trait_Formattable)

def deactivate():
    utils.remove_type(NullType)
    utils.remove_type(List_readonly)
    utils.remove_type(Map_readonly)
    utils.remove_type(MapItem)
    utils.remove_type(Iterator)
    utils.remove_type(RangeIterator)
    utils.remove_type(IterableIterator)
    utils.remove_type(IteratorIterator)
    utils.remove_type(CollectionIterator)
    utils.remove_type(SequenceIterator)
    utils.remove_type(Duration)
    utils.remove_type(ComplexDuration)
    for dt in _builtin_types:
        utils.remove_type(dt)
    utils.remove_type(JsonProxyRoot)
    utils.remove_type(JsonNode)
    utils.remove_type(List_Of)
    utils.remove_type(Map_Of)
    utils.remove_type(Iterator_Of)
    utils.remove_type(Not_Type)
    utils.remove_type(All_Types)
    utils.remove_type(Any_Types)

    remove_read_behavior("application/json", _read_file_json)
    remove_write_behavior("application/json", _write_file_json)

    utils.remove_function("list_from", f_list_from)
    utils.remove_function("map_from", f_map_from)
    utils.remove_function("isinstance", f_is)
    utils.remove_function("issubtype", f_issubtype)
    utils.remove_function("has", f_has)
    utils.remove_function("hasfunc", f_hasfunc)
    utils.remove_function("print", f_print)
    utils.remove_function("error", f_error)
    utils.remove_function("flush", f_flush)
    utils.remove_function("wait", f_wait)
    utils.remove_function("format_json", f_format_json)
    utils.remove_function("parse_json", f_parse_json)
    utils.remove_function("read", f_read)
    utils.remove_function("write", f_write)
    trait_Appendable.remove_function(f_append)
    trait_CanFind.remove_function(f_find)
    trait_Container.remove_function(f_contains)
    trait_Iterable.remove_function(f_iterate_over)
    utils.remove_function("iterate_over_range", f_iterate_over_range)
    utils.remove_function("get", f_get)
    utils.remove_function("next", f_next)
    utils.remove_function("reset", f_reset)
    trait_CanDelete.remove_function(f_delete)
    utils.remove_function("delete_attribute", f_delete_attribute)
    utils.remove_function("now", f_now)
    trait_Roundable.remove_function(f_round)
    trait_Formattable.remove_function(f_format)

    utils.remove_global("Appendable", trait_Appendable)
    utils.remove_global("Container", trait_Container)
    utils.remove_global("Iterable", trait_Iterable)
    utils.remove_global("CanFind", trait_CanFind)
    utils.remove_global("CanDelete", trait_CanDelete)
    utils.remove_global("Roundable", trait_Roundable)
    utils.remove_global("Formattable", trait_Formattable)
