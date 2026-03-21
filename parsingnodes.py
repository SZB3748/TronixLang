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

class ParsingNodeName(ParsingNode):
    def __init__(self, name:str, match:Match, parent:ParsingNode|None=None, children:list[ParsingNode]|None=None):
        super().__init__(match, parent, children)
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

class ParsingNodeComma(ParsingNode_Terminating):
    pass

class ParsingNodeOperator(ParsingNode_Terminating):
    def __init__(self, operator:str, match:Match, parent:ParsingNode|None=None):
        super().__init__(match, parent)
        self.operator = operator