from .exceptions import *
from .script import *
from . import script
import asyncio
from typing import Iterable

from typing import Any, Callable

def script_repr(v:ScriptValue)->str:
    return v.type.repr(v).inner

def generate_exception_help(raw:str, e:TronixException)->str:
    s = []
    if isinstance(e, TParsingException):
        ...
    elif isinstance(e, TCompilationException):
        ...
    elif isinstance(e, TRuntimeException):
        ...
    return "".join(s)

def add_type(dt:ScriptDataType, constructor:bool=True, init:bool=True):
    if init:
        dt.init()
    script.DATA_TYPE_TABLE[dt.inner] = dt
    if constructor:
        script.SCRIPT_FUNCTION_TABLE[dt.name] = dt.construct
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(dt, dt.inner))

def remove_type(dt:ScriptDataType):
    if dt is None:
        return
    if script.DATA_TYPE_TABLE.get(dt.inner,None) is dt:
        del script.DATA_TYPE_TABLE[dt.inner]
    if script.SCRIPT_FUNCTION_TABLE.get(dt.name,None) is dt.construct:
        del script.SCRIPT_FUNCTION_TABLE[dt.name]
    var = script.SCRIPT_GLOBAL_SCOPE.get(dt.name,None)
    if var is not None and var.get().inner is dt.inner:
        del script.SCRIPT_GLOBAL_SCOPE[dt.name]

