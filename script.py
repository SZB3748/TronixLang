from .import exceptions
from .parsingnodes import *

import hashlib
import re
from typing import Any, Callable, Self

PATTERN_NAME = r"(?:[a-zA-Z_][a-zA-Z0-9_]*)"
PATTERN_OPERATOR = r"(?:\.|[+\-*\/%=><\!]=?)"
PATTERN_INTEGER_LITERAL = r"(?:[0-9]+)"
PATTERN_FLOAT_LITERAL = r"(?:[0-9]+\.[0-9]+)"
PATTERN_STRING_LITERAL_SINGLE = r"(?:f?\'[^\\]*?(?:\\.[^\\]*?)*\')"
PATTERN_STRING_LITERAL_DOUBLE = r"(?:f?\"[^\\]*?(?:\\.[^\\]*?)*\")"
PATTERN_STRING_LITERAL = f"(?:{PATTERN_STRING_LITERAL_DOUBLE}|{PATTERN_STRING_LITERAL_SINGLE})"
PATTERN_LITERAL = f"(?:(?P<value_float>{PATTERN_FLOAT_LITERAL})|(?P<value_integer>{PATTERN_INTEGER_LITERAL})|(?P<value_string>{PATTERN_STRING_LITERAL}))"
PATTERN_VALUE = f"(?:(?P<value_name>{PATTERN_NAME})|{PATTERN_LITERAL})"
PATTERN_FUNCTION_BEGIN = f"(?:(?P<function_name>{PATTERN_NAME})\\s*\\()"
#PATTERN_ASSIGN_BEGIN = f"(?:(?P<assign_name>{PATTERN_NAME})\\s*=)"
PATTERN_MAIN = f"\\s*(?:(?P<function>{PATTERN_FUNCTION_BEGIN})|(?P<operator>{PATTERN_OPERATOR})|(?P<value>{PATTERN_VALUE})|(?P<semicolon>;)|(?P<comma>,)|(?P<parenthesis>\\()|(?P<enclend>[\\]\\)]))"

RE_MAIN = re.compile(PATTERN_MAIN)

# max told me to call this language Tronix, i'll think abt it 

class ScriptValue[T]:
    def __init__(self, value_type:"ScriptDataType", inner:T):
        self.type = value_type
        self.inner = inner

class ScriptValueAwaitable[T](ScriptValue[T]):
    def __await__(self):
        yield from self.inner.__await__()

class ScriptVariable:
    def __init__(self, value:ScriptValue):
        self.value = value
    
    def type(self):
        return self.value.type

    def get(self)->ScriptValue:
        return self.value
    
    def assign(self, value:ScriptValue):
        self.value = value

