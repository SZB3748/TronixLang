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