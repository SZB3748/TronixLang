from .exceptions import *
from .script import *

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
        v = wrap_python_value(v)
    if inspect.isawaitable(v.inner):
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

class ScriptRunner:
    def __init__(self):
        self.parse_trees:dict[bytes, ParsingNode] = {}

    def _prep(self, script:Script|str, force_parse:bool, force_compile:bool):
        if isinstance(script, str):
            script = Script(script)
        if force_parse:
            p = self.parse_trees[script._hash] = script.parse()
        else:
            p = self.parse_trees.get(script._hash, None)
            if p is None:
                p = self.parse_trees[script._hash] = script.parse()
                script.compile(p)

        if force_compile or not script.steps:
            script.compile(p)
        
        return script

    def run_iter(self, script:Script|str, force_parse:bool=False, force_compile:bool=False):
        script = self._prep(script, force_parse, force_compile)
        
        for step in script.steps:
            yield step()
    

    def run(self, script:Script|str, force_parse:bool=False, force_compile:bool=False):
        script = self._prep(script, force_parse, force_compile)

        for step in script.steps:
            step()

    async def run_async(self, script:Script|str, force_parse:bool=False, force_compile:bool=False):
        for result in self.run_iter(script, force_parse, force_compile):
            if inspect.isawaitable(result):
                await result