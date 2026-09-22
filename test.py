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

def test_exception(ctx:ScriptContext):
    raise Exception("test")


async def async_returner(ctx:ScriptContext):
    return wrap_python_value(ctx.params[0].get().inner + 1)

f_test_annotations = utils.ScriptFunction()
f_test_iter = utils.ScriptFunction()
f_rolist = utils.ScriptFunction()

@f_test_annotations.overload(("test", script_builtins.ListOf(script_builtins.String, script_builtins.ListOf(script_builtins.AnyType))))
def test_annotations(test:ScriptVariable[list[str]]):
    print("A", test.get().inner)

@f_test_annotations.overload(("test", script_builtins.ListOf(script_builtins.Integer, script_builtins.Float)))
def test_annotations_numbers(test:ScriptVariable[list[int|float]]):
    print("B", test.get().inner)

@f_test_iter.overload(("iter_var", [script_builtins.Integer, script_builtins.NullType]), ("limit", script_builtins.Integer))
def test_iter(iter_var:ScriptVariable[int|None], limit:ScriptVariable[int]):
    itval = iter_var.get().inner
    if itval is None:
        iter_var.assign(wrap_python_value(0))
        if 0 >= limit.get().inner:
            return script_builtins.false
    else:
        if itval >= limit.get().inner-1:
            return script_builtins.false
        iter_var.assign(wrap_python_value(itval+1))
    return script_builtins.true

@f_rolist.overload(("l", script_builtins.List))
def rolist(l:ScriptVariable[list]):
    return wrap_python_value(script_builtins._rolist_wrapper(l.get().inner))
    

SCRIPT_FUNCTION_TABLE["test_async"] = test_async
SCRIPT_FUNCTION_TABLE["async_returner"] = async_returner
SCRIPT_FUNCTION_TABLE["await"] = lambda ctx: ctx.params[0].get()
SCRIPT_FUNCTION_TABLE["test_annotations"] = f_test_annotations
SCRIPT_FUNCTION_TABLE["test_iter"] = f_test_iter
SCRIPT_FUNCTION_TABLE["test_exception"] = test_exception
SCRIPT_FUNCTION_TABLE["rolist"] = f_rolist

raw = r"""
x = 2
y = map()
z = list()
w = (x + y * z)
"""


s = Script(raw)

print("="*20)
print(s.raw.strip())
print("="*20)

print("parsing")
pstart = time.perf_counter_ns()
try:
    p = s.parse("TEST")
except exceptions.TParsingException as e:
    print(utils.generate_exception_help(s, e))
    traceback.print_exception(e)
    exit(-1)
pend = time.perf_counter_ns()

print("parsed:", pend-pstart, pstart, pend)

runner = utils.ScriptRunner()

async def run_func(runner:utils.ScriptRunner, s:Script):
    try:
        estart = time.perf_counter_ns()
        await runner.run_async(s)
        eend = time.perf_counter_ns()
    except exceptions.TronixException as e:
        print(utils.generate_exception_help(s, e))
        raise
    else:
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
    try:
        cstart = time.perf_counter_ns()
        s.compile(p)
        cend = time.perf_counter_ns()
    except exceptions.TronixException as e:
        print(utils.generate_exception_help(s, e))
        raise
    print("compiled:", cend - cstart, cstart, cend)


    print("\nexecuting")
    runner.parse_trees[s._hash] = p
    
    asyncio.run(run_func(runner, s))
else:
    print(utils.print_parsetree(p, include_context=False))
    