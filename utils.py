from .exceptions import *
from .script import *
from . import script
import asyncio
from typing import AsyncGenerator, AsyncIterable, Generator, Iterable
import xml.etree.ElementTree as ET
import xml.dom.minidom

from typing import Any, Callable

def script_repr(v:ScriptValue)->str:
    return v.type.repr(v).inner

def generate_exception_help(s:script.Script, e:TronixException, step:Callable[[], Any]|None=None)->str:
    help_text = e.help_text(s, step=step)
    if help_text is not None:
        return str(help_text)
    name = getattr(e, "__TNAME__", type(e).__name__)
    # if isinstance(e, TParsingException):
    #     ...
    # elif isinstance(e, TCompilationException):
    #     ...
    # elif isinstance(e, TRuntimeException):
    #     ...
    return f"{name}: {e}"

def add_type(dt:ScriptDataType, constructor:bool=True, init:bool=True):
    if init:
        dt.init()
    script.DATA_TYPE_TABLE[dt.inner] = dt
    if constructor:
        merge_function(dt.name, dt.construct)
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(dt, dt.inner))

def add_python_type(t:type, constructor:bool=True, init:bool=True, override_names:str|dict[str,str]|None=None):
    dt = script.wrap_python_type(t, override_names=override_names)
    if init:
        dt.init()
    if constructor:
        merge_function(dt.name, dt.construct)
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(dt, dt.inner))
    return dt

def remove_type(dt:ScriptDataType):
    if dt is None:
        return
    if script.DATA_TYPE_TABLE.get(dt.inner,None) is dt:
        del script.DATA_TYPE_TABLE[dt.inner]
    if script.SCRIPT_FUNCTION_TABLE.get(dt.name,None) is dt.construct:
        remove_function(dt.name, dt.construct)
    var = script.SCRIPT_GLOBAL_SCOPE.get(dt.name,None)
    if var is not None and var.get().inner is dt.inner:
        del script.SCRIPT_GLOBAL_SCOPE[dt.name]

def merge_function(name:str, f:Callable[[ScriptContext], Any]):
    current = script.SCRIPT_FUNCTION_TABLE.get(name, None)
    if current is None:
        script.SCRIPT_FUNCTION_TABLE[name] = f
        return f
    elif isinstance(current, ScriptFunction):
        if isinstance(f, ScriptFunction):
            for cb, overload in zip(f.cbs, f.signature.overloads):
                current.add_overload(overload, cb)
        else:
            current.overload(auto=True)(f)
        return current
    elif isinstance(f, ScriptFunction):
        f.overload(auto=True, priority=0)(current)
        script.SCRIPT_FUNCTION_TABLE[name] = f
        return f
    else:
        x = ScriptFunction()
        x.overload(auto=True)(current)
        x.overload(auto=True)(f)
        script.SCRIPT_FUNCTION_TABLE[name] = x
        return x

def remove_function(name:str, f:Callable[[ScriptContext], Any]|None=None):
    if f is None:
        return script.SCRIPT_FUNCTION_TABLE.pop(name, None)
    else:
        x = script.SCRIPT_FUNCTION_TABLE.get(name,None)
        if x is f:
            del script.SCRIPT_FUNCTION_TABLE[name]
        elif isinstance(x, ScriptFunction):
            if isinstance(f, ScriptFunction):
                i = 0
                while i < len(x.cbs):
                    cb = x.cbs[i]
                    j = 0
                    deleted = False
                    while j < len(f.cbs):
                        jcb = f.cbs[j]
                        if cb is jcb:
                            if not deleted:
                                deleted = True
                            del f.cbs[j]
                            del f.signature.overloads[j]
                        else:
                            j += 1
                    if deleted:
                        del x.cbs[i]
                        del x.signature.overloads[i]
                    else:
                        i += 1
            else:
                i = 0
                while i < len(x.cbs):
                    cb = x.cbs[i]
                    if cb is f:
                        del x.cbs[i]
                        del x.signature.overloads[i]
                    else:
                        i += 1
            if not x.cbs:
                del script.SCRIPT_FUNCTION_TABLE[name]
        elif isinstance(f, ScriptFunction):
            if len(f.cbs) == 1 and f.cbs[0] is x:
                del script.SCRIPT_FUNCTION_TABLE[name]
            else:
                return None
        else:
            return None
        return f

