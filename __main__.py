from . import exceptions, script, script_builtins as builtins, utils
import traceback

builtins.activate()

s = script.Script("", loud_expressions=True)
runner = utils.ScriptRunner()

@runner.add_script_step_cb
async def output_step(s:script.Script, value):
    if isinstance(value, script._variable_access):
        value = await value.resolve(s.stack)
    if isinstance(value, script.ScriptVariable):
        print("[variable]", utils.script_repr(value.get()))
    elif isinstance(value, script.ScriptValue):
        print("[value]", utils.script_repr(value))
    else:
        print("[python]", value)

f_DEBUG_PARSE = utils.ScriptFunction()
f_DEBUG_STEPS = utils.ScriptFunction()
f_EXIT = utils.ScriptFunction()

@f_DEBUG_PARSE.overload(("include_context", builtins.Bool, builtins.false))
def debug_parse(include_context:script.ScriptVariable[bool]):
    print(utils.print_parsetree(p, include_context=include_context.get().inner))

@f_DEBUG_STEPS.overload(pass_ctx=True)
def debug_steps(ctx:script.ScriptContext):
    return script.wrap_python_value([repr(step) for step in ctx.script.steps])

@f_EXIT.overload(("code", builtins.Integer, 0))
def function_exit(code:script.ScriptVariable[int]):
    exit(code.get().inner)

utils.merge_function("DEBUG_PARSE", f_DEBUG_PARSE)
utils.merge_function("DEBUG_STEPS", f_DEBUG_STEPS)
utils.merge_function("EXIT", f_EXIT)

while True:
    try:
        s.raw = input(" > ")
        p = runner.cache(s, s.parse("<line input>"))
        s.compile(p)
        runner.run(s)
    except exceptions.TronixException as e:
        print(utils.generate_exception_help(s, e))
        #traceback.print_exception(e)
    except Exception as e:
        traceback.print_exception(e)
    except KeyboardInterrupt:
        print()
        break