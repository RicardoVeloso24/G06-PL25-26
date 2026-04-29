import ply.yacc as yacc
from lexer import tokens

#Precedence rules for operators (from highest to lowest)
precedence = (
    #rever repetição das precedências EQ_OP e NE_OP *)
    ('left', 'EQ_OP', 'NE_OP'),
    ('left', 'OR_OP'),
    ('left', 'AND_OP'),
    ('right', 'NOT_OP'),
    ('nonassoc', 'LT_OP', 'LE_OP', 'GT_OP', 'GE_OP'), # 'EQ_OP', 'NE_OP'),*)
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'), # menos unário (ex.: -5) //necessário preparar no módulo lexer.py
    #('right', 'POWER'),  #necessário preparar no módulo lexer)
)

# BNF Grammar definition
def p_program(p):
    'program : PROGRAM ID body END'
    p[0] = ('program', p[2], p[3])

def p_body(p):
    'body : declarations statements'
    p[0] = {'declarations': p[1], 'statements': p[2]}

#Variable Declarations
def p_declarations(p):
    '''declarations : declaration declarations
                    | empty'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_declaration(p):
    'declaration : type id_list'
    p[0] = ('decl', p[1], p[2])

def p_type(p):
    '''type : INTEGER
            | REAL
            | LOGICAL'''
    p[0] = p[1]

def p_id_list(p):
    '''id_list : ID COMMA id_list
               | ID'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

#Statements
def p_statements(p): 
    '''statements : statement statements
                  | empty'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_statement(p):
    '''statement : assignment
                 | if_stmt
                 | do_stmt
                 | goto_stmt
                 | io_stmt
                 | label_stmt
                 | continue_stmt'''
    p[0] = p[1]

# Assignment (=)
def p_assignment(p):
    'assignment : ID ASSIGN expression'
    p[0] = ('assign', p[1], p[3])

# Estruturas de Controlo: IF-THEN-ELSE 
def p_if_stmt(p):
    '''if_stmt : IF LPAREN expression RPAREN THEN statements ELSE statements ENDIF
               | IF LPAREN expression RPAREN THEN statements ENDIF'''
    if len(p) == 10:
        p[0] = ('if-then-else', p[3], p[6], p[8])
    else:
        p[0] = ('if-then', p[3], p[6])

# Estruturas de Controlo: DO (Ciclo) 
def p_do_stmt(p):
    'do_stmt : DO INT_LITERAL ID ASSIGN expression COMMA expression' # Fortran 77: DO label var = start, end
    p[0] = ('do-loop', p[2], p[3], p[5], p[7])

# GOTO e Labels
def p_goto_stmt(p):
    'goto_stmt : GOTO INT_LITERAL'
    p[0] = ('goto', p[2])

def p_label_stmt(p):
    'label_stmt : INT_LITERAL statement'
    p[0] = ('label', p[1], p[2])

def p_continue_stmt(p):
    'continue_stmt : CONTINUE' 
    p[0] = ('continue',)

# IO
def p_io_stmt(p):
    '''io_stmt : READ format_spec expression
               | WRITE format_spec expression
               | PRINT format_spec expression
               | READ expression
               | WRITE expression
               | PRINT expression'''
    if len(p) == 4:
        p[0] = (p[1].lower(), p[3])
    else:
        p[0] = (p[1].lower(), p[2])

def p_format_spec(p):
    '''format_spec : TIMES COMMA
                   | TIMES'''
    p[0] = '*'

# Arithmetic and Logical Expressions 
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression AND_OP expression
                  | expression OR_OP expression
                  | expression LT_OP expression
                  | expression LE_OP expression
                  | expression GT_OP expression
                  | expression GE_OP expression
                  | expression EQ_OP expression
                  | expression NE_OP expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_unop(p):
    '''expression : MINUS expression %prec UMINUS
                  | NOT_OP expression'''
    p[0] = ('unop', p[1], p[2])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_factor(p):
    '''expression : ID
                  | INT_LITERAL
                  | REAL_LITERAL
                  | TRUE_LITERAL
                  | FALSE_LITERAL
                  | STRING_LITERAL'''
    p[0] = ('leaf', p[1])

# Empty production for recursion
def p_empty(p):
    'empty :'
    pass

# Syntax Errors
def p_error(p):
    if p:
        print(f"Syntax Error: unexpected token '{p.value}' (line {p.lineno})")
    else:
        print("Syntax Error: unexpected end of file")


parser = yacc.yacc()

def parse(data):
    return parser.parse(data)