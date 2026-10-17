import string
import sys

class _chartree:
    __slots__ = "c", "substr", "children", "tail"

    @classmethod
    def new(cls, *values:str):
        root = cls("", "", {})
        root.add(*values)
        return root

    def __init__(self, c:str, substr:str, children:"dict[str, _chartree]", tail:bool=False):
        self.c = c
        self.substr = substr
        self.children = children
        self.tail = tail

    def add(self, *values:str):
        cls = type(self)
        for value in values:
            if not value:
                continue
            c = value[0]
            cx = value[1:]
            child = self.children.get(c, None)
            if child is None:
                child = self.children[c] = cls(c, self.substr + c, {})
            if cx:
                child.add(cx)
            else:
                child.tail = True

    def match(self, value:str):
        node = self
        for c in value:
            node = node.children.get(c,None)
            if node is None:
                return False

    def follow(self, value:str, i:int=0):
        last_tail = None
        node = self
        while i < len(value):
            child = node.children.get(value[i],None)
            if child is None:
                if node.tail:
                    return node.substr
                return None
            node = child
            if node.tail:
                last_tail = node.substr
            i += 1
        return last_tail

class MatcherResult:
    def __init__(self, name:str, resume:int, matched:"str|list[MatcherResult]|None"=None, fail:bool=False):
        self.name = name
        self.resume = resume
        self.matched = matched
        self.fail = fail

    def get_matched_str(self):
        if self.matched is None:
            return ""
        elif isinstance(self.matched, str):
            return self.matched
        else:
            return "".join(m.get_matched_str() for m in self.matched)
    

class Matcher:
    def __init__(self, name:str, *submatchers:"Matcher"):
        self.name = name
        self.submatchers = list(submatchers)

    def match(self, match_start:int, source:str, parent:"Matcher|None")->MatcherResult:
        results = []
        i = match_start
        for matcher in self.submatchers:
            print(i, self, self.name, matcher, matcher.name)
            try:
                result = matcher.match(i, source, self)
            except RecursionError:
                input("")
                raise
            if result.fail:
                return MatcherResult(self.name, match_start, results, fail=True)
            results.append(result)
            i = result.resume
        return MatcherResult(self.name, i, results)

class MatcherAny(Matcher):
    def match(self, match_start, source, parent):
        for matcher in self.submatchers:
            result = matcher.match(match_start, source, self)
            if not result.fail:
                return result
        return MatcherResult(self.name, match_start, fail=True)

class MatcherNTimes(Matcher):
    def __init__(self, name:str, *submatchers:Matcher, min:int=0, max:int=sys.maxsize):
        super().__init__(name, *submatchers)
        self.min = min
        self.max = max

    def match(self, match_start, source, parent):
        results = []
        current_start = match_start
        while len(results) < self.max:
            result = super().match(current_start, source, self)
            if result.fail:
                break
            results.append(results)
            current_start = result.resume
        matches = len(results)
        if matches < self.min:
            return MatcherResult(self.name, match_start, results, fail=True)
        else:
            return MatcherResult(self.name, current_start, results)

class MatchEnclose(Matcher):
    def __init__(self, name:str, start:str, stop:str, *submatchers:Matcher, balanced:bool=True):
        super().__init__(name, *submatchers)
        self.start = start
        self.stop = stop
        self.balanced = balanced

    def match(self, match_start, source, parent):
        if not source.startswith(self.start):
            return MatcherResult(self.name, match_start, fail=True)
        result = super().match(match_start + len(self.start), source, self)
        if result.fail:
            return MatcherResult(self.name, match_start, fail=True)
        i = result.resume
        if parent[i:i+len(self.stop)] != self.stop:
            return MatcherResult(self.name, match_start, [result], fail=True)
        if self.balanced:
            s = result.get_matched_str()
            if s.count(self.start) != s.count(self.stop):
                return MatcherResult(self.name, match_start, fail=True)
        return MatcherResult(self.name, match_start, [result])

class LiteralMatcher(Matcher):
    def __init__(self, name:str, *values:str):
        super().__init__(name)
        self.lookup = _chartree.new(*values)

    def match(self, match_start, source, parent):
        found = self.lookup.follow(source, i=match_start)
        if found is None:
            return MatcherResult(self.name, match_start, fail=True)
        return MatcherResult(self.name, match_start + len(found), found)

