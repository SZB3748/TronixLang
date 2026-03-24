from . import script
from .script import *

class _TypeType(ScriptDataType):
    def construct(self, ctx)->ScriptValue[type]:
        pc = len(ctx.params)
        if pc < 1:
            ... #TODO error
        elif pc > 1:
            ... #TODO error
        
        t = ctx.params[0].type()
        return ScriptValue(self, t.inner)
    
    def repr(self, value:ScriptValue[type]):
        return ScriptValue(String, f"<type {self.name} at {hex(id(value))}>")

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
        elif v.type.issubtype(Float, Integer, Bool, String):
            return ScriptValue(self, float(v.inner))
        else:
            ... #TODO error type

    def repr(self, value:ScriptValue[float]):
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
            elif v.type.issubtype(Integer, Bool, String):
                return ScriptValue(self, int(v.inner))
            #TODO error type
        else: # == 2
            v1 = ctx.params[0].get()
            v2 = ctx.params[1].get()
            if not v1.type.issubtype(String):
                ... #TODO error type
            if not v2.type.issubtype(Integer):
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


AnyType = BASE_TYPE
Type = _TypeType("type", type, BASE_TYPE)
Float = _FloatType("float", float, BASE_TYPE)
Integer = _IntegerType("int", int, BASE_TYPE)
String = _StringType("str", str, BASE_TYPE)
Bool = _BoolType("bool", bool, BASE_TYPE)

_builtin_types:set[ScriptDataType] = {Type, Float, Integer, String, Bool}

def _add_type(dt:ScriptDataType):
    script.DATA_TYPE_TABLE[dt.inner] = dt
    script.SCRIPT_FUNCTION_TABLE[dt.name] = dt.construct
    script.SCRIPT_GLOBAL_SCOPE[dt.name] = ScriptVariable(ScriptValue(Type, dt.inner))

def _add_function(name:str):
    def decor(f):
        script.SCRIPT_FUNCTION_TABLE[name] = f
        return f
    return decor

def _issubtype(t:ScriptDataType, vrs:list[ScriptVariable]):
    ts = []
    for i, vr in enumerate(vrs):
        vi:ScriptValue[type] = vr.get()
        if not vi.type.issubtype(Type):
            ... #TODO error type, use i to reference the ith parameter
        ts.append(script.DATA_TYPE_TABLE[vi.inner])
    return ScriptValue(Bool, t.issubtype(*ts))

@_add_function("isinstance")
def function_isinstance(ctx:ScriptContext):
    pc = len(ctx.params)
    if pc < 2:
        ... #TODO error
    
    v = ctx.params[0].get()
    vrs = ctx.params[1:]

    return _issubtype(v.type, vrs)

@_add_function("issubtype")
def function_issubtype(ctx:ScriptContext):
    pc = len(ctx.params)
    if pc < 2:
        ... #TODO error
    
    v = ctx.params[0].get()
    vrs = ctx.params[1:]

    if not v.type.issubtype(Type):
        ... #TODO error type
    
    return _issubtype(script.DATA_TYPE_TABLE[v.inner], vrs)

@_add_function("log")
def function_log(ctx:ScriptContext):
    ...

@_add_function("error")
def function_error(ctx:ScriptContext):
    ...

def activate():
    for dt in _builtin_types:
        _add_type(dt)