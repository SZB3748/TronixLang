from script import *
from exceptions import *

def generate_exception_help(raw:str, e:TronixException)->str:
    s = []
    if isinstance(e, TParsingException):
        ...
    elif isinstance(e, TCompilationException):
        ...
    elif isinstance(e, TRuntimeException):
        ...
    return "".join(s)

class ScriptRunner:
    def __init__(self):
        self.parse_trees:dict[bytes, ParsingNode] = {}

    def _prep(self, script:Script|str, force_parse:bool, force_compile:bool):
        if isinstance(script, str):
            script = Script(script)
        if force_parse:
            p = self.parse_trees[script._hash] = script.parse()
        else:
            p = self.parse_trees.get(script._hash, None)
            if p is None:
                p = self.parse_trees[script._hash] = script.parse()
                script.compile(p)

        if force_compile or not script.steps:
            script.compile(p)
        
        return script

    def run_iter(self, script:Script|str, force_parse:bool=False, force_compile:bool=False):
        script = self._prep(script, force_parse, force_compile)
        
        for step in script.steps:
            yield step()
    

    def run(self, script:Script|str, force_parse:bool=False, force_compile:bool=False):
        script = self._prep(script, force_parse, force_compile)

        for step in script.steps:
            step()
        