class CharsetMatcher(Matcher):
    def __init__(self, name:str, charset:str, min_matches:int=1, max_matches:int|None=None, not_match:bool=False):
        super().__init__(name)
        self.charset = charset
        self.min_matches = min_matches
        self.max_matches = max_matches
        self.not_match = not_match

    def match(self, match_start, source, parent):
        i = match_start
        if self.max_matches is None:
            limit = len(source)
        else:
            limit = min(i+self.max_matches, len(source))
        if self.not_match:
            while i < limit:
                c = source[i]
                if c not in self.charset:
                    i += 1
                else:
                    return MatcherResult(self.name, match_start, fail=True)
        else:
            while i < limit:
                c = source[i]
                if c in self.charset:
                    i += 1
                else:
                    return MatcherResult(self.name, match_start, fail=True)
        return MatcherResult(self.name, i, source[match_start:i])

def surround(name:str, p:str, *matchers, balanced:bool=True):
    return MatchEnclose(name, p[0], p[1], *matchers, balanced=balanced)


NEWLINE = LiteralMatcher("NEWLINE", "\r\n", "\n")
SPACE = CharsetMatcher("SPACE", " \t\v\f")
SPACE_optional = CharsetMatcher("SPACE", SPACE.charset, min_matches=0)
WHITESPACE = CharsetMatcher("WHITESPACE", string.whitespace)
WHITESPACE_optional = CharsetMatcher("WHITESPACE", WHITESPACE.charset, min_matches=0)

name_first_charset = string.ascii_lowercase+string.ascii_uppercase+"_"
name_charset = name_first_charset + string.digits

#forward declaration
EXPRESSION = Matcher("EXPRESSION")
CODE = Matcher("CODE")

NAME = Matcher("NAME", CharsetMatcher("", name_first_charset, max_matches=1), CharsetMatcher("", name_charset, min_matches=0))
BINOP_ADD = LiteralMatcher("BINOP_ADD", *"+-")
BINOP_MLT = LiteralMatcher("BINOP_MLT", *"*/%")
BINOP_CMP = LiteralMatcher("BINOP_CMP", *"><", ">=", "<=", "==", "!=")
BINOP_ASSIGN = LiteralMatcher("BINOP_ASSIGN", "+=", "-=", "*=", "/=", "%=", "=")
BINOP_LOG = LiteralMatcher("BINOP_LOG", "and", "or")
BINARY_OPERATOR = MatcherAny("BINARY_OPERATOR", BINOP_ADD, BINOP_MLT, BINOP_CMP, BINOP_ASSIGN, BINOP_LOG)
ULEFT_OPERATOR = LiteralMatcher("ULEFT_OPERATOR", "not", *"+-")
COLON = LiteralMatcher("COLON", ":")
SEMICOLON = LiteralMatcher("SEMICOLON", ";")
COMMA = LiteralMatcher("COMMA", ",")
DOT = LiteralMatcher("DOT", ".")
INTEGER = CharsetMatcher("INTEGER", string.digits)
FLOAT = Matcher("FLOAT", CharsetMatcher("", string.digits, min_matches=0), LiteralMatcher("", "."), CharsetMatcher("", string.digits))
STRING_START = Matcher("STRING_START", MatcherNTimes("FORMAT", LiteralMatcher("", "f"), max=1), CharsetMatcher("", "'\"", max_matches=1))
STRING_ESCAPE = LiteralMatcher("STRING_ESCAPE", "\\\"", "\\'")
STRING_END = CharsetMatcher("STRING_END", "'\"", max_matches=1)
STRING_CONTENTS = Matcher("STRING_CONTENTS", MatcherNTimes("", MatcherAny("", STRING_ESCAPE, CharsetMatcher("", STRING_END.charset, not_match=True))))
STRING_LITERAL = Matcher("STRING_LITERAL", STRING_START, STRING_CONTENTS, STRING_END)
IF = LiteralMatcher("IF", "if")
ELSE = LiteralMatcher("ELSE", "else")
ELIF = Matcher("ELIF", ELSE, SPACE, IF)
LOOP = LiteralMatcher("LOOP", "loop")
CATCH = LiteralMatcher("CATCH", "catch")
GLOBAL = LiteralMatcher("GLOBAL", "global")
VAR = LiteralMatcher("VAR", "var")
DEFINE = LiteralMatcher("DEFINE", "define")
BREAK = LiteralMatcher("BREAK", "break")
SKIP = LiteralMatcher("SKIP", "skip")
DELETE = LiteralMatcher("DELETE", "delete")
NULL = LiteralMatcher("NULL", "null")
BOOLEAN = LiteralMatcher("BOOLEAN", "true", "false")
# BRACKET_BEGIN = LiteralMatcher("BRACKET_BEGIN", "[")
# BRACKET_END = LiteralMatcher("BRACKET_END", "]")
# PARENTHESIS_BEGIN = LiteralMatcher("PARENTHESIS_BEGIN", "(")
# PARENTHESIS_END = LiteralMatcher("PARENTHESIS_END", ")")
# BRACE_BEGIN = LiteralMatcher("BRACE_BEGIN", "{")
# BRACE_END = LiteralMatcher("BRACE_END", "}")
NON_NUMERIC_LITERAL = MatcherAny("NON_NUMERIC_LITERAL", MatcherAny("", NULL, BOOLEAN, STRING_LITERAL))
NUMERIC_LITERAL = MatcherAny("NUMERIC_LITERAL", FLOAT, INTEGER)
LITERAL = MatcherAny("LITERAL", NON_NUMERIC_LITERAL, NUMERIC_LITERAL)

