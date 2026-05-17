class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.labels_defined = set()
        self.labels_used = set()
        self.do_labels_used = set()
        self.continue_labels = set()

    def analyze(self, ast):
        if not ast or ast[0] != "program":
            self.add_error("Programa invalido.")
            return

        _, prog_name, body = ast

        self.visit_declarations(body["declarations"])
        self.visit_statements(body["statements"])
        self.check_labels()

    def add_error(self, message):
        if message not in self.errors:
            self.errors.append(message)

    def visit_declarations(self, declarations):
        for decl in declarations:
            _, var_type, vars_list = decl

            for var in vars_list:
                name, kind, size = self.normalize_declaration_item(var)

                if name in self.symbol_table:
                    self.add_error(f"Variavel '{name}' redeclarada.")
                else:
                    if kind == "array" and size <= 0:
                        self.add_error(f"Array '{name}' tem dimensao invalida.")

                    self.symbol_table[name] = {
                        "type": var_type,
                        "kind": kind,
                        "size": size,
                        "initialized": False,
                    }

    def visit_statements(self, statements):
        for stmt in statements:
            self.visit_statement(stmt)

    def visit_statement(self, stmt):
        kind = stmt[0]

        if kind == "assign":
            self.visit_assign(stmt)

        elif kind == "if-then":
            self.visit_if(stmt[1], stmt[2])

        elif kind == "if-then-else":
            self.visit_if(stmt[1], stmt[2], stmt[3])

        elif kind == "do-loop":
            self.visit_do(stmt)

        elif kind == "goto":
            self.labels_used.add(stmt[1])

        elif kind == "label":
            self.visit_label(stmt)

        elif kind == "read":
            self.visit_read(stmt)

        elif kind in ["write", "print"]:
            self.visit_output(stmt)

        elif kind == "continue":
            return

        else:
            self.add_error(f"Instrucao desconhecida: {kind}.")

    def visit_assign(self, stmt):
        _, var, expr = stmt
        target_type = self.visit_assignment_target(var)
        expr_type = self.visit_expression(expr)

        if target_type != "UNKNOWN" and expr_type != "UNKNOWN" and not self.type_compatible(target_type, expr_type):
            var_name = self.extract_variable_name(var)
            self.add_error(
                f"Incompatibilidade de tipos: '{var_name}' e {target_type}, recebeu {expr_type}."
            )

        var_name = self.extract_variable_name(var)
        if target_type != "UNKNOWN" and var_name in self.symbol_table:
            self.symbol_table[var_name]["initialized"] = True

    def visit_if(self, condition, then_statements, else_statements=None):
        condition_type = self.visit_expression(condition)
        if condition_type != "LOGICAL":
            self.add_error("Condicao de IF tem de ser LOGICAL.")

        self.visit_statements(then_statements)

        if else_statements is not None:
            self.visit_statements(else_statements)

    def visit_do(self, stmt):
        _, label, var, start, end = stmt

        self.labels_used.add(label)
        self.do_labels_used.add(label)

        if var not in self.symbol_table:
            self.add_error(f"Variavel de controlo '{var}' nao declarada.")
        elif self.symbol_table[var]["kind"] != "scalar":
            self.add_error(f"Variavel de controlo '{var}' tem de ser escalar.")
        elif self.symbol_table[var]["type"] != "INTEGER":
            self.add_error(f"Variavel de controlo '{var}' tem de ser INTEGER.")

        start_type = self.visit_expression(start)
        end_type = self.visit_expression(end)

        if start_type not in ["INTEGER", "REAL"]:
            self.add_error("Valor inicial de DO tem de ser numerico.")

        if end_type not in ["INTEGER", "REAL"]:
            self.add_error("Valor final de DO tem de ser numerico.")

    def visit_label(self, stmt):
        _, label, inner_stmt = stmt

        if label in self.labels_defined:
            self.add_error(f"Label {label} redeclarada.")

        self.labels_defined.add(label)

        if inner_stmt[0] == "continue":
            self.continue_labels.add(label)

        self.visit_statement(inner_stmt)

    def visit_read(self, stmt):
        _, target = stmt
        targets = self.flatten_items(target)

        if not targets:
            self.add_error("READ tem de receber pelo menos uma variavel.")
            return

        for item in targets:
            target_type = self.visit_assignment_target(item)
            var_name = self.extract_variable_name(item)

            if var_name is None:
                self.add_error("READ so pode receber variaveis.")
                continue

            if target_type != "UNKNOWN" and var_name in self.symbol_table:
                self.symbol_table[var_name]["initialized"] = True

    def visit_output(self, stmt):
        _, expr = stmt
        for item in self.flatten_items(expr):
            self.visit_expression(item, allow_string=True)

    def visit_expression(self, expr, allow_string=False):
        kind = expr[0]

        if kind == "leaf":
            return self.visit_leaf(expr[1], allow_string)

        if kind == "var":
            return self.visit_variable(expr[1])

        if kind == "array_ref":
            return self.visit_array_reference(expr)

        if kind == "string":
            return "STRING"
    
        if kind == "function_call":
            return self.visit_function_call(expr)

        if kind == "binop":
            _, op, left_expr, right_expr = expr
            left_type = self.visit_expression(left_expr)
            right_type = self.visit_expression(right_expr)
            return self.check_binary_operator(op, left_type, right_type)

        if kind == "unop":
            _, op, inner_expr = expr
            inner_type = self.visit_expression(inner_expr)
            return self.check_unary_operator(op, inner_type)

        self.add_error(f"Expressao desconhecida: {kind}.")
        return "UNKNOWN"

    def visit_leaf(self, value, allow_string=False):
        if isinstance(value, bool):
            return "LOGICAL"

        if isinstance(value, int):
            return "INTEGER"

        if isinstance(value, float):
            return "REAL"

        return "UNKNOWN"

    def visit_function_call(self, expr):
        _, name, args = expr

        if name != "MOD":
            self.add_error(f"Funcao '{name}' nao suportada.")
            return "UNKNOWN"

        if len(args) != 2:
            self.add_error("Funcao MOD exige dois argumentos.")
            return "UNKNOWN"

        arg_types = [self.visit_expression(arg) for arg in args]

        if any(arg_type != "INTEGER" for arg_type in arg_types):
            self.add_error("Funcao MOD exige argumentos INTEGER.")
            return "UNKNOWN"

        return "INTEGER"


    def visit_variable(self, name):
        if name not in self.symbol_table:
            self.add_error(f"Variavel '{name}' nao declarada.")
            return "UNKNOWN"

        symbol = self.symbol_table[name]

        if symbol["kind"] == "array":
            self.add_error(f"Array '{name}' usado sem indice.")
            return "UNKNOWN"

        return symbol["type"]

    def visit_array_reference(self, expr):
        _, name, index_expr = expr

        index_type = self.visit_expression(index_expr)
        if index_type != "INTEGER":
            self.add_error(f"Indice do array '{name}' tem de ser INTEGER.")

        if name not in self.symbol_table:
            self.add_error(f"Variavel '{name}' nao declarada.")
            return "UNKNOWN"

        symbol = self.symbol_table[name]

        if symbol["kind"] != "array":
            self.add_error(f"Variavel escalar '{name}' usada como array.")
            return "UNKNOWN"

        return symbol["type"]

    def visit_assignment_target(self, target):
        if not isinstance(target, tuple):
            self.add_error("Lado esquerdo da atribuicao tem de ser uma variavel.")
            return "UNKNOWN"

        if target[0] == "var":
            name = target[1]

            if name not in self.symbol_table:
                self.add_error(f"Variavel '{name}' nao declarada.")
                return "UNKNOWN"

            symbol = self.symbol_table[name]

            if symbol["kind"] == "array":
                self.add_error(f"Array '{name}' usado sem indice.")
                return "UNKNOWN"

            return symbol["type"]

        if target[0] == "array_ref":
            return self.visit_array_reference(target)

        self.add_error("Lado esquerdo da atribuicao tem de ser uma variavel.")
        return "UNKNOWN"

    def check_binary_operator(self, op, left_type, right_type):
        arithmetic_ops = {"+", "-", "*", "/"}
        relational_ops = {".EQ.", ".NE.", ".LT.", ".LE.", ".GT.", ".GE."}
        logical_ops = {".AND.", ".OR."}

        if op in arithmetic_ops:
            if not self.is_numeric(left_type) or not self.is_numeric(right_type):
                self.add_error(f"Operador aritmetico '{op}' exige operandos numericos.")
                return "UNKNOWN"

            if left_type == "REAL" or right_type == "REAL":
                return "REAL"

            return "INTEGER"

        if op in relational_ops:
            if not self.types_comparable(left_type, right_type):
                self.add_error(f"Operador relacional '{op}' recebeu tipos incompativeis.")
            return "LOGICAL"

        if op in logical_ops:
            if left_type != "LOGICAL" or right_type != "LOGICAL":
                self.add_error(f"Operador logico '{op}' exige operandos LOGICAL.")
            return "LOGICAL"

        self.add_error(f"Operador desconhecido: {op}.")
        return "UNKNOWN"

    def check_unary_operator(self, op, inner_type):
        if op == "-":
            if not self.is_numeric(inner_type):
                self.add_error("Menos unario exige operando numerico.")
                return "UNKNOWN"
            return inner_type

        if op == ".NOT.":
            if inner_type != "LOGICAL":
                self.add_error("Operador logico '.NOT.' exige operando LOGICAL.")
            return "LOGICAL"

        self.add_error(f"Operador unario desconhecido: {op}.")
        return "UNKNOWN"

    def check_labels(self):
        for label in self.labels_used:
            if label not in self.labels_defined:
                self.add_error(f"Label {label} usada mas nao definida.")

        for label in self.do_labels_used:
            if label in self.labels_defined and label not in self.continue_labels:
                self.add_error(f"Label {label} usada em DO tem de corresponder a CONTINUE.")

    def flatten_items(self, node):
        if isinstance(node, list):
            return node

        if isinstance(node, tuple) and node and node[0] == "list":
            return node[1]

        return [node]

    def extract_variable_name(self, node):
        if isinstance(node, str):
            return node

        if isinstance(node, tuple) and len(node) == 2 and node[0] == "var":
            return node[1]

        if isinstance(node, tuple) and len(node) == 3 and node[0] == "array_ref":
            return node[1]

        return None

    def normalize_declaration_item(self, item):
        if isinstance(item, tuple) and item[0] == "array_decl":
            return item[1], "array", item[2]

        return item, "scalar", None

    def is_numeric(self, type_name):
        return type_name in ["INTEGER", "REAL"]

    def types_comparable(self, left_type, right_type):
        if left_type == "UNKNOWN" or right_type == "UNKNOWN":
            return False

        if self.is_numeric(left_type) and self.is_numeric(right_type):
            return True

        return left_type == right_type

    def type_compatible(self, var_type, expr_type):
        if expr_type == "UNKNOWN":
            return False

        if var_type == expr_type:
            return True

        if var_type == "REAL" and expr_type == "INTEGER":
            return True

        return False

    def get_errors(self):
        return self.errors

    def get_symbol_table(self):
        return self.symbol_table