class ScriptRunner:
    def __init__(self):
        self.parse_trees:dict[bytes, ParsingNode] = {}
        self.script_end_cbs:list[Callable[[Script],Any]] = []

    def _prep(self, s:Script|str, force_parse:bool, force_compile:bool):
        if isinstance(s, str):
            s = Script(s)
        if force_parse:
            p = self.parse_trees[s._hash] = s.parse()
        else:
            p = self.parse_trees.get(s._hash, None)
            if p is None:
                p = self.parse_trees[s._hash] = s.parse()
                s.compile(p)

        if force_compile or not s.steps:
            s.compile(p)
        
        return s

    async def run_async(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        s = self._prep(s, force_parse, force_compile)

        async def _next(steps:Iterable[Callable[[], Awaitable]]):
            for step in steps:
                x = await step()
                if isinstance(x, script._step_expansion):
                    if x.new_ns_stackframe:
                        s.stack = script.ns_stack({}, s.stack)
                    await _next(x.steps)
                    if x.new_ns_stackframe:
                        s.stack = s.stack.prev

        await _next(s.steps)

    def run(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        asyncio.run(self.run_async(s, force_parse, force_compile))

    def add_script_end_cb(self, f:Callable[[Script],Any]):
        self.script_end_cbs.append(f)
        return f
    
    def remove_script_end_cb(self, f:Callable[[Script],Any]):
        self.script_end_cbs.remove(f)

AttributeGetter = Callable[[ScriptValue, str], ScriptValue]
AttributeSetter = Callable[[ScriptValue, str, ScriptVariable], ScriptValue]
AttributeDeleter = Callable[[ScriptValue, str], ScriptValue]
AttributeItemGetter = Callable[[ScriptValue, ScriptVariable], ScriptValue]
AttributeItemSetter = Callable[[ScriptValue, ScriptVariable, ScriptVariable], ScriptValue]
AttributeItemDeleter = Callable[[ScriptValue, ScriptVariable], ScriptValue]

class ScriptAttributeNoAccess[T, K, U]:
    def __init__(self, message:str|Callable[[ScriptValue[T], str|ScriptVariable[K], ScriptVariable[U]|None], str], error:type[Exception]=AttributeError):
        self.message = message
        self.error = error

    def __call__(self, object:ScriptValue[T], name:str|ScriptVariable[K], value:ScriptVariable[U]|None=None):
        if isinstance(self.message, str):
            m = self.message
        else:
            m = self.message(object, name, value)
        raise self.error(m)

def __error_repr_attr_key(n:str|ScriptVariable):
    return script_repr(n.get()) if isinstance(n, script.ScriptVariable) else repr(n)

_DEFAULT_READONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only get {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)
_DEFAULT_WRITEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only assign to {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)
_DEFAULT_DELETEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only delete {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)
_DEFAULT_READ_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not get {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)
_DEFAULT_WRITE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not assign {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)
_DEFAULT_DELETE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not delete {__error_repr_attr_key(n)} attribute from {o.type.name} object", error=TypeError)

_DEFAULT_ITEM_READONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only get {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_WRITEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only assign to {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_DELETEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can only delete {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_READ_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not get {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_WRITE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not assign {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_DELETE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"can not delete {__error_repr_attr_key(n)} item from {o.type.name} object", error=TypeError)

_DEFAULT_ITEM_NOT_SUBSCRIPTABLE = ScriptAttributeNoAccess(lambda o, n, v: f"object of type {o.type.name} is not subscriptable (you can't do value[...])", error=exceptions.TNotImplemented)
_DEFAULT_WRITE_WRONG_TYPE = ScriptAttributeNoAccess(lambda o, n, v: f"can not assign value of type {v.type().name} to {__error_repr_attr_key(n)} {"item" if isinstance(n, script.ScriptVariable) else "attribute"} from {o.type.name} object", error=exceptions.TTypeError)

def SimpleGetAttribute(name:str|None=None)->AttributeGetter:
    def f(o:ScriptValue, n:str):
        return script.wrap_python_value(getattr(o.inner, name or n))
    return f
def MethodGetAttribute(name:str|None=None, args:tuple=(), kwargs:dict[str]={})->AttributeGetter:
    def f(o:ScriptValue, n:str):
        return script.wrap_python_value(getattr(o.inner, name or n)(*args, **kwargs))
    return f
def SimpleSetAttribute(name:str|None=None)->AttributeSetter:
    def f(o:ScriptValue, n:str, v:ScriptVariable):
        x = v.get()
        setattr(o.inner, name or n, x.inner)
        return x
    return f
def SimpleDelAttribute(name:str=None, pop:bool=True)->AttributeDeleter:
    if pop:
        def f(o:ScriptValue, n):
            nn = name or n
            x = o.type.getattr(o, nn)
            delattr(o.inner, nn)
            return x
    else:
        def f(o:ScriptValue, n):
            delattr(o.inner, name or n)
    return f

__ITEM_SIMPLE_NO_OVERRIDE = object()

def SimpleGetItem(key:Any=__ITEM_SIMPLE_NO_OVERRIDE)->AttributeItemGetter:
    def f(o:ScriptValue, n:ScriptVariable):
        return script.wrap_python_value(o.inner[n.get().inner if key is __ITEM_SIMPLE_NO_OVERRIDE else key])
    return f
def SimpleSetItem(key:Any=__ITEM_SIMPLE_NO_OVERRIDE)->AttributeItemSetter:
    def f(o:ScriptValue, n:ScriptVariable, v:ScriptVariable):
        x = v.get()
        o.inner[n.get().inner if key is __ITEM_SIMPLE_NO_OVERRIDE else key] = x.inner
        return x
    return f
def SimpleDelItem(key:Any=__ITEM_SIMPLE_NO_OVERRIDE, pop:bool=True)->AttributeItemDeleter:
    if pop:
        kvar = None if key is __ITEM_SIMPLE_NO_OVERRIDE else script.ScriptVariable(script.wrap_python_value(key))
        def f(o:ScriptValue, n:ScriptVariable):
            v = kvar or n
            x = o.type.getitem(o, v)
            del o.inner[v.get().inner]
            return x
    else:
        def f(o:ScriptValue, n:ScriptVariable):
            del o.inner[n.get().inner if key is __ITEM_SIMPLE_NO_OVERRIDE else key]
    return f
def SimpleGetAttributeAsItem(name:str|None=None)->AttributeItemGetter:
    def f(o:ScriptValue, n:ScriptVariable):
        return script.wrap_python_value(getattr(o.inner, name or n.get().inner))
    return f
def SimpleSetAttributeAsItem(name:str|None=None)->AttributeItemSetter:
    def f(o:ScriptValue, n:ScriptVariable, v:ScriptVariable):
        x = v.get()
        setattr(o.inner, name or n.get().inner, x.inner)
        return x
    return f
def SimpleDelAttributeAsItem(name:str|None=None, pop:bool=True)->AttributeItemDeleter:
    if pop:
        def f(o:ScriptValue, n:ScriptVariable):
            nn = name or n.get().inner
            x = o.type.getattr(o, nn)
            delattr(o.inner, nn)
            return x
    else:
        def f(o:ScriptValue, n:ScriptVariable):
            delattr(o.inner, name or n.get().inner)
    return f

def TypedSetter(ts:type|ScriptDataType|list[type|ScriptDataType], f:AttributeSetter|AttributeItemSetter|None=None, no_access:ScriptAttributeNoAccess|None=None):
    if no_access is None:
        no_access = _DEFAULT_WRITE_WRONG_TYPE

    def decor(ff:AttributeSetter|AttributeItemSetter):
        def typecheck_wrapper(o:ScriptValue, n:str|ScriptVariable, v:ScriptVariable):
            if isinstance(ts, (type, script.ScriptDataType)):
                tlist = [script.wrap_python_type(ts)]
            else:
                tlist = [script.wrap_python_type(t) for t in ts]
            x = v.get()
            if x.type.issubtype(*tlist):
                return ff(o, n, v)
            else:
                return no_access(o, n, v)
        return typecheck_wrapper

    if f is None:
        return decor
    else:
        return decor(f)


class ScriptValueAttribute[T, K, U]:
    def __init__(self, key:K,
                 get:Callable[[ScriptValue[T], str], ScriptValue[U]]|None=None,
                 set:Callable[[ScriptValue[T], str, ScriptVariable[U]], ScriptValue]|None=None,
                 delete:Callable[[ScriptValue[T], str], ScriptValue[U]]|None=None,
                 getitem:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]|None=None,
                 setitem:Callable[[ScriptValue[T], ScriptVariable[K], ScriptVariable[U]], ScriptValue]|None=None,
                 delitem:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]|None=None):
        self.key = key
        self._get = get
        self._set = set
        self._del = delete
        self._getitem = getitem
        self._setitem = setitem
        self._delitem = delitem

    def readonly(self, f:Callable[[ScriptValue[T], str], ScriptValue[U]], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_READONLY_NO_ACCESS
        return self.getter(f).setter(no_access).deleter(no_access)
    
    def writeonly(self, f:Callable[[ScriptValue[T], str, ScriptVariable[U]], ScriptValue], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_WRITEONLY_NO_ACCESS
        return self.getter(no_access).setter(f).deleter(no_access)
    
    def deleteonly(self, f:Callable[[ScriptValue[T], str], ScriptValue[U]], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_DELETEONLY_NO_ACCESS
        return self.getter(no_access).setter(no_access).deleter(f)
    
    def noget(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.getter(_DEFAULT_READ_NO_ACCESS if no_access is None else no_access)
    
    def noset(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.getter(_DEFAULT_WRITE_NO_ACCESS if no_access is None else no_access)
    
    def nodel(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.getter(_DEFAULT_DELETE_NO_ACCESS if no_access is None else no_access)

    def getter(self, f:Callable[[ScriptValue[T], str], ScriptValue[U]]):
        self._get = f
        return self
    
    def setter(self, f:Callable[[ScriptValue[T], str, ScriptVariable[U]], ScriptValue]):
        self._set = f
        return self
    
    def deleter(self, f:Callable[[ScriptValue[T], str], ScriptValue[U]]):
        self._del = f
        return self
    
    def itemreadonly(self, f:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_ITEM_READONLY_NO_ACCESS
        return self.itemgetter(f).itemsetter(no_access).itemdeleter(no_access)
    
    def itemwriteonly(self, f:Callable[[ScriptValue[T], ScriptVariable[K], ScriptVariable[U]], ScriptValue], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_ITEM_WRITEONLY_NO_ACCESS
        return self.itemgetter(no_access).itemsetter(f).itemdeleter(no_access)
    
    def itemdeleteonly(self, f:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue], no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        if no_access is None:
            no_access = _DEFAULT_ITEM_DELETEONLY_NO_ACCESS
        return self.itemgetter(no_access).itemsetter(no_access).itemdeleter(f)
    
    def itemnoget(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.itemgetter(_DEFAULT_ITEM_READ_NO_ACCESS if no_access is None else no_access)
    
    def itemnoset(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.itemsetter(_DEFAULT_ITEM_WRITE_NO_ACCESS if no_access is None else no_access)
    
    def itemnodel(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.itemdeleter(_DEFAULT_ITEM_DELETE_NO_ACCESS if no_access is None else no_access)

    def itemgetter(self, f:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]):
        self._getitem = f
        return self
    
    def itemsetter(self, f:Callable[[ScriptValue[T], ScriptVariable[K], ScriptVariable[U]], ScriptValue]):
        self._setitem = f
        return self
    
    def itemdeleter(self, f:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]):
        self._delitem = f
        return self
    
    def reverse_attach(self, dt:script.ScriptDataType|type[script.ScriptDataType]):
        self._get:Callable[[ScriptValue[T], str], ScriptValue[U]]|None                                      = getattr(dt, "getattr", None)
        self._set:Callable[[ScriptValue[T], str, ScriptVariable[U]], ScriptValue]|None                      = getattr(dt, "setattr", None)
        self._del:Callable[[ScriptValue[T], str], ScriptValue[U]]|None                                      = getattr(dt, "delattr", None)
        self._getitem:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]|None                       = getattr(dt, "getitem", None)
        self._setitem:Callable[[ScriptValue[T], ScriptVariable[K], ScriptVariable[U]], ScriptValue]|None    = getattr(dt, "setitem", None)
        self._delitem:Callable[[ScriptValue[T], ScriptVariable[K]], ScriptValue]|None                       = getattr(dt, "delitem", None)
        return self



ATTR_ATTACH_ALL = "getattr", "setattr", "delattr", "getitem", "setitem", "delitem"
ATTR_ATTACH_ATTRS = "getattr", "setattr", "delattr"
ATTR_ATTACH_ITEMS = "getitem", "setitem", "delitem"

class ScriptAttributeHandler[T,K]:
    def __init__(self, parent:"ScriptAttributeHandler|None"=None, wildcard:ScriptValueAttribute[T,K,Any]|None=None, no_subscripting:bool=False):
        self.parent = parent
        self.no_subscripting = no_subscripting
        if no_subscripting:
            if not wildcard:
                wildcard = ScriptValueAttribute("")
            wildcard = wildcard.itemgetter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE).itemsetter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE).itemdeleter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE)
        self.wildcard = wildcard
        self.attributes:dict[str|K, ScriptValueAttribute[T,K,Any]] = {}
    
    def __getitem__(self, key:K):
        return self.attributes[key]

    def entry[U](self, key:str|K, *aliases:str, vt:type[U]=Any):
        if key in self.attributes:
            raise KeyError(f"{repr(key)} already in attribute handler")
        attr = self.attributes[key] = ScriptValueAttribute[T,K,U](key)
        if self.no_subscripting:
            attr = attr.itemgetter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE).itemsetter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE).itemdeleter(_DEFAULT_ITEM_NOT_SUBSCRIPTABLE)
        return self.alias(attr, *aliases)

    def alias[U](self, attr:ScriptValueAttribute[T,K,U], *aliases:K):
        for alias in aliases:
            self.attributes[alias] = attr
        return attr

    def func_get(self):
        def getattr(_, object:ScriptValue[T], name:str):
            p = self
            while p is not None:
                attr = self.attributes.get(name, self.wildcard)
                if not (attr is None or attr._get is None):
                    return attr._get(object, name)
                p = self.parent
            raise AttributeError(repr(name))
        return getattr
    
    def func_getitem(self):
        def getitem(_, object:ScriptValue[T], key:ScriptVariable[K]):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = self.attributes.get(keyx, None)
                if not (attr is None or attr._getitem is None):
                    return attr._getitem(object, key)
                p = self.parent
            raise LookupError(key.type().repr(key.get()).inner)
        return getitem

    def func_set(self):
        def setattr(_, object:ScriptValue[T], name:str, value:ScriptVariable):
            p = self
            while p is not None:
                attr = self.attributes.get(name, self.wildcard)
                if attr is not None:
                    if attr._set is not None:
                        return attr._set(object, name, value)
                p = self.parent
            raise AttributeError(repr(name))
        return setattr
    
    def func_setitem(self):
        def setitem(_, object:ScriptValue[T], key:ScriptVariable[K], value:ScriptVariable):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = self.attributes.get(keyx, None)
                if not (attr is None or attr._setitem is None):
                    return attr._setitem(object, key, value)
                p = self.parent
            raise LookupError(key.type().repr(key.get()).inner)
        return setitem
    
    def func_del(self):
        def delattr(_, object:ScriptValue[T], name:str):
            p = self
            while p is not None:
                attr = self.attributes.get(name, self.wildcard)
                if attr is not None:
                    if attr._del is not None:
                        return attr._del(object, name)
                p = self.parent
            raise AttributeError(repr(name))
        return delattr
    
    def func_delitem(self):
        def getitem(_, object:ScriptValue[T], key:ScriptVariable[K]):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = self.attributes.get(keyx, None)
                if not (attr is None or attr._delitem is None):
                    return attr._delitem(object, key)
                p = self.parent
            raise LookupError(key.type().repr(key.get()).inner)
        return getitem
    
    def make_funcs(self):
        return self.func_get(), self.func_set(), self.func_del(), self.func_getitem(), self.func_setitem(), self.func_delitem()
    
    def attach(self, dt):
        dt.getattr, dt.setattr, dt.delattr, dt.getitem, dt.setitem, dt.delitem = self.make_funcs()
        return dt
    
    def attach_some(self, *names:str):
        funcs = dict(zip(ATTR_ATTACH_ALL, self.make_funcs()))
        def decor(dt):
            for name in names:
                func = funcs.get(name,None)
                if func is not None:
                    setattr(dt, name, func)
            return dt
        return decor
    
    def _enforce(self, sdt:ScriptDataType, attach_names:tuple[str]):
        t = type(sdt)
        attrs = getattr(t, "attrs", None)
        if not isinstance(attrs, ScriptAttributeHandler) or attrs is self:
            attrs = ScriptAttributeHandler(self)
            setattr(t, "attrs", attrs)
            if attach_names:
                attrs.attach_some(*attach_names)(t)

    def enforce_child_attrs(self, *names:str, skip_child_attach:bool=False):
        def decor(dt):
            nonlocal names
            if skip_child_attach:
                names = ()
            elif not names:
                names = ATTR_ATTACH_ALL
            
            base_init_subtype = getattr(dt, "init_subtype", None)

            if callable(base_init_subtype):
                def enforcement_init_wrapper(s, subtype:ScriptDataType):
                    self._enforce(subtype, names)
                    return base_init_subtype(s, subtype)
                setattr(dt, "init_subtype", enforcement_init_wrapper)
            else:
                def enforcement_init(_, subtype:ScriptDataType):
                    self._enforce(subtype, names)
                setattr(dt, "init_subtype", enforcement_init)

            return dt
        return decor

_PARAM_NO_DEFAULT = object()

class ScriptFunctionParam:
    def __init__(self, name:str, dtypes:list[ScriptDataType|str], default=_PARAM_NO_DEFAULT, pack:bool=False):
        self.name = name
        self.types = dtypes
        self.default = default
        self.pack = pack

    def resolve_types(self):
        for t in self.types:
            if isinstance(t, ScriptDataType):
                yield t
            else:
                tt = script.name_to_type(t)
                if tt is None:
                    raise exceptions.TMissingName(f"function signature: {repr(t)} not found")

    def __eq__(self, other):
        if isinstance(other, ScriptFunctionParam):
            if self.pack != other.pack or self.default != other.default or self.name != other.name:
                return False
            st = [t.name if isinstance(t, ScriptDataType) else t for t in self.types]
            ot = [t.name if isinstance(t, ScriptDataType) else t for t in other.types]
            return st == ot
        return super().__eq__(other)

class ScriptFunctionParamSet:
    def __init__(self, params:list[ScriptFunctionParam], pass_ctx:bool=False):
        self.params = params
        self.pass_ctx = pass_ctx

    def __eq__(self, other):
        if isinstance(other, ScriptFunctionParamSet):
            return self.pass_ctx == other.pass_ctx and self.params == other.params
        return super().__eq__(other)

    def check(self):
        got_required_end = False
        index = None
        for i, param in enumerate(self.params):
            if param.default is _PARAM_NO_DEFAULT and not param.pack: #is positional and not pack
                if got_required_end: #after default args
                    raise exceptions.TInvalidParameterOrder("cannot have positional parameter after parameter with a default value")
            elif not got_required_end:
                got_required_end = True
                index = i
            elif param.pack:
                raise exceptions.TInvalidParameterOrder("cannot have multiple pack params or a pack parameter after a parameter with a default value")
        return len(self.params) if index is None else index

class ScriptFunctionSignature:
    def __init__(self, overloads:list[ScriptFunctionParamSet]):
        self.overloads = overloads

    def fit(self, args:list[ScriptVariable])->tuple[int, list[ScriptVariable], dict[str, ScriptVariable]]|tuple[None,None,None]:
        pair = DATA_TYPE_TABLE[ScriptNameValuePair]
        for i, overload in enumerate(self.overloads):
            l = overload.check()-1
            if len(args) < l:
                continue
            pi = 0
            ai = 0
            all_args_match = True
            rtv_args = []
            rtv_kwargs = {}

            once = True
            while ai < len(args) and pi < len(overload.params):
                p = overload.params[pi]
                resolvedts = list(p.resolve_types())
                takespair = pair in resolvedts
                while (p.pack or once) and ai < len(args):
                    if once:
                        once = False

                    _p = p
                    ts = resolvedts

                    arg = args[ai]
                    v = arg.get()
                    if v.type is pair and not takespair:
                        k:str = v.inner.name
                        for _p in overload.params:
                            if _p.name == k:
                                break
                        else:
                            raise exceptions.TUnknownParameter(f"unknown parameter with given keyword argument name: {repr(k)}")
                        if _p.pack:
                            raise exceptions.TInvalidParameterOrder(f"cannot keyword assign to pack parameter ({repr(k)})")
                        ts = list(_p.resolve_types())
                        v = wrap_python_value(v.inner.value)
                    else:
                        k = None
                    if not v.type.issubtype(*ts):
                        if not _p.pack:
                            all_args_match = False
                        break
                    ai += 1

                    if k is None: #positional
                        rtv_args.append(arg)
                    else: #keyword
                        rtv_kwargs[k] = ScriptVariable(v)
                if not all_args_match:
                    break
                pi += 1
                if not once:
                    once = True
            if pi == len(overload.params) and ai < len(args):
                continue #too many arguments
            if all_args_match:
                for j in range(pi, len(overload.params)):
                    p = overload.params[j]
                    if p.pack:
                        continue
                    if p.default is not _PARAM_NO_DEFAULT:
                        rtv_kwargs.setdefault(p.name, ScriptVariable(wrap_python_value(p.default)))
                return i, rtv_args, rtv_kwargs
        return None, None, None

ScriptFunctionParam_Like = ScriptFunctionParam|str|tuple[str]|tuple[str, str|ScriptDataType|type|list[str|ScriptDataType|type]]|dict[str]

class ScriptFunction[T]:

    def __init__(self):
        self.signature = ScriptFunctionSignature([])
        self.cbs:list[Callable[..., ScriptValue]] = []

    def __get__(self, instance, owner)->"BoundScriptFunction[T]":
        b = BoundScriptFunction.__new__(BoundScriptFunction)
        b.__dict__.update(self.__dict__)
        b.instance = instance
        return b

    def add_overload(self, params:ScriptFunctionParamSet, cb:Callable[..., ScriptValue]):
        params.check()
        for existing in self.signature.overloads:
            if existing == params:
                raise exceptions.DuplicateOverloadException("overload already exists in this function")
        self.signature.overloads.append(params)
        self.cbs.append(cb)

    def overload(self, *params:ScriptFunctionParam_Like, auto:bool=False, pass_ctx:bool=False):
        def decor(cb:Callable[..., ScriptValue]):
            if auto and not params:
                ... #TODO inspect function and determine types from annotations
            else:
                plist = []
                AnyType = script.DATA_TYPE_TABLE[object]
                for p in params:
                    if isinstance(p, str):
                        p = ScriptFunctionParam(p, [AnyType])
                    elif isinstance(p, tuple):
                        if len(p) < 1:
                            raise ValueError(f"cannot construct script function parameter from data: {p}")
                        elif len(p) > 1:
                            tp = p[1]
                            if isinstance(tp, type):
                                tp = script.DATA_TYPE_TABLE[tp]
                            if isinstance(tp, (str, ScriptDataType)):
                                p = (p[0], [tp], *p[2:])
                            elif isinstance(tp, list):
                                tl = []
                                for v in tp:
                                    if isinstance(v, type):
                                        v = script.DATA_TYPE_TABLE[v]
                                    elif not isinstance(v, (str, ScriptDataType)):
                                        raise TypeError(f"script function parameter type union must be made of str, ScriptDataType, or type, got: {type(v).__name__} {v}")
                                    tl.append(v)
                                p = (p[0], tl, *p[2:])
                            p = ScriptFunctionParam(*p)
                        else:
                            p = ScriptFunctionParam(p[0], [AnyType])
                    elif isinstance(p, dict):
                        p = ScriptFunctionParam(**p)
                    elif not isinstance(p, ScriptFunctionParam):
                        raise ValueError(f"cannot construct script function parameter from value: {p}")
                    plist.append(p)  
                self.add_overload(ScriptFunctionParamSet(plist, pass_ctx=pass_ctx), cb)
            return cb
        return decor
    
    def _get_fit(self, ctx:ScriptContext):
        i, args, kwargs = self.signature.fit(ctx.params)
        if i is None:
            raise exceptions.TTypeError(f"function has no overloads that match the following arguments: {", ".join(v.type().name for v in ctx.params)}")
        return self.cbs[i], i, args, kwargs

    def __call__(self, ctx:ScriptContext):
        cb, i, args, kwargs = self._get_fit(ctx)
        if self.signature.overloads[i].pass_ctx:
            return cb(ctx, *args, **kwargs)
        else:
            return cb(*args, **kwargs)
        
class BoundScriptFunction[T](ScriptFunction[T]):
    def __init__(self, instance:T):
        super().__init__()
        self.instance = instance

    def __call__(self, ctx:ScriptContext):
        cb, i, args, kwargs = self._get_fit(ctx)
        if self.signature.overloads[i].pass_ctx:
            return cb(self.instance, ctx, *args, **kwargs)
        else:
            return cb(self.instance, *args, **kwargs)
        
class _serialized_value:
    @classmethod
    def serialize(cls, value:ScriptValue, type_str:bool=False):
        return cls(value.type.inner, value.type.serialize(value, type_str=type_str), type_str=type_str)
    
    def __init__(self, t:type, v, type_str:bool=False):
        self.t = t
        self.v = v
        self.type_str = type_str

    def _deserialize(self):
        if isinstance(self.t, str):
            return script.name_to_type(self.t).deserialize(self.v)
        else:
            return script.wrap_python_type(self.t).deserialize(self.v)

    def deserialize(self)->ScriptValue:
        return script.wrap_python_value(self._deserialize())
    
    def __getstate__(self)->dict[str]:
        return {
            "t": script.wrap_python_type(self.t).name if self.type_str else self.t,
            "v": self.v,
        }
    
    def __setstate__(self, d:dict[str]):
        self.t = d["t"]
        self.v = d["v"]
        self.type_str = isinstance(self.t, str)


SerializedNamespace = dict[str, _serialized_value]

def serialize_namespace(space:Namespace)->SerializedNamespace:
    return {name:_serialized_value.serialize(var.get()) for name, var in space.items()}

def deserialize_namespace(space:SerializedNamespace)->Namespace:
    return {name:sval.deserialize() for name, sval in space.items()}


def serialize_value(value, type_str:bool=False):
    return _serialized_value.serialize(script.wrap_python_value(value), type_str=type_str).__getstate__()

def deserialize_value(value:dict[str]):
    ser = _serialized_value.__new__(_serialized_value)
    ser.__setstate__(value)
    return ser.deserialize()

def serialize_value_headless(value, type_str:bool=False):
    v = script.wrap_python_value(value)
    return v.type.serialize(v, type_str=type_str)