def MatcherP[T:Matcher](op:T):
    return surround(f"{op.name}P", "()", WHITESPACE_optional, op, WHITESPACE_optional)

def MatcherX[T:Matcher,U:Matcher](opp:T, op:U):
    return MatcherAny(f"{op.name}X", opp, op)

NVPAIR = Matcher("NVPAIR", NAME, WHITESPACE_optional, COLON, WHITESPACE_optional, EXPRESSION)
VALUE = MatcherAny("VALUE", LITERAL, NVPAIR, NAME)
NNVALUE = MatcherAny("NNVALUE", NON_NUMERIC_LITERAL, NAME)
EXPRESSIONP = MatcherP(EXPRESSION)
EXPRESSIONX = MatcherX(EXPRESSIONP, EXPRESSION)
SUBSCRIPT = surround("SUBSCRIPT", "[]", WHITESPACE_optional, EXPRESSIONX, WHITESPACE_optional)
FUNCTION_CALL = Matcher(
    NAME, SPACE_optional, surround(
        "", "()",
        WHITESPACE_optional,
        MatcherNTimes(
            "FUNCTION_CALL_ARGUMENTS",
            EXPRESSIONX, MatcherNTimes("", WHITESPACE_optional, COMMA, WHITESPACE_optional, EXPRESSIONX),
            MatcherNTimes("", WHITESPACE_optional, COMMA, max=1),
            max=1
        ),
        WHITESPACE_optional
    ))
EVALUE = MatcherAny("EVALUE", FUNCTION_CALL, VALUE)
ENNVALUE = MatcherAny("ENNVALUE", FUNCTION_CALL, NNVALUE)
EVALUEP = MatcherP(EVALUE)
EVALUEX = MatcherX(EVALUEP, EVALUE)
LOOKUP_CHAIN = MatcherAny("LOOKUP_CHAIN", SUBSCRIPT, Matcher("ATTRIBUTE", SPACE, DOT, WHITESPACE_optional, NAME))

OP_P1 = MatcherAny(
    "OP_P1",
    Matcher("", MatcherAny("", EVALUEP, ENNVALUE), MatcherNTimes("", LOOKUP_CHAIN, min=1)),
    Matcher("", NUMERIC_LITERAL, SUBSCRIPT, MatcherNTimes("", LOOKUP_CHAIN, min=1))
)
OP_P1P = MatcherP(OP_P1)
OP_P1X = MatcherX(OP_P1P, OP_P1)

OP_P2 = MatcherAny(
    "OP_P2",
    Matcher("", DELETE, SPACE, MatcherAny("", OP_P1, NAME)),
    Matcher("", ULEFT_OPERATOR, WHITESPACE_optional, MatcherAny("", OP_P1X, EVALUEX))
)
OP_P2P = MatcherP(OP_P2)
OP_P2X = MatcherX(OP_P2P, OP_P2)

OP_P3 = Matcher("OP_P3")
OP_P3P = MatcherP(OP_P3)
OP_P3X = MatcherX(OP_P3P, OP_P3)
OP_P3.submatchers.extend([
    MatcherAny("", OP_P2X, OP_P3X, EVALUEX),
    WHITESPACE_optional, BINOP_MLT, WHITESPACE_optional,
    MatcherAny("", OP_P2X, EVALUEX)
])

OP_P4 = Matcher("OP_P4")
OP_P4P = MatcherP(OP_P4)
OP_P4X = MatcherX(OP_P4P, OP_P4)
OP_P4.submatchers.extend([
    MatcherAny("", OP_P3X, OP_P4X, EVALUEX),
    WHITESPACE_optional, BINOP_ADD, WHITESPACE_optional,
    MatcherAny("", OP_P3X, EVALUEX)
])

