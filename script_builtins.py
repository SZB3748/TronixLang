from .script import *

class _FloatType(ScriptDataType):
    def construct(self, ctx)->ScriptValue[float]:
        pc = len(ctx.params)
        if pc < 1:
            return ScriptValue(self, 0.0)
        elif pc > 1:
            ... #TODO error
        
        v = ctx.params[0].get()
        if v.type is Float:
            return v
        elif v.type.isinstance(Float, Integer, Bool, String):
            return ScriptValue(self, float(v.inner))
        else:
            ... #TODO error type

    def repr(self, value):
        return ScriptValue(String, repr(value.inner))

class _IntegerType(ScriptDataType):
    def construct(self, ctx):
        pc = len(ctx.params)
        if pc < 1:
            return ScriptValue(self, 0)
        elif pc > 2:
            ... #TODO error
        
        if pc == 1:
            v = ctx.params[0].get()
            if v.type is Integer:
                return v
            elif v.type.isinstance(Integer, Bool, String):
                return ScriptValue(self, int(v.inner))
            #TODO error type
        else: # == 2
            v1 = ctx.params[0].get()
            v2 = ctx.params[1].get()
            if not v1.type.isinstance(String):
                ... #TODO error type
            if not v2.type.isinstance(Integer):
                ... #TODO error type
            return ScriptValue(self, int(v1.inner, v2.inner))
        
    def repr(self, value:ScriptValue[int]):
        return ScriptValue(String, repr(value.inner))

class _StringType(ScriptDataType):
    def construct(self, ctx):
        pc = len(ctx.params)
        if pc < 1:
            return ScriptValue(self, "")
        elif pc > 1:
            ... #TODO error
        
        v = ctx.params[0].get()
        if v.type is String:
            return v
        else:
            try:
                x = v.type.conv_str(v)
            except NotImplementedError as e:
                raise exceptions.TNotImplemented(f"str() for {v.type.name} is not implemented") from e
            except Exception as e:
                raise exceptions.wrap(e)
            if x is None:
                raise exceptions.TMustEvaluate(f"str() for {v.type.name} must evaluate but resulted in no value")
            elif x is NotImplemented:
                raise exceptions.TNotImplemented(f"str() for {v.type.name} is not implemented")
            return x
    
    def conv_str(self, value:ScriptValue[str]):
        return value

    def repr(self, value:ScriptValue[str]):
        return ScriptValue(String, repr(value.inner))


class _BoolType(ScriptDataType):
    def construct(self, ctx):
        pc = len(ctx.params)
        if pc < 1:
            return ScriptValue(self, False)
        elif pc > 1:
            ... #TODO error
        
        v = ctx.params[0].get()
        if v.type is Bool:
            return v
        else:
            try:
                x = v.type.conv_bool(v)
            except NotImplementedError as e:
                raise exceptions.TNotImplemented(f"bool() for {v.type.name} is not implemented") from e
            except Exception as e:
                raise exceptions.wrap(e)
            if x is None:
                raise exceptions.TMustEvaluate(f"bool() for {v.type.name} must evaluate but resulted in no value")
            elif x is NotImplemented:
                raise exceptions.TNotImplemented(f"bool() for {v.type.name} is not implemented")
            return x
    
    def conv_bool(self, value:ScriptValue[bool]):
        return value

    def repr(self, value:ScriptValue[bool]):
        return ScriptValue(String, "true" if value.inner else "false")



Float = _FloatType("float", float, BASE_TYPE)
Integer = _IntegerType("int", int, BASE_TYPE)
String = _StringType("str", str, BASE_TYPE)
Bool = _BoolType("bool", bool, BASE_TYPE)

_builtin_types:set[ScriptDataType] = {Float, Integer, String, Bool}

def activate():
    from . import script
    script.DATA_TYPE_TABLE.update({dt.inner:dt for dt in _builtin_types})
    script.SCRIPT_FUNCTION_TABLE.update({dt.name: dt.construct for dt in _builtin_types})