def add_global(name:str, value):
    g = script.SCRIPT_GLOBAL_SCOPE.get(name, None)
    v = script.wrap_python_value(value)
    if g is None:
        script.SCRIPT_GLOBAL_SCOPE[name] = script.ScriptVariable(v)
    else:
        g.assign(v)

def remove_global(name:str, value):
    g = script.SCRIPT_GLOBAL_SCOPE.get(name, None)
    if g is None:
        return
    if isinstance(value, script.ScriptValue):
        value = value.inner
    if g.get().inner == value:
        script.SCRIPT_GLOBAL_SCOPE.pop(name, None)

class ScriptRunner:
    def __init__(self):
        self.parse_trees:dict[bytes, ParsingNode] = {}
        self.script_start_cbs:list[Callable[[Script],Any]] = []
        self.script_end_cbs:list[Callable[[Script],Any]] = []
        self.script_step_cbs:list[Callable[[Script, Any],Any]] = []

    def cache(self, s:Script|bytes, p:ParsingNode):
        if isinstance(s, script.Script):
            s = s._hash
        self.parse_trees[s] = p
        return p

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

    async def _run_cbs(self, s:Script, cbs:list[Callable[[Script],Any]]):
        for cb in cbs:
            c = cb(s)
            if inspect.isawaitable(c):
                await c

    async def run_async(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        s = self._prep(s, force_parse, force_compile)
        control:script._step_control|None = None

        async def run_step(step:Callable[[], Awaitable], exception_control:bool):
            nonlocal control
            try:
                if exception_control:
                    try:
                        x = await step()
                    except Exception as e:
                        x = script._step_control(script._STEP_CONTROL_BREAK|script._STEP_CONTROL_EXCEPTION, exc=e)
                else:
                    x = await step()
                if isinstance(x, script._step_control):
                    control = x
                elif isinstance(x, script._step_expansion):
                    if x.new_ns_stackframe:
                        s.stack = script.ns_stack({}, s.stack)
                    await _next(x)
                    if x.new_ns_stackframe:
                        s.stack = s.stack.prev
                else:
                    results = [c for cb in self.script_step_cbs if inspect.isawaitable(c:=cb(s, x))]
                    if results:
                        await asyncio.gather(*results)
            except Exception as e:
                te = wrap(e)
                if te._ctx is None:
                    _step = step
                    while isinstance(_step, script._step_evaluation):
                        _step = _step.cb
                    node = s.steps_debug.get(_step, None)
                    if node is not None:
                        te._set_context(exceptions.ExceptionContext(node, _step))
                if te is e:
                    raise
                else:
                    raise te from e

        async def _next(steps:AsyncIterable[Callable[[], Awaitable]]|Iterable[Callable[[], Awaitable]]):
            nonlocal control
            try:
                stepiter = aiter(steps)
            except TypeError:
                stepiter = iter(steps)
            if isinstance(stepiter, AsyncGenerator):
                exc_ctrl = stepiter.handle_step_control if isinstance(stepiter, script._step_expansion) else True
                try:
                    control = None
                    while True:
                        step = await stepiter.asend(control)
                        control = None
                        await run_step(step, exc_ctrl)
                except StopAsyncIteration:
                    pass
            elif isinstance(stepiter, Generator):
                exc_ctrl = stepiter.handle_step_control if isinstance(stepiter, script._step_expansion) else True
                try:
                    control = None
                    while True:
                        step = stepiter.send(control, exc_ctrl)
                        control = None
                        await run_step(step, exc_ctrl)
                except StopIteration:
                    pass
            else:
                for step in stepiter:
                    await run_step(step, False)

        await self._run_cbs(s, self.script_start_cbs)
        await _next(s.steps)
        await self._run_cbs(s, self.script_end_cbs)

    def run(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        return asyncio.run(self.run_async(s, force_parse, force_compile))

    def add_script_start_cb(self, f:Callable[[Script],Any]):
        self.script_start_cbs.append(f)
        return f

    def add_script_end_cb(self, f:Callable[[Script],Any]):
        self.script_end_cbs.append(f)
        return f

    def add_script_step_cb(self, f:Callable[[Script, Any],Any]):
        self.script_step_cbs.append(f)
    
    def remove_script_start_cb(self, f:Callable[[Script],Any]):
        self.script_start_cbs.remove(f)

    def remove_script_end_cb(self, f:Callable[[Script],Any]):
        self.script_end_cbs.remove(f)

    def remove_script_step_cb(self, f:Callable[[Script, Any],Any]):
        self.script_step_cbs.remove(f)

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

_DEFAULT_READONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"attribute {__error_repr_attr_key(n)} from {o.type.name} object is get-only", error=TypeError)
_DEFAULT_WRITEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"attribute {__error_repr_attr_key(n)} from {o.type.name} object is assign-only", error=TypeError)
_DEFAULT_DELETEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"attribute {__error_repr_attr_key(n)} from {o.type.name} object is delete-only", error=TypeError)
_DEFAULT_READ_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot get attribute {__error_repr_attr_key(n)} from {o.type.name} object", error=TypeError)
_DEFAULT_WRITE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot assign attribute {__error_repr_attr_key(n)} from {o.type.name} object", error=TypeError)
_DEFAULT_DELETE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot delete attribute {__error_repr_attr_key(n)} from {o.type.name} object", error=TypeError)

