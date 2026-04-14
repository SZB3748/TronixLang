from .exceptions import *
from .script import *
from . import script
from typing import Iterable

import inspect
from typing import Any

def generate_exception_help(raw:str, e:TronixException)->str:
    s = []
    if isinstance(e, TParsingException):
        ...
    elif isinstance(e, TCompilationException):
        ...
    elif isinstance(e, TRuntimeException):
        ...
    return "".join(s)

def awaitable(v:ScriptValue|Any):
    if isinstance(v, ScriptValueAwaitable):
        return v
    elif not isinstance(v, ScriptValue):
        if inspect.isawaitable(v):
            return ScriptValueAwaitable(wrap_python_type(type(v)), v)
    elif inspect.isawaitable(v.inner):
        return ScriptValueAwaitable(v.type, v.inner)

def async_function(f):
    def async_function_wrapper(ctx:ScriptContext):
        v = f(ctx)
        if v is None or v is NotImplemented:
            return v
        else:
            return awaitable(v)
    async_function_wrapper.__name__ = f.__name__
    async_function_wrapper.__doc__ = f.__doc__
    return async_function_wrapper

def add_type(dt:ScriptDataType, constructor:bool=True):
    script.DATA_TYPE_TABLE[dt.inner] = dt
    if constructor:
        script.SCRIPT_FUNCTION_TABLE[dt.name] = dt.construct
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(script.DATA_TYPE_TABLE[type], dt.inner))

class ScriptRunner:
    def __init__(self):
        self.parse_trees:dict[bytes, ParsingNode] = {}

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

    def run_iter(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        s = self._prep(s, force_parse, force_compile)

        def _next(steps:Iterable[Callable[[], Any]]):
            for step in steps:
                x = step()
                if isinstance(x, script._step_expansion):
                    if x.new_ns_stackframe:
                        s.stack = script.ns_stack({}, s.stack)
                    yield from _next(x.steps)
                    if x.new_ns_stackframe:
                        s.stack = s.stack.prev
                else:
                    yield x

        yield from _next(s.steps)

    def run(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        s = self._prep(s, force_parse, force_compile)

        def _next(steps:Iterable[Callable[[], Any]]):
            for step in steps:
                x = step()
                if isinstance(x, script._step_expansion):
                    if x.new_ns_stackframe:
                        s.stack = script.ns_stack({}, s.stack)
                    _next(x)
                    if x.new_ns_stackframe:
                        s.stack = s.stack.prev

        _next(s.steps)

    async def run_async(self, s:Script|str, force_parse:bool=False, force_compile:bool=False):
        for result in self.run_iter(s, force_parse, force_compile):
            if inspect.isawaitable(result):
                await result

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
                tt = script._map_name_to_type(t)
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
            if all_args_match:
                for j in range(pi, len(overload.params)):
                    p = overload.params[j]
                    if p.pack:
                        continue
                    if p.default is not _PARAM_NO_DEFAULT:
                        rtv_kwargs.setdefault(p.name, ScriptVariable(wrap_python_value(p.default)))
                return i, rtv_args, rtv_kwargs
        return None, None, None

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

    def overload(self, *params:ScriptFunctionParam, auto:bool=False, pass_ctx:bool=False):
        def decor(cb:Callable[..., ScriptValue]):
            if auto and not params:
                ... #TODO inspect function and determine types from annotations
            else:
                self.add_overload(ScriptFunctionParamSet(list(params), pass_ctx=pass_ctx), cb)
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