class ScriptDataType:
    """The default datatype containing all the default operation behaviors."""

    def __init__(self, name:str, inner:type, parent:Self):
        self.name = name
        self.inner = inner
        self.parent = parent
    
    def isinstance(self, *dts:"ScriptDataType")->bool:
        c = self
        while c is not BASE_TYPE:
            if c in dts:
                return True
            c = c.parent
        return False

    def construct(self, ctx:"ScriptContext")->ScriptValue:
        return ScriptValue(self, object())
    
    def conv_str(self, value:ScriptValue)->ScriptValue[str]:
        return self.repr(value)

    def conv_bool(self, value:ScriptValue)->ScriptValue[bool]:
        return _convert_script_value(bool(value.inner))
    
    def repr(self, value:ScriptValue)->ScriptValue[str]:
        return _convert_script_value(f"<value {self.name} at {hex(id(value))}>")
    
    def lt(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner < rhs.get().inner)
    
    def le(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner <= rhs.get().inner)
    
    def gt(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner > rhs.get().inner)
    
    def ge(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner >= rhs.get().inner)
    
    def eq(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner == rhs.get().inner)
    
    def ne(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue[bool]|None:
        return wrap_python_value(lhs.get().inner != rhs.get().inner)
    
    def add(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner + rhs.get().inner)
    
    def sub(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner - rhs.get().inner)
    
    def mlt(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner * rhs.get().inner)
    
    def div(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner / rhs.get().inner)
    
    def mod(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(lhs.get().inner % rhs.get().inner)
    
    def iadd(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        x = wrap_python_value(lhs.get().inner + rhs.get().inner)
        lhs.assign(x)
        return x
    
    def isub(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        x = wrap_python_value(lhs.get().inner - rhs.get().inner)
        lhs.assign(x)
        return x
    
    def imlt(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        x = wrap_python_value(lhs.get().inner * rhs.get().inner)
        lhs.assign(x)
        return x
    
    def idiv(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        x = wrap_python_value(lhs.get().inner / rhs.get().inner)
        lhs.assign(x)
        return x
    
    def imod(self, lhs:ScriptVariable, rhs:ScriptVariable)->ScriptValue|None:
        x = wrap_python_value(lhs.get().inner % rhs.get().inner)
        lhs.assign(x)
        return x
    
    def uadd(self, h:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(+h.get().inner)

    def usub(self, h:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(-h.get().inner)

    def unot(self, h:ScriptVariable)->ScriptValue|None:
        return wrap_python_value(not h.get().inner)
    
    def getattr(self, obj:ScriptValue, name:str)->ScriptValue:
        return wrap_python_value(getattr(obj.inner, name))
    
    def setattr(self, obj:ScriptValue, name:str, value:ScriptVariable)->ScriptValue:
        setattr(obj.inner, name, value.get().inner)
        return wrap_python_value(getattr(obj.inner, name))

    def delattr(self, obj:ScriptValue, name:str)->ScriptValue:
        v = wrap_python_value(getattr(obj.inner, name))
        delattr(obj.inner, name)
        return v

    def getitem(self, obj:ScriptValue, item:ScriptVariable)->ScriptValue:
        return wrap_python_value(obj.inner[item.get().inner])
    
    def setitem(self, obj:ScriptValue, item:ScriptVariable, value:ScriptVariable)->ScriptValue:
        obj.inner[item.get().inner] = value.get().inner
        return wrap_python_value(obj.inner[item.get().inner])

    def delitem(self, obj:ScriptValue, item:ScriptVariable)->ScriptValue:
        v = wrap_python_value(obj.inner[item.get().inner])
        del obj.inner[item.get().inner]
        return v

Namespace = dict[str, ScriptVariable]

class ns_stack:
    def __init__(self, ns:Namespace, prev:Self|None=None):
        self.ns = ns
        self.prev = prev

    def find_name(self, name:str):
        node = self
        while node is not None:
            if name in node.ns:
                return node.ns
            node = node.prev

class ScriptContext:
    def __init__(self, stack:ns_stack, params:list[ScriptVariable]):
        self.stack = stack
        self.params = params

FunctionTable = dict[str, Callable[[ScriptContext], ScriptValue]]

SCRIPT_FUNCTION_TABLE:FunctionTable = {}
SCRIPT_GLOBAL_SCOPE:Namespace = {}

class _enclose_stack:
    def __init__(self, c:str, end:str, pnode:ParsingNode, basenode:ParsingNode, prev:Self|None=None):
        self.c = c
        self.end = end
        self.pnode = pnode
        self.basenode = basenode
        self.prev = prev

class _operation_node:
    def __init__(self, position:int, operation:str, onode:ParsingNodeOperator, precedence:int, lhand:Self|Any, rhand:Self|Any):
        self.position = position
        self.operation = operation
        self.onode = onode
        self.precedence = precedence
        self.lhand = lhand
        self.rhand = rhand

class _variable_access:
    def __init__(self, name_path:list[str], value_root:ScriptVariable|ScriptValue|None=None):
        self.name_path = name_path
        self.value_root = value_root

    def resolve(self, stack:ns_stack, slice_end:int=None)->ScriptVariable|ScriptValue|None:
        if slice_end is None:
            slice_end = len(self.name_path)
            
        if self.value_root is None:
            ns = stack.find_name(self.name_path[0])
            if ns is None:
                return None
            target = ns[self.name_path[0]]
            i = 1
        elif isinstance(self.value_root, (ScriptValue, ScriptVariable)):
            target = self.value_root
            i = 0
        
        subpath = self.name_path[i:slice_end]
        if not subpath:
            return target
        
        if isinstance(target, ScriptVariable):
            target = target.get()
        for name in subpath:
            target = target.type.getattr(target, name)
        
        return target

class _step_evaluation:
    def __init__(self, cb:Callable[[], Any]=None):
        self.cb = cb

    def __call__(self):
        return self.cb()
    
    def __bool__(self):
        return self.cb is not None

_escape_character_mapping = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "\n": "",
    "\\": "\\",
    "'": "'",
    "\"": "\"",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "v": "\v"
}

_operator_order = [
    {"."},
    {"-u", "+u", "!u"},
    {"*", "/", "%"},
    {"+", "-"},
    {"==", "!=", ">=", "<=", ">", "<"},
    {"=", "+=", "-=", "*=", "/=", "%="},
]

#operator associativity for order sets, True is left-to-right, False is right-to-left. doesn't especially matter for unary
_operator_direction = {
    0: False,
    1: True,
    2: True,
    3: True,
    4: True,
    5: False
}


_operator_order_index = {k:i for i, so in enumerate(_operator_order) for k in so} #maps each operator to the index of its order set

BASE_TYPE = ScriptDataType("object", object, None); BASE_TYPE.parent = BASE_TYPE

DATA_TYPE_TABLE:dict[type, ScriptDataType] = {
    object: BASE_TYPE
}

def _convert_script_value(value):
    t = DATA_TYPE_TABLE.get(type(value), None)
    if t is None:
        return None
    return ScriptValue(t, value)

def wrap_python_value(value):
    v = _convert_script_value(value)
    if v is None:
        t = type(value)
        st = tchain = ScriptDataType(t.__name__, t, None)
        for sup in t.mro():
            supt = DATA_TYPE_TABLE.get(sup, None)
            if supt is None:
                tchain.parent = ScriptDataType(sup.__name__, sup, None)
            else:
                tchain.parent = supt
                break
        DATA_TYPE_TABLE[t] = st
        v = ScriptValue(st, value)
    return v


class Script:
    def __init__(self, raw:str, scope:Namespace=None, global_scope:Namespace=SCRIPT_GLOBAL_SCOPE, function_table:FunctionTable=SCRIPT_FUNCTION_TABLE):
        self.raw = raw
        self._hash = hashlib.md5(raw.encode("utf-8"), usedforsecurity=False).digest()
        self.scope = {} if scope is None else scope
        self.global_scope = global_scope
        self.function_table = function_table
        self.steps:list[Callable[[]]] = []
        self.stack = ns_stack(self.scope, ns_stack(global_scope))
    
    def parse(self)->ParsingNode:
        i = 0
        root = ParsingNode(None)
        current = root
        enclstack:_enclose_stack|None = None

        #build the parse tree
        while True:
            _s = self.raw[i:]
            r = RE_MAIN.match(_s)
            if r is None:
                if _s.strip():
                    raise exceptions.TParsingException("unrecognizable syntax", target=(i, None))
                return root
            if r["function"] is not None:
                if not isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                    exprnode = ParsingNodeExpression(r, current)
                    current.children.append(exprnode)
                    current = exprnode
                node = ParsingNodeFunction(r["function_name"], r, current)
                current.children.append(node)
                enclstack = _enclose_stack("(",")", node, current, enclstack)
                current = node
                i += r.end()
            elif r["value"] is not None:
                v_name = r["value_name"]
                v_string = r["value_string"]
                v_integer = r["value_integer"]
                v_float = r["value_float"]
                if not isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                    exprnode = ParsingNodeExpression(r, current)
                    current.children.append(exprnode)
                    current = exprnode
                if v_name:
                    node = ParsingNodeName(v_name, r, current)
                else:
                    if v_string:
                        vs = v_string[1:-1] #strip off the quotes
                        chars = []
                        ci = 0
                        while ci < len(vs):
                            c = vs[ci]
                            if c == "\\":
                                ci += 1
                                c = vs[ci]
                                ec = _escape_character_mapping.get(c, None)
                                if ec:
                                    chars.append(ec)
                                elif c == "u":
                                    chars.append(chr(int(vs[ci+1:ci+5], 16)))
                                    ci += 4 #(ci + 5 - 1) + 1
                                elif c == "U":
                                    chars.append(chr(int(vs[ci+1:ci+9], 16)))
                                    ci += 8
                                elif c == "o":
                                    chars.append(chr(int(vs[ci+1:ci+3], 8)))
                                    ci += 2
                                elif c == "x":
                                    chars.append(chr(int(vs[ci+1:ci+3], 16)))
                                    ci += 2
                                else:
                                    chars.append(f"\\{c}")
                            else:
                                chars.append(c)
                            ci += 1
                        value = "".join(chars)
                    elif v_integer:
                        value = int(v_integer)
                    elif v_float:
                        value = float(v_float)
                    else:
                        raise exceptions.TUnknownValue(f"unknown value", target=(i, r))
                    node = ParsingNodeValue(value, r, current)
                current.children.append(node)
                i += r.end()
            elif (operator := r["operator"]) is not None:
                if not isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                    exprnode = ParsingNodeExpression(r, current)
                    current.children.append(exprnode)
                    current = exprnode
                node = ParsingNodeOperator(operator, r, current)
                current.children.append(node)
                i += r.end()
            elif r["parenthesis"] is not None:
                if not isinstance(current, (ParsingNodeExpression, ParsingNodeParentheses)):
                    exprnode = ParsingNodeExpression(r, current)
                    current.children.append(exprnode)
                    current = exprnode
                node = ParsingNodeParentheses(r, current)
                current.children.append(node)
                enclstack = _enclose_stack("(",")", node, current, enclstack)
                current = node
                i += r.end()
            elif (enclend := r["enclend"]) is not None:
                if enclstack is None:
                    raise exceptions.TEnclMismatch(f"unmatched {enclend}", target=(i, r))
                elif enclstack.end != enclend:
                    raise exceptions.TEnclMismatch(f"closing {enclend} does not match opening {enclstack.c}", target=(i, r))
                current = enclstack.basenode
                enclstack = enclstack.prev
                i += r.end()
            elif r["comma"] is not None:
                if enclstack is not None:
                    if isinstance(enclstack.pnode, ParsingNodeFunction):
                        current = enclstack.pnode
                        current.children.append(ParsingNodeComma(r, current))
                        continue
                raise exceptions.TUnexpectedSymbol("unexpected here", target=(i, r))
            elif r["semicolon"] is not None:
                if enclstack is not None: #NOTE: if adding code blocks, allow code blocks to contain semicolons (enclstack.pnode isinstance check)
                    raise exceptions.TUnexpectedSymbol("unexpected here", target=(i, r))
                if isinstance(current, ParsingNodeExpression):
                    current = root #NOTE: this only works if code blocks dont exist, the semicolon must bring current to the nearest code block (or default to root)
                i += r.end()
            elif enclstack is not None:
                raise exceptions.TExpectedSymbol("expected here", target=(i, r))
            else:
                return root

    def _generate_function_call_step(self, node:ParsingNodeFunction, params:list[Callable[[], ScriptVariable]]):
        def _function_step(): #evaluable step: step function 
            if node.function_name in self.function_table:
                function = self.function_table[node.function_name]
                evaluated_params = []
                for param_cb in params:
                    param = param_cb()
                    while isinstance(param, _step_evaluation):
                        param = param()
                    if isinstance(param, ScriptValue):
                        param = ScriptVariable(param)
                    evaluated_params.append(param)
                    
                local_ns = {}
                self.stack = ns_stack(local_ns, self.stack) #push
                ctx = ScriptContext(stack=self.stack, params=evaluated_params)
                value = function(ctx)
                self.stack = self.stack.prev #pop
                return value
            else:
                raise exceptions.TMissingFunction(f"cannot find callable name {node.function_name}")
        return _function_step

    def _generate_function_steps(self, node:ParsingNodeFunction, rtv:_step_evaluation|None=None):
        params:list[Callable[[],ScriptVariable]] = []
        param:Callable[[],ScriptVariable]|None = None
        for child in node.children:
            if isinstance(child, ParsingNodeComma):
                if param is None:
                    raise exceptions.TIncorrectParamaterOrder("comma is not following a parameter", target=child)
                params.append(param)
                param = None
            elif param is not None:
                raise exceptions.TIncorrectParamaterOrder("consecutive parameters without a comma", target=child)
                
            if isinstance(child, ParsingNodeFunction):
                param = _step_evaluation()
                self._generate_function_steps(child, param)
            elif isinstance(child, (ParsingNodeExpression, ParsingNodeParentheses)):
                param = _step_evaluation()
                self._generate_expression_steps(child, param)
            else:
                assert False, f"Unexpected node: {child}"

        if param is not None:
            params.append(param)
        
        step_cb = self._generate_function_call_step(node, params)
        if rtv is None:
            self.steps.append(step_cb)
        else:
            rtv.cb = step_cb

    def _get_expression_operations(self, node:ParsingNodeExpression|ParsingNodeParentheses)->_operation_node:
        operators:list[tuple[int, str, ParsingNodeOperator, int]] = []
        lh = None
        root_precedence_level = -1
        root_index = None
        root_direction = None
        for i, child in enumerate(node.children):
            if isinstance(child, ParsingNodeOperator):
                if lh is None:
                    operator = f"{child.operator}u"
                else:
                    operator = child.operator
                    lh = None

                precedence = _operator_order_index.get(operator, None)
                assert precedence is not None, f"Missing compilation data for handling operator: {operator}"

                oi = len(operators)
                operators.append((i, operator, child, precedence))
                
                if precedence > root_precedence_level:
                    root_precedence_level = precedence
                    root_index = oi
                    root_direction = _operator_direction[precedence]
                elif precedence == root_precedence_level:
                    if root_direction and oi > root_index:
                        root_index = oi
                    #no other checks needed cause right-left associativity (False direction) needs the first operator as the root
            elif lh is None:
                lh = child
            else:
                raise exceptions.TIncorrectOperandOrder("consecutive operands where operator is expected", target=child)

        if root_index is None:
            return None #no operators, node only contains a value
        
        def _left_construct(midpoint:int, parent:_operation_node, bounds:tuple[int, int]):
            if parent.operation.endswith("u"):
                return
            
            plevel = -1
            next_midpoint = None
            next_direction = None
            for i  in range(bounds[0], midpoint):
                *_, p = operators[i]
                if p > plevel:
                    plevel = p
                    next_midpoint = i
                    next_direction = _operator_direction[p]
                elif p == plevel:
                    if next_direction and i > next_midpoint:
                        next_midpoint = i

            if next_midpoint is None:
                lhand = node.children[parent.position-1]
                if isinstance(lhand, (ParsingNodeParentheses, ParsingNodeExpression)):
                    l = self._get_expression_operations(lhand)
                    if l is None:
                        if len(lhand.children) == 1 and isinstance((child := lhand.children[0]), (ParsingNodeName, ParsingNodeValue)):
                            lhand = child
                        else:
                            raise exceptions.TInvalidOperand("invalid expression", target=lhand)
                    else:
                        lhand = l
                parent.lhand = lhand
            else:
                next = _operation_node(*operators[next_midpoint], None, None)
                parent.lhand = next
                _left_construct(next_midpoint, next, (bounds[0], next_midpoint-1))
                _right_construct(next_midpoint, next, (next_midpoint+1, bounds[1]))
        
        def _right_construct(midpoint:int, parent:_operation_node, bounds:tuple[int, int]):
            plevel = -1
            next_midpoint = None
            next_direction = None
            for i in range(midpoint+1, bounds[1]+1):
                *_, p = operators[i]
                if p > plevel:
                    plevel = p
                    next_midpoint = i
                    next_direction = _operator_direction[p]
                elif p == plevel:
                    if next_direction and i > next_midpoint:
                        next_midpoint = i
            
            if next_midpoint is None:
                rhand = node.children[parent.position+1]
                if isinstance(rhand, (ParsingNodeParentheses, ParsingNodeExpression)):
                    r = self._get_expression_operations(rhand)
                    if r is None:
                        if len(rhand.children) == 1 and isinstance((child := rhand.children[0]), (ParsingNodeName, ParsingNodeValue)):
                            rhand = child
                        else:
                            raise exceptions.TInvalidOperand("invalid expression", target=rhand)
                    else:
                        rhand = r
                parent.rhand = rhand
            else:
                next = _operation_node(*operators[next_midpoint], None, None)
                parent.rhand = next
                _left_construct(next_midpoint, next, (bounds[0], next_midpoint-1))
                _right_construct(next_midpoint, next, (next_midpoint+1, bounds[1]))

        root = _operation_node(*operators[root_index], None, None)

        _left_construct(root_index, root, (0, root_index-1))
        _right_construct(root_index, root, (root_index+1, len(operators)-1))

        return root
    
    def _generate_operation_steps(self, operation:_operation_node|Any):
        if isinstance(operation, _operation_node):
            lhs = self._generate_operation_steps(operation.lhand)
            rhs = self._generate_operation_steps(operation.rhand)
            return _step_evaluation(_operator_step_generators[operation.operation](self, lhs, rhs))
        elif isinstance(operation, ParsingNodeFunction):
            step_eval = _step_evaluation()
            self._generate_function_steps(operation, rtv=step_eval)
            return step_eval
        elif isinstance(operation, ParsingNodeName):
            return operation
        elif isinstance(operation, ParsingNodeValue):
            value = _convert_script_value(operation.value)
            assert value is not None, f"Failed to lookup type for value: {operation} {repr(operation.value)}"
            return value

    def _generate_expression_steps(self, node:ParsingNodeExpression|ParsingNodeParentheses, rtv:_step_evaluation|None=None):
        operation_tree = self._get_expression_operations(node)
        if operation_tree is None:
            child = node.children[0]
            if isinstance(child, ParsingNodeFunction):
                self._generate_function_steps(child, rtv)
            elif isinstance(child, ParsingNodeName):
                def _resolve_name(n:ParsingNodeName):
                    def _step():
                        ns = self.stack.find_name(n.name)
                        if ns is None:
                            raise exceptions.TMissingName(f"{repr(n.name)} not found")
                        return ns[n.name]
                    return _step
                if rtv is not None:
                    rtv.cb = _resolve_name(child)
            elif isinstance(child, ParsingNodeValue):
                if rtv is not None:
                    value = _convert_script_value(child.value)
                    rtv.cb = lambda: value
            assert not isinstance(child, (ParsingNodeExpression, ParsingNodeParentheses)), f"illegal recursive node: {node} -> {child}"   
        else:
            os = self._generate_operation_steps(operation_tree)
            if isinstance(os, _step_evaluation) and os:
                if rtv is None:
                    self.steps.append(os.cb)
                else:
                    rtv.cb = os.cb
            elif isinstance(os, ParsingNodeName):
                ...
            elif isinstance(os, ScriptValue):
                ...
            else:
                raise exceptions.TInvalidParameter("failed to evaluate parameter", node)


    def compile(self, tree:ParsingNode):
        if self.steps:
            self.steps.clear()
        for node in tree.children:
            if isinstance(node, (ParsingNodeExpression, ParsingNodeParentheses)):
                self._generate_expression_steps(node)
            elif isinstance(node, ParsingNodeFunction):
                self._generate_function_steps(node)


def _validate_h(h):
    return isinstance(h, (_step_evaluation, _variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

def _resolve_h(script:Script, h)->ScriptVariable:
    _h = h
    if isinstance(h, _step_evaluation):
        h = h()
    if isinstance(h, _variable_access):
        h = h.resolve(script.stack)
        
    if isinstance(h, ScriptVariable):
        return h
    elif isinstance(h, ScriptValue):
        return ScriptVariable(h)
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            raise exceptions.TMissingName(f"{repr(h.name)} not found")
        return ns[h.name]
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_vh(h):
    return isinstance(h, (_step_evaluation, _variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

def _resolve_vh(script:Script, h)->ScriptValue:
    _h = h
    if isinstance(h, _step_evaluation):
        h = h()
    if isinstance(h, _variable_access):
        h = h.resolve(script.stack)
    
    if isinstance(h, ScriptVariable):
        return h.get()
    elif isinstance(h, ScriptValue):
        return h
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            raise exceptions.TMissingName(f"{repr(h.name)} not found")
        return ns[h.name].get()
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_ih(h):
    return isinstance(h, (_variable_access, ScriptVariable, ParsingNodeName))

def _resolve_ih(script:Script, h, make_name_if_missing:bool=False)->ScriptVariable:
    _h = h
    if isinstance(h, _variable_access):
        h = h.resolve(script.stack)
        
    if isinstance(h, ScriptVariable):
        return h
    elif isinstance(h, ScriptValue):
        return ScriptVariable(h)
    elif isinstance(h, ParsingNodeName):
        ns = script.stack.find_name(h.name)
        if ns is None:
            if make_name_if_missing:
                ns = script.stack.ns
                ns[h.name] = ScriptVariable(None)
            else:
                raise exceptions.TMissingName(f"{repr(h.name)} not found")
        return ns[h.name]
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {_h} -> {h}")

def _validate_nh(h):
    return isinstance(h, (_variable_access, ScriptVariable, ScriptValue, ParsingNodeName))

def _resolve_nh(h)->_variable_access:
    if isinstance(h, _variable_access):
        return h
    elif isinstance(h, (ScriptValue, ScriptVariable)):
        return _variable_access([], h)
    elif isinstance(h, ParsingNodeName):
        return _variable_access([h.name])
    else:
        raise exceptions._TronixRuntimeAssertion(f"invalid operand {h}")


def _generate_add_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().add(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step

def _generate_sub_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().sub(l, r)
            print(l.get().inner, "-", r.get().inner, "->", x.inner)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_mlt_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().mlt(l, r)
            print(l.get().inner, "*", r.get().inner, "->", x.inner)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_div_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().div(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_mod_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().mod(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_iadd_steps(script:Script, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_ih(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().iadd(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_isub_steps(script:Script, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_ih(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().isub(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_imlt_steps(script:Script, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_ih(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().imlt(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_idiv_steps(script:Script, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_ih(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().idiv(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    

def _generate_imod_steps(script:Script, lh, rh):
    if not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_ih(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().imod(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    
def _generate_dot_steps(script:Script, lh, rh):
    if not _validate_nh(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to something with attributes")
    elif not isinstance(rh, ParsingNodeName):
        raise exceptions.TInvalidOperand("right-hand operand must be a name")
    def _step():
        l = _resolve_nh(lh)
        return _variable_access([*l.name_path, rh.name], l.value_root)
    return _step

def _generate_assign_steps(script:Script, lh, rh):
    if isinstance(lh, _variable_access) and len(lh.name_path) > 1:
        if not _validate_vh(rh):
            raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
        def _step():
            l = lh.resolve(script.stack, -1)
            if l is None:
                raise exceptions.TMissingName(f"{repr(lh.name_path[0])} not found")
            elif isinstance(l, ScriptVariable):
                r = _resolve_vh(script, rh)
                l.assign(r)
            else:
                r = _resolve_vh(script, rh)
                try:
                    x = l.type.setattr(l, lh.name_path[-1], r)
                except NotImplementedError as e:
                    raise exceptions.TNotImplemented("operation is not implemented") from e
                except Exception as e:
                    raise exceptions.wrap(e)
                if x is None:
                    raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
                elif x is NotImplemented:
                    raise exceptions.TNotImplemented("operation is not implemented")
            return r
    elif not _validate_ih(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must be a variable or attribute")
    elif not _validate_vh(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    else:
        def _step():
            l = _resolve_ih(script, lh, make_name_if_missing=True)
            r = _resolve_vh(script, rh)
            l.assign(r)
            return r
    return _step

def _generate_uadd_steps(script:Script, lh, rh):
    if lh is not None:
        raise exceptions._TronixRuntimeAssertion(f"unary operations should not be passed a left-hand operand: {lh}")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"operand must resolve to a value")
    def _step():
        h = _resolve_h(script, rh)
        try:
            x = h.type().uadd(h)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step
    
def _generate_usub_steps(script:Script, lh, rh):
    if lh is not None:
        raise exceptions._TronixRuntimeAssertion(f"unary operations should not be passed a left-hand operand: {lh}")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"operand must resolve to a value")
    def _step():
        h = _resolve_h(script, rh)
        try:
            x = h.type().usub(h)
            print("-", h.get().inner, "->", x.inner)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step

def _generate_unot_steps(script:Script, lh, rh):
    if lh is not None:
        raise exceptions._TronixRuntimeAssertion(f"unary operations should not be passed a left-hand operand: {lh}")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"operand must resolve to a value")
    def _step():
        h = _resolve_h(script, rh)
        try:
            x = h.type().unot(h)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step


def _generate_gt_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().gt(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step

def _generate_lt_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().lt(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step

def _generate_ge_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().ge(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step

def _generate_le_steps(script:Script, lh, rh):
    if not _validate_h(lh):
        raise exceptions.TInvalidOperand(f"left-hand operand must resolve to a value")
    elif not _validate_h(rh):
        raise exceptions.TInvalidOperand(f"right-hand operand must resolve to a value")
    def _step():
        l = _resolve_h(script, lh)
        r = _resolve_h(script, rh)
        try:
            x = l.type().le(l, r)
        except NotImplementedError as e:
            raise exceptions.TNotImplemented("operation is not implemented") from e
        except Exception as e:
            raise exceptions.wrap(e)
        if x is None:
            raise exceptions.TMustEvaluate(f"operation must evaluate but resulted in no value")
        elif x is NotImplemented:
            raise exceptions.TNotImplemented("operation is not implemented")
        return x
    return _step



_operator_step_generators:dict[str, Callable[[Script, Any, Any], Callable[[], _variable_access|ScriptValue]]] = {
    ".": _generate_dot_steps,
    "-u": _generate_usub_steps,
    "+u": _generate_uadd_steps,
    "!u": _generate_unot_steps,
    "*": _generate_mlt_steps,
    "/": _generate_div_steps,
    "%": _generate_mod_steps,
    "+": _generate_add_steps,
    "-": _generate_sub_steps,
    ">": _generate_gt_steps,
    "<": _generate_lt_steps,
    ">=": _generate_ge_steps,
    "<=": _generate_le_steps,
    "=": _generate_assign_steps,
    "+=": _generate_iadd_steps,
    "-=": _generate_isub_steps,
    "*=": _generate_imlt_steps,
    "/=": _generate_idiv_steps,
    "%=": _generate_imod_steps,
}