_DEFAULT_ITEM_READONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"item at [{__error_repr_attr_key(n)}] from {o.type.name} object is get-only", error=TypeError)
_DEFAULT_ITEM_WRITEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"item at [{__error_repr_attr_key(n)}] from {o.type.name} object is assign-only", error=TypeError)
_DEFAULT_ITEM_DELETEONLY_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"item at [{__error_repr_attr_key(n)}] from {o.type.name} object is delete-only", error=TypeError)
_DEFAULT_ITEM_READ_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot get item at [{__error_repr_attr_key(n)}] from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_WRITE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot assign item at [{__error_repr_attr_key(n)}] from {o.type.name} object", error=TypeError)
_DEFAULT_ITEM_DELETE_NO_ACCESS = ScriptAttributeNoAccess(lambda o, n, v: f"cannot delete item at [{__error_repr_attr_key(n)}] from {o.type.name} object", error=TypeError)

_DEFAULT_ITEM_NOT_SUBSCRIPTABLE = ScriptAttributeNoAccess(lambda o, n, v: f"object of type {o.type.name} is not subscriptable", error=exceptions.TRNotImplemented)
_DEFAULT_WRITE_WRONG_TYPE = ScriptAttributeNoAccess(lambda o, n, v: f"cannot assign value of type {v.type().name} to {"item at" if isinstance(n, script.ScriptVariable) else "attribute"} {__error_repr_attr_key(n)} from {o.type.name} object", error=exceptions.TRTypeError)
_DEFAULT_DELETE_WRONG_TYPE = ScriptAttributeNoAccess(lambda o, n: f"cannot delete {f"item at value of type {n.type().name}" if isinstance(n, script.ScriptVariable) else "attribute"} from {o.type.name} object", error=exceptions.TRTypeError)

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

