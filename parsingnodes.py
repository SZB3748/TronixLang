from typing import Any
from re import Match

class ParsingNode:
    def __init__(self, match:Match|None, parent:"ParsingNode|None"=None, children:list["ParsingNode"]|None=None):
        self.parent = parent
        self.children = [] if children is None else children
        self.match = match

class ParsingNode_Terminating(ParsingNode):
    def __init__(self, match:Match, parent:ParsingNode|None=None):
        super().__init__(match, parent, None)

class ParsingNodeExpression(ParsingNode):
    pass

class ParsingNodeName(ParsingNode_Terminating):
    def __init__(self, name:str, match:Match, parent:ParsingNode|None=None):
        super().__init__(match, parent)
        self.name = name

class ParsingNodeFunction(ParsingNode):
    def __init__(self, function_name:str, match:Match, parent:ParsingNode|None=None, parameters:list[ParsingNode]|None=None):
        super().__init__(match, parent, parameters)
        self.function_name = function_name

class ParsingNodeValue(ParsingNode_Terminating):
    def __init__(self, value:Any, match:Match, parent:ParsingNode|None=None):
        super().__init__(match, parent)
        self.value = value

class ParsingNodeParentheses(ParsingNode):
    pass

class ParsingNodeCodeBlock(ParsingNode):
    pass

class ParsingNodeComma(ParsingNode_Terminating):
    pass

class ParsingNodeOperator(ParsingNode_Terminating):
    def __init__(self, operator:str, match:Match, parent:ParsingNode|None=None):
        super().__init__(match, parent)
        self.operator = operator

class ParsingNodeIfStatement(ParsingNode):
    pass

class ParsingNodeConditionPair(ParsingNode):
    def __init__(self, match:Match, parent:ParsingNodeIfStatement|None, condition:ParsingNodeExpression|ParsingNodeParentheses|None=None, codeblock:ParsingNodeCodeBlock|None=None, takes_condition:bool=False):
        super().__init__(match, parent, [])
        self.takes_condition = takes_condition
        self.condition = condition
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
    def __init__(self, match:Match, parent:ParsingNode|None=None, name:ParsingNodeName|None=None, value:ParsingNodeExpression|ParsingNodeParentheses|None=None):
        super().__init__(match, parent, [])
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

class ParsingNodeGlobalStatement(ParsingNode):
    def __init__(self, match:Match, parent:ParsingNode|None=None, name:ParsingNodeName|None=None):
        super().__init__(match, parent, [])
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