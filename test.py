from .script import *
from . import script_builtins, utils

import time
import traceback

script_builtins.activate()

def test_function(ctx:ScriptContext)->ScriptValue:
    x = ctx.params[0]
    x.assign(x.type().add(x, ScriptVariable(wrap_python_value(1))))
    return True

async def _print_async(x:ScriptValue):
    print(x.type.conv_str(x).inner)

@utils.async_function
def test_async(ctx:ScriptContext):
    x = ctx.params[0].get()
    return _print_async(x)

SCRIPT_FUNCTION_TABLE["test"] = test_function
SCRIPT_FUNCTION_TABLE["test_async"] = test_async

raw = r"""
x = 'hello';
y = 'world';
{
    x = 'evil';
    "z = ' doesn\'t exist'"
}

test_async(x + ' ' + y)

"""

s = Script(raw)

print("parsing")
pstart = time.perf_counter_ns()
try:
    p = s.parse()
except exceptions.TParsingException as e:
    traceback.print_exception(e)
    i, m = e.target
    if m is None:
        if i is None:
            span = raw
        else:
            span = raw[i-10:i+10]
    else:
        span = raw[i+m.start():i+m.end()]
    print("position", i)
    print(repr(span))
    print(f"{type(e).__name__}: {e}")
    exit(-1)
pend = time.perf_counter_ns()

print("parsed:", pend-pstart, pstart, pend)

runner = utils.ScriptRunner()

async def run_func(runner:utils.ScriptRunner, s:Script):
    estart = time.perf_counter_ns()
    await runner.run_async(s)
    eend = time.perf_counter_ns()
    print("executed:", eend - estart, estart, eend)
    print()

if __name__ == "__main__":
    import asyncio
    print("\ncompiling")
    cstart = time.perf_counter_ns()
    s.compile(p)
    cend = time.perf_counter_ns()
    print("compiled:", cend - cstart, cstart, cend)


    print("\nexecuting")
    runner.parse_trees[s._hash] = p
    
    asyncio.run(run_func(runner, s))
    
    print(s.raw)
    # print(repr(s.scope["x"].get().inner))
    # print(repr(s.scope["y"].get().inner))
    # print(repr(s.scope["z"].get().inner))