def TypedSetter(ts:type|ScriptDataType|ScriptTypeAnnotation|list[type|ScriptDataType|ScriptTypeAnnotation], f:AttributeSetter|AttributeItemSetter|None=None, no_access:ScriptAttributeNoAccess|None=None):
    if no_access is None:
        no_access = _DEFAULT_WRITE_WRONG_TYPE

    def decor(ff:AttributeSetter|AttributeItemSetter):
        def typecheck_wrapper(o:ScriptValue, n:str|ScriptVariable, v:ScriptVariable):
            if isinstance(ts, type):
                tlist = [script.wrap_python_type(ts)]
            elif isinstance(ts, (script.ScriptDataType, script.ScriptTypeAnnotation)):
                tlist = [ts]
            else:
                tlist = [t if isinstance(t, (script.ScriptDataType, script.ScriptTypeAnnotation)) else script.wrap_python_type(t) for t in ts]
            x = v.get()
            if x.isinstance(*tlist):
                return ff(o, n, v)
            else:
                return no_access(o, n, v)
        return typecheck_wrapper

    if f is None:
        return decor
    else:
        return decor(f)

def _TypedSolo[T](ts:type|ScriptDataType|ScriptTypeAnnotation|list[type|ScriptDataType|ScriptTypeAnnotation], f:T|None=None, no_access:ScriptAttributeNoAccess|None=None):
    if no_access is None:
        no_access = _DEFAULT_DELETE_WRONG_TYPE

    def decor(ff:T):
        def typecheck_wrapper(o:ScriptValue, n:str|ScriptVariable):
            if isinstance(ts, type):
                tlist = [script.wrap_python_type(ts)]
            elif isinstance(ts, (script.ScriptDataType, script.ScriptTypeAnnotation)):
                tlist = [ts]
            else:
                tlist = [t if isinstance(t, (script.ScriptDataType, script.ScriptTypeAnnotation)) else script.wrap_python_type(t) for t in ts]
            if isinstance(n, str):
                if script.ScriptValue(script.DATA_TYPE_TABLE[str], n).isinstance(*tlist):
                    return ff(o, n)
            elif n.get().isinstance(*tlist):
                return ff(o, n)
            return no_access(o, n)
        return typecheck_wrapper

    if f is None:
        return decor
    else:
        return decor(f)
    
