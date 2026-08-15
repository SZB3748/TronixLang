from .script import *
from . import json_proxy, script_builtins, utils

import time
import traceback
import tracemalloc

class monitormem:
    def __enter__(self):
        tracemalloc.start()
    
    def __exit__(self, exc_type, exc, tb):
        printmem()
        tracemalloc.stop()

def printmem():
    print("MEM (current, peak):", *tracemalloc.get_traced_memory())

script_builtins.activate()

async def _print_async(x:ScriptValue):
    print(x.type.conv_str(x).inner)

def test_async(ctx:ScriptContext):
    x = ctx.params[0].get()
    return _print_async(x)


async def async_returner(ctx:ScriptContext):
    return wrap_python_value(ctx.params[0].get().inner + 1)

f_test_annotations = utils.ScriptFunction()
@f_test_annotations.overload(("test", script_builtins.ListOf(script_builtins.String, script_builtins.ListOf(script_builtins.AnyType))))
def test_annotations(test:ScriptVariable[list[str]]):
    print("A", test.get().inner)

@f_test_annotations.overload(("test", script_builtins.ListOf(script_builtins.Integer, script_builtins.Float)))
def test_annotations_numbers(test:ScriptVariable[list[int|float]]):
    print("B", test.get().inner)

SCRIPT_FUNCTION_TABLE["test_async"] = test_async
SCRIPT_FUNCTION_TABLE["async_returner"] = async_returner
SCRIPT_FUNCTION_TABLE["await"] = lambda ctx: ctx.params[0].get()
SCRIPT_FUNCTION_TABLE["test_annotations"] = f_test_annotations

raw = r"""
deg = degrees(180);
rad = radians(degrees(45));
log("degrees:", deg, percent(deg));
log("radians:", rad, percent(rad));
log("deg + rad:", deg + rad, percent(deg + rad));

log("minute and a half:", minutes(1) + percent(50));

x = 1;
log(delete("x"));
l = list(1,2,3);
log(l);
log(delete(l, 1), l);

log("annotation test:");
test_annotations(list("1", list("1", 2)));
"""

s = Script(raw)

print(s.raw)

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

    def configupdate(d)->bool:
        import json
        c = json.dumps(d, indent=4)
        with open(configs.path, "w") as f:
            f.write(c)
        return True

    configs = json_proxy.JsonProxyRoot("data/config.json", savefunc=configupdate)
    @runner.add_script_end_cb
    def save_config(_):
        if configs._pending_updates:
            configs.merge_changes()

    SCRIPT_GLOBAL_SCOPE["configs"] = ScriptVariable(wrap_python_value(configs))

    print("\ncompiling")
    cstart = time.perf_counter_ns()
    s.compile(p)
    cend = time.perf_counter_ns()
    print("compiled:", cend - cstart, cstart, cend)


    print("\nexecuting")
    runner.parse_trees[s._hash] = p
    
    asyncio.run(run_func(runner, s))

    