OP_P5 = Matcher("OP_P5")
OP_P5P = MatcherP(OP_P5)
OP_P5X = MatcherX(OP_P5P, OP_P5)
OP_P5.submatchers.extend([
    MatcherAny("", OP_P4X, OP_P5X, EVALUEX),
    WHITESPACE_optional, BINOP_CMP, WHITESPACE_optional,
    MatcherAny("", OP_P4X, EVALUEX)
])

OP_P6 = Matcher("OP_P6")
OP_P6P = MatcherP(OP_P6)
OP_P6X = MatcherX(OP_P6P, OP_P6)
OP_P6.submatchers.extend([
    MatcherAny("", OP_P5X, OP_P6X, EVALUEX),
    WHITESPACE_optional, BINOP_LOG, WHITESPACE_optional,
    MatcherAny("", OP_P5X, EVALUEX)
])

OP_P7 = Matcher("OP_P7")
OP_P7P = MatcherP(OP_P7)
OP_P7X = MatcherX(OP_P7P, OP_P7)
OP_P6.submatchers.extend([
    MatcherAny("", OP_P1, NAME),
    WHITESPACE_optional, BINOP_LOG, WHITESPACE_optional,
    MatcherAny("", OP_P6X, OP_P7X, EVALUEX)
])

OPERATION = MatcherAny("OPERATION", OP_P1, OP_P2, OP_P3, OP_P4, OP_P5, OP_P6, OP_P7)
EXPRESSION.submatchers.extend([OPERATION, EVALUE])

CODE_BLOCK = surround("CODE_BLOCK", "{}", WHITESPACE_optional, CODE, WHITESPACE_optional)

EXPRESSION_STATEMENT = Matcher("EXPRESSION_STATEMENT", MatcherAny(
    SEMICOLON,
    Matcher("", EXPRESSIONX, SPACE_optional, NEWLINE),
    Matcher("", EXPRESSIONX, WHITESPACE_optional, SEMICOLON)
))

DECLARE_STATEMENT = Matcher(
    "DECLARE_STATEMENT",
    MatcherAny("MODE", GLOBAL, VAR, DEFINE), SPACE, NAME,
    MatcherNTimes(
        "", 
        LiteralMatcher("", "="), WHITESPACE_optional, EXPRESSIONX,
        max=1
    ),
    MatcherNTimes(
        "",
        WHITESPACE_optional, COMMA, WHITESPACE_optional, NAME,
        MatcherNTimes(
            "",
            LiteralMatcher("", "="), WHITESPACE_optional, EXPRESSIONX,
            max=1
        )
    )
)

LOOP_CONTROL_STATEMENT = LiteralMatcher("LOOP_CONTROL_STATEMENT", "break", "skip")

IF_STATEMENT = Matcher(
    "IF_STATEMENT",
    IF, WHITESPACE, EXPRESSIONX, WHITESPACE_optional, CODE_BLOCK,
    MatcherNTimes(
        "",
        WHITESPACE_optional, ELIF, WHITESPACE, EXPRESSIONX,
        WHITESPACE_optional, CODE_BLOCK
    ),
    MatcherNTimes(
        "",
        WHITESPACE_optional, ELSE, WHITESPACE_optional, CODE_BLOCK,
        max=1
    )
)

LOOP_STATEMENT = Matcher(
    "LOOP_STATEMENT",
    LOOP, WHITESPACE, EXPRESSIONX,
    MatcherNTimes(
        "",
        WHITESPACE_optional, SEMICOLON, WHITESPACE_optional, EXPRESSIONX
    ),
    WHITESPACE_optional,
    CODE_BLOCK
)

CATCH_STATEMENT = Matcher(
    "CATCH_STATEMENT",
    CATCH, MatcherNTimes("", WHITESPACE_optional, NAME, max=1),
    WHITESPACE_optional, CODE_BLOCK
)

STATEMENT = MatcherAny(
    "STATEMENT",
    DECLARE_STATEMENT, LOOP_CONTROL_STATEMENT, IF_STATEMENT,
    LOOP_STATEMENT, CATCH_STATEMENT, EXPRESSION_STATEMENT
)

CODE.submatchers.extend([
    MatcherAny("", CODE_BLOCK, STATEMENT),
    MatcherNTimes("", WHITESPACE_optional, MatcherAny("", CODE_BLOCK, STATEMENT))
])