TypedGetter:Callable[[type|ScriptDataType|ScriptTypeAnnotation|list[type|ScriptDataType|ScriptTypeAnnotation], AttributeGetter|AttributeItemGetter|None], Callable[[ScriptValue, ScriptVariable|str], Any]|Callable[[AttributeGetter|AttributeItemGetter|None], AttributeGetter|AttributeItemGetter]] = _TypedSolo
TypedDeleter:Callable[[type|ScriptDataType|ScriptTypeAnnotation|list[type|ScriptDataType|ScriptTypeAnnotation], AttributeDeleter|AttributeItemDeleter|None], Callable[[ScriptValue, ScriptVariable|str], Any]|Callable[[AttributeDeleter|AttributeItemDeleter|None], AttributeDeleter|AttributeItemDeleter]] = _TypedSolo


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
        return self.setter(_DEFAULT_WRITE_NO_ACCESS if no_access is None else no_access)
    
    def nodel(self, no_access:ScriptAttributeNoAccess[T,K,U]|None=None):
        return self.deleter(_DEFAULT_DELETE_NO_ACCESS if no_access is None else no_access)

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
                attr = p.attributes.get(name, p.wildcard)
                if not (attr is None or attr._get is None):
                    return attr._get(object, name)
                p = p.parent
            raise AttributeError(f"{object.type.name} object has no attribute {repr(name)}")
        return getattr
    
    def func_getitem(self):
        def getitem(_, object:ScriptValue[T], key:ScriptVariable[K]):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = p.attributes.get(keyx, p.wildcard)
                if not (attr is None or attr._getitem is None):
                    return attr._getitem(object, key)
                p = p.parent
            raise LookupError(key.type().repr(key.get()).inner)
        return getitem

    def func_set(self):
        def setattr(_, object:ScriptValue[T], name:str, value:ScriptVariable):
            p = self
            while p is not None:
                attr = p.attributes.get(name, p.wildcard)
                if attr is not None:
                    if attr._set is not None:
                        return attr._set(object, name, value)
                p = p.parent
            raise AttributeError(f"{object.type.name} object has no attribute {repr(name)}")
        return setattr
    
    def func_setitem(self):
        def setitem(_, object:ScriptValue[T], key:ScriptVariable[K], value:ScriptVariable):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = p.attributes.get(keyx, p.wildcard)
                if not (attr is None or attr._setitem is None):
                    return attr._setitem(object, key, value)
                p = p.parent
            raise LookupError(key.type().repr(key.get()).inner)
        return setitem
    
    def func_del(self):
        def delattr(_, object:ScriptValue[T], name:str):
            p = self
            while p is not None:
                attr = p.attributes.get(name, p.wildcard)
                if attr is not None:
                    if attr._del is not None:
                        return attr._del(object, name)
                p = p.parent
            raise AttributeError(f"{object.type.name} object has no attribute {repr(name)}")
        return delattr
    
    def func_delitem(self):
        def getitem(_, object:ScriptValue[T], key:ScriptVariable[K]):
            p = self
            keyx = key.get().inner
            while p is not None:
                attr = p.attributes.get(keyx, p.wildcard)
                if not (attr is None or attr._delitem is None):
                    return attr._delitem(object, key)
                p = p.parent
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
    def __init__(self, name:str, dtypes:list[ScriptDataType|ScriptTypeAnnotation|str], default=_PARAM_NO_DEFAULT, pack:bool=False):
        self.name = name
        self.types = dtypes
        self.default = default
        self.pack = pack

    def resolve_types(self):
        for t in self.types:
            if isinstance(t, (script.ScriptDataType, script.ScriptTypeAnnotation)):
                yield t
            else:
                tt = script.parse_script_type_annotation(t)
                if tt is None:
                    raise exceptions.TRMissingName(
                        f"function signature: type or annotation {repr(t)} not defined", t)
                yield tt

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
                    raise exceptions.TRInvalidParameterOrder("cannot have positional parameter after parameter with a default value")
            elif not got_required_end:
                got_required_end = True
                index = i
            elif param.pack:
                raise exceptions.TRInvalidParameterOrder("cannot have multiple pack params or a pack parameter after a parameter with a default value")
        return len(self.params) if index is None else index

class ScriptFunctionSignature:
    def __init__(self, overloads:list[ScriptFunctionParamSet]):
        self.overloads = overloads

    def fit(self, args:list[ScriptVariable])->tuple[int, list[ScriptVariable], dict[str, ScriptVariable]]|tuple[None,None,None]:
        npair = DATA_TYPE_TABLE[script.ScriptNameValuePair]
        for i, overload in enumerate(self.overloads):
            l = overload.check()-1
            if len(args) < l:
                continue
            pi = 0
            ai = 0
            all_args_match = True
            positional_parameters_encountered = 0
            rtv_args = []
            rtv_kwargs = {}

            once = True
            while ai < len(args) and pi < len(overload.params):
                p = overload.params[pi]
                resolvedts = list(p.resolve_types())
                takespair = npair in resolvedts
                while (p.pack or once) and ai < len(args):
                    if once:
                        once = False

                    _p = p
                    ts = resolvedts

                    arg = args[ai]
                    v = arg.get()
                    if v.type is npair and not takespair:
                        k:str = v.inner.name
                        for _p in overload.params:
                            if _p.name == k:
                                break
                        else:
                            if i == len(self.overloads)-1:
                                raise exceptions.TRUnknownParameter(f"unknown parameter with given keyword argument name: {repr(k)}")
                            else:
                                all_args_match = False
                        if _p.pack:
                            raise exceptions.TRInvalidParameterOrder(f"cannot keyword assign to pack parameter ({repr(k)})")
                        ts = list(_p.resolve_types())
                        v = wrap_python_value(v.inner.value)
                    else:
                        k = None
                    if not v.isinstance(*ts):
                        if _p.pack:
                            positional_parameters_encountered += 1
                        else:
                            all_args_match = False
                        break
                    ai += 1

                    if k is None: #positional
                        rtv_args.append(arg)
                        if not p.pack:
                            positional_parameters_encountered += 1
                    else: #keyword
                        rtv_kwargs[k] = ScriptVariable(v)
                if not all_args_match:
                    break
                pi += 1
                if not once:
                    once = True
            if pi >= len(overload.params) and ai < len(args):
                continue #too many arguments
            if all_args_match:
                for j in range(positional_parameters_encountered, len(overload.params)):
                    p = overload.params[j]
                    if p.pack:
                        continue
                    if p.default is not _PARAM_NO_DEFAULT:
                        rtv_kwargs.setdefault(p.name, ScriptVariable(wrap_python_value(p.default)))
                return i, rtv_args, rtv_kwargs
        return None, None, None

