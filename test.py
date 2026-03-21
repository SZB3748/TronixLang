from datetime import datetime
from script import *
import traceback


def test_function(ctx:ScriptContext)->ScriptValue:
    x = ctx.params[0]
    x.assign(x.type().add(x, ScriptVariable(wrap_python_value(1))))
    return True


SCRIPT_FUNCTION_TABLE["test"] = test_function

raw = "x = 1; test(x)"

s = Script(raw)

print("parsing")
pstart = datetime.now()
try:
    p = s.parse()
except exceptions.TParsingException as e:
    traceback.print_exception(e)
    i, m = e.target
    if m is None:
        if i is None:
            span = raw
        else:
            span = raw[i]
    else:
        span = raw[i+m.start():i+m.end()]
    print("position", i)
    print(span)
    print(f"{type(e).__name__}: {e}")
    exit(-1)
pend = datetime.now()

print("parsed:", (pend-pstart).total_seconds(), pstart, pend)

if __name__ == "__main__":
    print("\ncompiling")
    cstart = datetime.now()
    s.compile(p)
    cend = datetime.now()
    print("compiled:", (cend-cstart).total_seconds(), cstart, cend)

    print("\nexecuting")
    estart = datetime.now()
    for step in s.steps:
        step()
    eend = datetime.now()
    print("executed:", (eend-estart).total_seconds(), estart, eend)
    print()
    
    print(s.scope["x"].get().inner)