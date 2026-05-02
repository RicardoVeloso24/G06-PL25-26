class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.labels_defined = set()
        self.labels_used = set()

    def analyze(self, ast):
        if ast[0] != 'program':
            self.errors.append("Programa inválido.")
            return

        _, prog_name, body = ast

        self.visit_declarations(body['declarations'])
        self.visit_statements(body['statements'])

        self.check_labels()

    # -------------------------
    # DECLARAÇÕES
    # -------------------------
    def visit_declarations(self, declarations):
        for decl in declarations:
            _, var_type, vars_list = decl

            for var in vars_list:
                if var in self.symbol_table:
                    self.errors.append(f"Variável '{var}' redeclarada.")
                else:
                    self.symbol_table[var] = {
                        'type': var_type,
                        'initialized': False
                    }

    # -------------------------
    # STATEMENTS
    # -------------------------
    def visit_statements(self, statements):
        for stmt in statements:
            self.visit_statement(stmt)

    def visit_statement(self, stmt):
        kind = stmt[0]

        if kind == 'assign':
            self.visit_assign(stmt)

        elif kind == 'if-then':
            self.visit_expression(stmt[1])
            self.visit_statements(stmt[2])

        elif kind == 'if-then-else':
            self.visit_expression(stmt[1])
            self.visit_statements(stmt[2])
            self.visit_statements(stmt[3])

        elif kind == 'do-loop':
            self.visit_do(stmt)

        elif kind == 'goto':
            self.labels_used.add(stmt[1])

        elif kind == 'label':
            self.labels_defined.add(stmt[1])
            self.visit_statement(stmt[2])

        elif kind in ['read', 'write', 'print']:
            self.visit_expression(stmt[1])

    # -------------------------
    # ASSIGN
    # -------------------------
    def visit_assign(self, stmt):
        _, var, expr = stmt

        if var not in self.symbol_table:
            self.errors.append(f"Variável '{var}' não declarada.")
            return

        expr_type = self.visit_expression(expr)
        var_type = self.symbol_table[var]['type']

        if not self.type_compatible(var_type, expr_type):
            self.errors.append(
                f"Incompatibilidade de tipos: '{var}' é {var_type}, recebeu {expr_type}"
            )

        self.symbol_table[var]['initialized'] = True

    # -------------------------
    # EXPRESSÕES
    # -------------------------
    def visit_expression(self, expr):
        kind = expr[0]

        if kind == 'leaf':
            value = expr[1]

            if isinstance(value, int):
                return 'INTEGER'

            elif isinstance(value, float):
                return 'REAL'

            elif value in ['.TRUE.', '.FALSE.']:
                return 'LOGICAL'

            elif isinstance(value, str):
                if value in self.symbol_table:
                    return self.symbol_table[value]['type']
                else:
                    return 'STRING'

        elif kind == 'binop':
            left = self.visit_expression(expr[2])
            right = self.visit_expression(expr[3])

            if left == 'REAL' or right == 'REAL':
                return 'REAL'
            return 'INTEGER'

        elif kind == 'unop':
            return self.visit_expression(expr[2])

        return 'UNKNOWN'

    # -------------------------
    # DO LOOP
    # -------------------------
    def visit_do(self, stmt):
        _, label, var, start, end = stmt

        self.labels_used.add(label)

        if var not in self.symbol_table:
            self.errors.append(f"Variável de controlo '{var}' não declarada.")

        self.visit_expression(start)
        self.visit_expression(end)

    # -------------------------
    # LABELS
    # -------------------------
    def check_labels(self):
        for label in self.labels_used:
            if label not in self.labels_defined:
                self.errors.append(f"Label {label} usada mas não definida.")

    # -------------------------
    # TIPOS
    # -------------------------
    def type_compatible(self, var_type, expr_type):
        if var_type == expr_type:
            return True

        if var_type == 'REAL' and expr_type == 'INTEGER':
            return True

        return False

    # -------------------------
    def get_errors(self):
        return self.errors

    def get_symbol_table(self):
        return self.symbol_table