ScriptFunctionParam_Like = ScriptFunctionParam|str|tuple[str]|tuple[str, str|ScriptDataType|ScriptTypeAnnotation|type|list[str|ScriptDataType|ScriptTypeAnnotation|type]]|dict[str]

def _resolve_script_function_param_like(param:ScriptFunctionParam_Like, AnyType):
    if isinstance(param, str):
        param = ScriptFunctionParam(param, [AnyType])
    elif isinstance(param, tuple):
        if len(param) < 1:
            raise ValueError(f"cannot construct script function parameter from data: {param}")
        elif len(param) > 1:
            tp = param[1]
            if isinstance(tp, type):
                tp = script.DATA_TYPE_TABLE[tp]
            if isinstance(tp, (str, ScriptDataType, ScriptTypeAnnotation)):
                param = (param[0], [tp], *param[2:])
            elif isinstance(tp, list):
                tl = []
                for v in tp:
                    if isinstance(v, type):
                        v = script.DATA_TYPE_TABLE[v]
                    elif not isinstance(v, (str, ScriptDataType, ScriptTypeAnnotation)):
                        raise TypeError(f"script function parameter type union must be made of str, ScriptDataType, ScriptTypeAnnotation, or type, got: {type(v).__name__} {v}")
                    tl.append(v)
                param = (param[0], tl, *param[2:])
            param = ScriptFunctionParam(*param)
        else:
            param = ScriptFunctionParam(param[0], [AnyType])
    elif isinstance(param, dict):
        param = ScriptFunctionParam(**param)
    elif not isinstance(param, ScriptFunctionParam):
        raise ValueError(f"cannot construct script function parameter from value: {param}")
    return param


class ScriptFunction[T]:

    def __init__(self):
        self.signature = ScriptFunctionSignature([])
        self.cbs:list[Callable[..., ScriptValue]] = []

    def __get__(self, instance, owner)->"BoundScriptFunction[T]":
        b = BoundScriptFunction.__new__(BoundScriptFunction)
        b.__dict__.update(self.__dict__)
        b.instance = instance
        return b

    def add_overload(self, params:ScriptFunctionParamSet, cb:Callable[..., ScriptValue], priority:int|None=None):
        params.check()
        for existing in self.signature.overloads:
            if existing == params:
                raise exceptions.DuplicateOverloadException("overload already exists in this function")
        if priority is None:
            self.signature.overloads.append(params)
            self.cbs.append(cb)
        else:
            self.signature.overloads.insert(priority, params)
            self.cbs.insert(priority, cb)


    def overload(self, *params:ScriptFunctionParam_Like, auto:bool=False, pass_ctx:bool=False, priority:int|None=None):
        def decor(cb:Callable[..., ScriptValue]):
            if auto and not params:
                ... #TODO inspect function and determine types from annotations
            else:
                plist = []
                AnyType = script.DATA_TYPE_TABLE[object]
                for p in params:
                    plist.append(_resolve_script_function_param_like(p, AnyType))
                self.add_overload(ScriptFunctionParamSet(plist, pass_ctx=pass_ctx), cb, priority=priority)
            return cb
        return decor
    
    def _get_fit(self, ctx:ScriptContext):
        i, args, kwargs = self.signature.fit(ctx.params)
        if i is None:
            raise exceptions.TRTypeError(f"function has no overloads that match the following arguments: {", ".join(v.type().name for v in ctx.params)}")
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

