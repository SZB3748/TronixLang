import json
import os
from typing import Any, Callable, Self

class JsonProxyNode:
    def __init__(self, path:list[str|int], root:"JsonProxyRoot", parent:"JsonProxyNode", inner:dict[str]|list=None):
        self.path = path
        self.root = root
        self.parent = parent
        self.inner = inner

    def resolve(self):
        data, updated = self.root.get_data()
        if updated or self.inner is None:
            c = data
            for k in self.path:
                c = data[k]
            self.inner = c
            return c
        else:
            return self.inner

    def getchild(self, key:str|int)->"str|int|float|bool|None|JsonProxyNode":
        c = self.resolve()
        value = c[key]
        if isinstance(value, (dict,list)):
            return JsonProxyNode([*self.path, key], self.root, self, value)
        return value

    def setchild(self, key:str|int, value:"str|int|float|bool|None|dict|list|JsonProxyNode"):
        if isinstance(value, JsonProxyNode):
            value = value.resolve()
        c = self.resolve()
        c[key] = value
        self.root.mark_updated([*self.path, key], path_is_kept=True)
    
    def delchild(self, key:str|int)->str|int|float|bool|None|dict|list:
        c = self.resolve()
        value = c.pop(key)
        self.root.mark_updated([*self.path, key], path_is_kept=False)
        return value

class _schema_match_node:
    def __init__(self, segment:str|int|None, t:type|None=None):
        self.segment = segment
        self.children:dict[str|int|None, Self] = {}
        self.t = t

class JsonProxySchema:
    def __init__(self):
        self._root:dict[str|int|None, _schema_match_node] = {}

    def add_path(self, path:list[str|int|None], t:type):
        d = self._root
        for segment in path:
            node = d.get(segment, None)
            if node is None:
                node = d[segment] = _schema_match_node(segment)
            d = node.children
        if node.t is None:
            node.t = t
        return node.t
    
    def match_path(self, path:list[str|int]):
        node = None
        d = self._root
        for segment in path:
            node = d.get(segment, None)
            if node is None:
                node = d.get(None, None)
                if node is None:
                    return None
            d = node.children
        if node is None:
            return None
        return node.t

class JsonProxyRoot:
    def __init__(self, path:str, buffer:bool=True, mtimefunc:Callable[[],int]|None=None, loadfunc:Callable[[],Any]|None=None, savefunc:Callable[[Any],bool]|None=None, schema:JsonProxySchema|None=None):
        self.path = path
        self.buffer = buffer
        self.mtimefunc = mtimefunc
        self.loadfunc = loadfunc
        self.savefunc = savefunc
        self.schema = JsonProxySchema() if schema is None else schema
        self._cached = None
        self._last_updated = None
        self._pending_updates:list[tuple[bool, list[str|int]]] = []

    def _get_mtime(self):
        if self.mtimefunc is None:
            return os.stat(self.path).st_mtime_ns
        else:
            return self.mtimefunc()
        
    def getchild(self, key:str|int)->"str|int|float|bool|None|JsonProxyNode":
        c, _ = self.get_data()
        value = c[key]
        if isinstance(value, (dict,list)):
            return JsonProxyNode([key], self, None, value)
        return value

    def setchild(self, key:str|int, value:"str|int|float|bool|None|dict|list|JsonProxyNode"):
        if isinstance(value, JsonProxyNode):
            value = value.resolve()
        c, _ = self.get_data()
        c[key] = value
        self.mark_updated([key], path_is_kept=True)
    
    def delchild(self, key:str|int)->str|int|float|bool|None|dict|list:
        c, _ = self.get_data()
        value = c.pop(key)
        self.mark_updated([key], path_is_kept=False)
        return value

    def get_data(self):
        lu = self._last_updated
        mtime = self._get_mtime()
        if mtime != self._last_updated:
            self.merge_changes(mtime=mtime)
        return self._cached, lu != self._last_updated

    def merge_changes(self, mtime:int=None):
        if mtime is None:
            mtime = self._get_mtime()
        if mtime != self._last_updated:
            self._last_updated = mtime
            if self.loadfunc is None:
                with open(self.path) as f:
                    new = json.load(f)
            else:
                new = self.loadfunc()
            if self.buffer and self._pending_updates:
                pending = _make_update_tree(self._cached)
                _recursive_update(pending, self._cached, new)
            self._cached = new

        if self.savefunc is None:
            c = json.dumps(self._cached)
            with open(self.path, "w") as f:
                f.write(c)
            saved = True
        else:
            saved = self.savefunc(self._cached)
        if saved:
            self._last_updated = self._get_mtime()
        
        self._pending_updates.clear()

    def mark_updated(self, path:list[str|int], path_is_kept:bool=True):
        if path:
            self._pending_updates.append((path_is_kept, path))


class update_node:
    def __init__(self, key:str, children:dict[str|int,Self], kept:bool=True):
        self.key = key
        self.children = children
        self.kept = kept

def _make_update_tree(updates:list[tuple[bool, list[str|int]]]):
    main_branches:dict[str,update_node] = {}

    for update in updates:
        u, (pkey, *keys) = update

        branch = main_branches.get(pkey,None)
        if branch is None:
            branch = main_branches[pkey] = update_node(pkey, {})
        
        for key in keys:
            child = branch.children.get(key,None)
            if child is None:
                branch = branch.children[key] = update_node(key, {})
            else:
                branch = child
        
        if not u:
            branch.kept = False
    return update_node("", main_branches)

def _recursive_update(node:update_node, old:dict[str]|list, new:dict[str]|list):
    if type(new) != type(old):
        return
    if isinstance(new, dict):
        for key, child in node.children.items():
            if not child.kept:
                if key in new:
                    del new[key]
            elif child.children:
                _recursive_update(child, old[key], new[key])
            else:
                new[key] = old[key]
    elif isinstance(new, list):
        for index, child in node.children.items():
            if not child.kept:
                new.clear()
                new.extend(old)
                return
            elif child.children:
                _recursive_update(child, old[index], new[index])
            elif index < len(new):
                new[index] = old[index]
            elif index == len(new):
                new.append(old[index])
            else:
                new.extend(None for _ in range(len(new)-index))
                new.append(old[index])