import ply.lex as lex

KEYWORDS = {
    "program": "PROGRAM",
    "end": "END",
    "integer": "INTEGER",
    "real": "REAL",
    "logical": "LOGICAL",
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "endif": "ENDIF",
    "do": "DO",
    "continue": "CONTINUE",
    "goto": "GOTO",
    "read": "READ",
    "write": "WRITE",
    "print": "PRINT",
}

tokens = list(KEYWORDS.values()) + [
    "ID",
    "INT_LITERAL",
    "REAL_LITERAL",
    "STRING_LITERAL",
    "EQ_OP",
    "NE_OP",
    "LT_OP",
    "LE_OP",
    "GT_OP",
    "GE_OP",
    "AND_OP",
    "OR_OP",
    "NOT_OP",
    "TRUE_LITERAL",
    "FALSE_LITERAL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "ASSIGN",
    "LPAREN",
    "RPAREN",
    "COMMA",
]

t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_ASSIGN = r"="
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_COMMA = r","


t_ignore = " \t\r"


def t_COMMENT(t):
    r"![^\n]*"
    pass


def t_TRUE_LITERAL(t):
    r"\.[Tt][Rr][Uu][Ee]\."
    t.value = True
    return t


def t_FALSE_LITERAL(t):
    r"\.[Ff][Aa][Ll][Ss][Ee]\."
    t.value = False
    return t


def t_EQ_OP(t):
    r"\.[Ee][Qq]\."
    return t


def t_NE_OP(t):
    r"\.[Nn][Ee]\."
    return t


def t_LT_OP(t):
    r"\.[Ll][Tt]\."
    return t


def t_LE_OP(t):
    r"\.[Ll][Ee]\."
    return t


def t_GT_OP(t):
    r"\.[Gg][Tt]\."
    return t


def t_GE_OP(t):
    r"\.[Gg][Ee]\."
    return t


def t_AND_OP(t):
    r"\.[Aa][Nn][Dd]\."
    return t


def t_OR_OP(t):
    r"\.[Oo][Rr]\."
    return t


def t_NOT_OP(t):
    r"\.[Nn][Oo][Tt]\."
    return t


def t_REAL_LITERAL(t):
    r"([0-9]+\.[0-9]*|\.[0-9]+)([Ee][+-]?[0-9]+)?"
    t.value = float(t.value)
    return t


def t_INT_LITERAL(t):
    r"[0-9]+"
    t.value = int(t.value)
    return t


def t_STRING_LITERAL(t):
    r"'([^'\n]|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_ID(t):
    r"[A-Za-z][A-Za-z0-9_]*"
    lowered = t.value.lower()
    t.type = KEYWORDS.get(lowered, "ID")
    t.value = t.value.upper()
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    if not hasattr(t.lexer, "errors"):
        t.lexer.errors = []
    t.lexer.errors.append(
        f"Lexical error at line {t.lineno}: illegal character '{t.value[0]}'"
    )
    t.lexer.skip(1)


def build_lexer(**kwargs):
    lexer_instance = lex.lex(**kwargs)
    lexer_instance.errors = []
    return lexer_instance


lexer = build_lexer()