_TRAIT_EXTRA_NAMES = "name", "dtypes", "default", "pack"

class ScriptTrait(script.ScriptTypeAnnotation):

    ANNOTATION_NAME = "trait"

    @classmethod
    def parse(cls, data): #trait[name, 0, (...), extra1, extra2, (extra3)]
        parts = script.split_type_annotation_contents(data, ",")
        if len(parts) < 1:
            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} takes at least 1 arguments for the trait name")
        fname = parts[0].strip()
        if not script.RE_NAME.match(fname):
            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} argument 1 must be a valid function name")
        if len(parts) < 2:
            return cls(fname, 0, [script.BASE_TYPE])
        index_s = parts[1].strip()
        if index_s:
            if not script.RE_INTEGER_SIGNED.match(index_s):
                raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} argument 2 takes an integer")
            index = int(index_s)
        else:
            index = 0
        if len(parts) < 3:
            return cls(fname, index, [script.BASE_TYPE])

        tcs_s = parts[2].strip()
        if tcs_s:
            if tcs_s[0] in script._TA_ENCL_STARTS:
                tcs_parts = script.split_type_annotation_contents(tcs_s[1:-1], ",|")
                tcs = [script.parse_script_type_annotation(part) for part in tcs_parts]
            else:
                tcs = [script.parse_script_type_annotation(tcs_s)]
        else:
            tcs = [script.BASE_TYPE]

        extra = []
        for i, part in enumerate(parts[3:]):
            if not part:
                continue
            if part[0] in script._TA_ENCL_STARTS:
                exp_parts = script.split_type_annotation_contents(part[1:-1], ",")
                if not exp_parts:
                    continue
                d = {}
                name = exp_parts[0].strip()
                if name:
                    if not script.RE_NAME.match(name):
                        raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} argument {4+i}: element 1 must be blank or a valid parameter name")
                    d["name"] = name
                if len(exp_parts) > 1:
                    dts_s = exp_parts[1].strip()
                    if dts_s:
                        if dts_s[0] in script._TA_ENCL_STARTS:
                            dts_parts = script.split_type_annotation_contents(dts_s[1:-1], ",|")
                            dts = [script.parse_script_type_annotation(part) for part in dts_parts]
                        else:
                            dts = [script.parse_script_type_annotation(dts)]
                        d["dts"] = dts
                    if len(exp_parts) > 2:
                        dfts_s = exp_parts[2].strip()
                        if dts_s:
                            if dfts_s[0] in script._TA_ENCL_STARTS:
                                dfts_parts = script.split_type_annotation_contents(dfts_s[1:-1], ",|")
                                dfts = [script.parse_script_type_annotation(part) for part in dfts_parts]
                            else:
                                dfts = [script.parse_script_type_annotation(dfts)]
                            d["default"] = dfts
                        if len(exp_parts) > 4:
                            raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} argument {4+i}: does not take more than 4 elements")
                        elif len(exp_parts) == 4:
                            pack_s = exp_parts[3].strip()
                            if pack_s  == "true":
                                d["pack"] = True
                            elif pack_s == "false":
                                d["pack"] = False
                            else:
                                raise exceptions.AnnotationBadArgumentsException(f"{cls.ANNOTATION_NAME} argument {4+i}: element 4 must be true or false")
                if d:
                    extra.append(d)
            else:
                extra.append(dict(dtypes=script.parse_script_type_annotation(part)))

            return cls(fname, index, tcs, *extra)
        

    def __init__(self, func_name:str, target_index:int, target_type_constraints:list[ScriptDataType|ScriptTypeAnnotation],
                 *extra:dict[str]):
        self.func_name = func_name
        self.target_index = target_index
        self.target_type_constraints = target_type_constraints
        self.extra = list(extra)

    def __eq__(self, other):
        if isinstance(other, ScriptTrait):
            return (self.func_name == other.func_name and
                    self.target_index == other.target_index and
                    self.target_type_constraints == other.target_type_constraints and
                    self.extra == other.extra)
        return False

    def _comp_ex(self, p:ScriptFunctionParam, ex:dict[str]):
        if (name := ex.get("name")) is not None:
            if name != p.name:
                return False
        if (dts:=ex.get("dts")) is not None:
            pdts = list(p.resolve_types())
            if not any(t in pdts for t in dts):
                return False
        if (default:=ex.get("default")) is not None:
            if p.default is _PARAM_NO_DEFAULT:
                return False
            dv = script.wrap_python_value(p.default)
            if not dv.type.issubtype(*default):
                return False
        if (pack:=ex.get("pack")):
            if pack != p.pack:
                return False
        return True

    def compare(self, other):
        func = script.SCRIPT_FUNCTION_TABLE.get(self.func_name,None)
        if not isinstance(func, ScriptFunction):
            return False
        other = script.wrap_python_value(other)
        if not other.isinstance(*self.target_type_constraints):
            return False
        for overload in func.signature.overloads:
            if self.target_index >= len(overload.params) or self.target_index*-1 > len(overload.params):
                continue
            param = overload.params[self.target_index]
            if other.isinstance(*param.resolve_types()):
                excomps:set[int] = set()
                for p in overload.params:
                    if p is param:
                        continue
                    for i, ex in enumerate(self.extra):
                        if self._comp_ex(p, ex):
                            excomps.add(i)
                if len(excomps) == len(self.extra):
                    return True
        return False

    def format_data(self):
        tcs = [t.name if isinstance(t, script.ScriptDataType) else f"{t.ANNOTATION_NAME}[{t.format_data()}]" for t in self.target_type_constraints]
        extra = [f"({", ".join("" if (v:=ex.get(name,None)) is None else v for name in _TRAIT_EXTRA_NAMES)})" for ex in self.extra]
        return f"{self.ANNOTATION_NAME}[{self.func_name}, {self.target_index},{f" ({", ".join(tcs)})," if tcs else ""}{f" {", ".join(extra)}" if extra else ""}]"

    def merge_function(self, f:ScriptFunction):
        for overload in f.signature.overloads:
            if self.target_index >= len(overload.params) or self.target_index*-1 > len(overload.params):
                continue
            param = overload.params[self.target_index]
            dts = list(param.resolve_types())
            if any(dt.issubtype(*self.target_type_constraints) for dt in dts):
                excomps:set[int] = set()
                for p in overload.params:
                    if p is param:
                        continue
                    for i, ex in enumerate(self.extra):
                        if self._comp_ex(p, ex):
                            excomps.add(i)
                if len(excomps) == len(self.extra):
                    return merge_function(self.func_name, f)
        raise exceptions.TraitMergeException(f"Function does not meet the requirements of this trait.")

    def remove_function(self, f:ScriptFunction):
        return remove_function(self.func_name, f)

        
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


def parsetree_to_xml(p:ParsingNode, include_context:bool=True):
    d = p.__dict__.copy()
    if not include_context:
        d.pop("ctx",None)
    d.pop("parent",None)
    children = d.pop("children",None)
    elm = ET.Element(type(p).__name__, attrib={k:v if isinstance(v, str) else repr(v) for k,v in d.items()})
    if children:
        for child in children:
            childelm  = parsetree_to_xml(child, include_context)
            elm.append(childelm)
    return elm

def print_parsetree(p:ParsingNode|ET.Element, include_context:bool=True):
    if not isinstance(p, ET.Element):
        p = parsetree_to_xml(p, include_context)
    return xml.dom.minidom.parseString(ET.tostring(p)).toprettyxml(indent="    ")
    

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