from . import exceptions, script, script_builtins as builtins, utils
import traceback

builtins.activate()

scope = {}
runner = utils.ScriptRunner()

@runner.add_script_step_cb
async def output_step(s:script.Script, value):
    if isinstance(value, script.ScriptVariable):
        print("[variable]", utils.script_repr(value.get()))
    elif isinstance(value, script.ScriptValue):
        print("[value]", utils.script_repr(value))
    else:
        print("[python]", value)

f_DEBUG_PARSE = utils.ScriptFunction()
f_DEBUG_STEPS = utils.ScriptFunction()

@f_DEBUG_PARSE.overload(("include_matches", builtins.Bool, builtins.false))
def debug_parse(include_matches:script.ScriptVariable[bool]):
    print(utils.print_parsetree(p, include_matches=include_matches.get().inner))

@f_DEBUG_STEPS.overload(pass_ctx=True)
def debug_steps(ctx:script.ScriptContext):
    return script.wrap_python_value([repr(step) for step in ctx.script.steps])

utils.merge_function("DEBUG_PARSE", f_DEBUG_PARSE)
utils.merge_function("DEBUG_STEPS", f_DEBUG_STEPS)

while True:
    try:
        s = script.Script(input(" > "), scope, loud_expressions=True)
        p = s.parse()
        s.compile(p)
        runner.run(s)
    except exceptions.TronixException as e:
        utils.generate_exception_help(s.raw, e)
        #traceback.print_exception(e)
    except Exception as e:
        traceback.print_exception(e)
    except KeyboardInterrupt:
        print()
        break