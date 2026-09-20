from typing import Any, Self
from re import Match

class ParsingContext:
    __slots__ = "i", "match", "name", "parent", "i_end"
    def __init__(self, i:int, match:Match|None, name:str, parent:Self|None=None, i_end:int|None=None):
        self.i = i
        self.match = match
        self.name = name
        self.parent = parent
        self.i_end = i_end

    def __repr__(self):
        return f"<{type(self).__name__} i={self.i} match={self.match} name={repr(self.name)} parent={"NONE" if self.parent is None else repr(self.parent.name)}>"

class ParsingNode:
    def __init__(self, ctx:ParsingContext, parent:"ParsingNode|None"=None, children:list["ParsingNode"]|None=None):
        self.parent = parent
        self.children = [] if children is None else children
        self.ctx = ctx

class ParsingNode_Terminating(ParsingNode):
    def __init__(self, ctx:ParsingContext, parent:ParsingNode|None=None):
        super().__init__(ctx, parent, None)

class ParsingNodeExpression(ParsingNode):
    pass

class ParsingNodeName(ParsingNode_Terminating):
    def __init__(self, name:str, ctx:ParsingContext, parent:ParsingNode|None=None):
        super().__init__(ctx, parent)
        self.name = name

class ParsingNodeFunction(ParsingNode):
    def __init__(self, function_name:str, ctx:ParsingContext, parent:ParsingNode|None=None, parameters:list[ParsingNode]|None=None):
        super().__init__(ctx, parent, parameters)
        self.function_name = function_name

class ParsingNodeValue(ParsingNode_Terminating):
    def __init__(self, value:Any, ctx:ParsingContext, parent:ParsingNode|None=None):
        super().__init__(ctx, parent)
        self.value = value

class ParsingNodeFString(ParsingNode):
    pass

class ParsingNodeParentheses(ParsingNode):
    pass

class ParsingNodeCodeBlock(ParsingNode):
    pass

class ParsingNodeComma(ParsingNode_Terminating):
    pass

class ParsingNodeOperator(ParsingNode_Terminating):
    def __init__(self, operator:str, ctx:ParsingContext, parent:ParsingNode|None=None):
        super().__init__(ctx, parent)
        self.operator = operator

class ParsingNodeSubscript(ParsingNode):
    pass

class ParsingNodeIfStatement(ParsingNode):
    pass

class ParsingNodeLoopExpression(ParsingNode):
    def __init__(self, ctx:ParsingContext, parent:"ParsingNodeLoopStatement|None"=None, expression:ParsingNodeExpression|ParsingNodeParentheses|None=None):
        super().__init__(ctx, parent, [])
        if expression is not None:
            self.children.append(expression)

class ParsingNodeLoopStatement(ParsingNode):
    def __init__(self, ctx:ParsingContext, parent:ParsingNode|None=None, expressions:list[ParsingNodeLoopExpression]|None=None, codeblock:ParsingNodeCodeBlock|None=None):
        super().__init__(ctx, parent, [])
        if expressions is not None:
            self.children.extend(expressions)
        if codeblock is not None:
            self.children.append(codeblock)


class ParsingNodeConditionPair(ParsingNode):
    def __init__(self, ctx:ParsingContext, parent:ParsingNodeIfStatement|None, condition:ParsingNodeExpression|ParsingNodeParentheses|None=None, codeblock:ParsingNodeCodeBlock|None=None, takes_condition:bool=False):
        super().__init__(ctx, parent, [])
        self.takes_condition = takes_condition
        if condition is not None:
            self.condition = condition
        if codeblock is not None:
            self.codeblock = codeblock
    
    @property
    def condition(self)->ParsingNodeExpression|ParsingNodeParentheses|None:
        if self.takes_condition and len(self.children) > 0:
            return self.children[0]
        else:
            return None
    
    @condition.setter
    def condition(self, value:ParsingNodeExpression|ParsingNodeParentheses|None):
        if self.takes_condition:
            if self.children:
                self.children[0] = value
            else:
                self.children.append(value)
    
    @property
    def codeblock(self)->ParsingNodeCodeBlock|None:
        i = bool(self.takes_condition)
        if len(self.children) > i:
            return self.children[i]
        else:
            return None
    
    @codeblock.setter
    def codeblock(self, value:ParsingNodeCodeBlock|None):
        i = bool(self.takes_condition)
        if len(self.children) > i:
            self.children[bool(self.takes_condition)] = value
        else:
            if i-1 >= len(self.children):
                self.children.append(None)
            self.children.append(value)

class ParsingNodeNVPair(ParsingNode):
    def __init__(self, ctx:ParsingContext, parent:ParsingNode|None=None, name:ParsingNodeName|None=None, value:ParsingNodeExpression|ParsingNodeParentheses|None=None):
        super().__init__(ctx, parent, [])
        if name is not None:
            self.name = name
        if value is not None:
            self.value = value

    @property
    def name(self)->ParsingNodeName|None:
        if self.children:
            return self.children[0]
        else:
            return None
    
    @name.setter
    def name(self, value:ParsingNodeName|None):
        if self.children:
            self.children[0] = value
        else:
            self.children.append(value)
    
    @property
    def value(self)->ParsingNodeExpression|ParsingNodeParentheses|None:
        if len(self.children) > 1:
            return self.children[1]
        else:
            return None
    
    @value.setter
    def value(self, value:ParsingNodeExpression|ParsingNodeParentheses|None):
        if len(self.children) > 1:
            self.children[1] = value
        else:
            if not self.children:
                self.children.append(None)
            self.children.append(value)

class ParsingNodeVarDecl(ParsingNode):
    def __init__(self, ctx:ParsingContext, kw:str, parent:ParsingNode|None=None, name:ParsingNodeName|None=None):
        super().__init__(ctx, parent, [])
        self.kw = kw
        if name is not None:
            self.children.append(name)

    @property
    def name(self)->ParsingNodeName|None:
        if self.children:
            return self.children[0]
        else:
            return None
    
    @name.setter
    def name(self, value:ParsingNodeName|None):
        if self.children:
            self.children[0] = value
        else:
            self.children.append(value)

class ParsingNodeLoopControl(ParsingNode_Terminating):
    def __init__(self, flags:int, value:int, ctx:ParsingContext, parent:ParsingNode|None=None):
        super().__init__(ctx, parent)
        self.flags = flags
        self.value = value

class ParsingNodeCatchStatement(ParsingNode):
    pass