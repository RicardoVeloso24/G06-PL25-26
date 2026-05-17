class CodeGenerator:
    def __init__(self, symbol_table=None):
        self.symbol_table = symbol_table or {}
        self.instructions = []
        self.label_counter = 0
        self.global_addresses = {}
        self.global_sizes = {}

    def generate(self, ast):
        kind, program_name, body = ast

        if kind != "program":
            raise ValueError("AST invalida para geracao de codigo.")

        self.build_global_layout(body["declarations"])
        if self.total_global_size() > 0:
            self.emit(f"PUSHN {self.total_global_size()}")

        self.generate_statements(body["statements"])
        self.emit("STOP")
        return "\n".join(self.instructions)

    def emit(self, instruction):
        self.instructions.append(instruction)

    def emit_label(self, label):
        self.emit(f"{label}:")

    # def new_label(self, prefix):
    #     self.label_counter += 1
    #     return f"{prefix}_{self.label_counter}"

    def sanitize_label(self, label):
        return "".join(ch for ch in str(label) if ch.isalnum())

    def new_label(self, prefix):
        self.label_counter += 1
        return f"{self.sanitize_label(prefix)}{self.label_counter}"

    def build_global_layout(self, declarations):
        next_address = 0

        for decl in declarations:
            _, var_type, vars_list = decl
            for var in vars_list:
                if isinstance(var, tuple) and var[0] == "array_decl":
                    name = var[1]
                    size = var[2]
                else:
                    name = var
                    size = 1

                self.global_addresses[name] = next_address
                self.global_sizes[name] = size
                next_address += size

    def total_global_size(self):
        return sum(self.global_sizes.values())

    def generate_statements(self, statements):
        index = 0

        while index < len(statements):
            stmt = statements[index]

            if stmt[0] == "do-loop":
                body, next_index = self.collect_do_body(statements, index)
                self.generate_do(stmt, body)
                index = next_index
            else:
                self.generate_statement(stmt)
                index += 1

    def collect_do_body(self, statements, do_index):
        do_stmt = statements[do_index]
        label = do_stmt[1]
        body = []
        index = do_index + 1

        while index < len(statements):
            stmt = statements[index]
            if stmt[0] == "label" and stmt[1] == label and stmt[2][0] == "continue":
                return body, index + 1

            body.append(stmt)
            index += 1

        return body, index

    def generate_statement(self, stmt):
        kind = stmt[0]

        if kind == "assign":
            self.generate_assignment(stmt[1], stmt[2])

        elif kind == "if-then":
            self.generate_if(stmt[1], stmt[2])

        elif kind == "if-then-else":
            self.generate_if(stmt[1], stmt[2], stmt[3])

        elif kind == "do-loop":
            self.generate_do(stmt, [])

        elif kind == "goto":
            self.emit(f"JUMP L{stmt[1]}")

        elif kind == "label":
            self.emit_label(f"L{stmt[1]}")
            self.generate_statement(stmt[2])

        elif kind == "continue":
            return

        elif kind == "read":
            self.generate_read(stmt[1])

        elif kind in ["print", "write"]:
            self.generate_output(stmt[1])

        else:
            raise ValueError(f"Instrucao nao suportada no codegen: {kind}")

    def generate_assignment(self, target, expr):
        if target[0] == "var":
            self.generate_expression(expr)
            self.emit(f"STOREG {self.global_address(target[1])}")

        elif target[0] == "array_ref":
            self.generate_array_address(target[1], target[2])
            self.generate_expression(expr)
            self.emit("STOREN")

        else:
            raise ValueError("Atribuicao recebeu alvo que nao e variavel.")

    def generate_if(self, condition, then_statements, else_statements=None):
        else_label = self.new_label("IF_ELSE")
        end_label = self.new_label("IF_END")

        self.generate_expression(condition)

        if else_statements is None:
            self.emit(f"JZ {end_label}")
            self.generate_statements(then_statements)
            self.emit_label(end_label)
        else:
            self.emit(f"JZ {else_label}")
            self.generate_statements(then_statements)
            self.emit(f"JUMP {end_label}")
            self.emit_label(else_label)
            self.generate_statements(else_statements)
            self.emit_label(end_label)

    def generate_do(self, stmt, body):
        _, label, var_name, start_expr, end_expr = stmt
        start_label = self.new_label(f"DO_{label}_START")
        end_label = self.new_label(f"DO_{label}_END")

        self.generate_expression(start_expr)
        self.emit(f"STOREG {self.global_address(var_name)}")
        self.emit_label(start_label)
        self.emit(f"PUSHG {self.global_address(var_name)}")
        self.generate_expression(end_expr)
        self.emit("INFEQ")
        self.emit(f"JZ {end_label}")
        self.generate_statements(body)
        self.emit_label(f"L{label}")
        self.emit(f"PUSHG {self.global_address(var_name)}")
        self.emit("PUSHI 1")
        self.emit("ADD")
        self.emit(f"STOREG {self.global_address(var_name)}")
        self.emit(f"JUMP {start_label}")
        self.emit_label(end_label)

    def generate_read(self, target):
        for item in self.flatten_items(target):
            target_type = self.target_type(item)

            if item[0] == "var":
                self.emit("READ")
                self.emit(self.read_conversion_instruction(target_type))
                self.emit(f"STOREG {self.global_address(item[1])}")

            elif item[0] == "array_ref":
                self.generate_array_address(item[1], item[2])
                self.emit("READ")
                self.emit(self.read_conversion_instruction(target_type))
                self.emit("STOREN")

            else:
                raise ValueError("READ recebeu item que nao e variavel.")

    def generate_output(self, output):
        for item in self.flatten_items(output):
            output_type = self.expression_type(item)
            self.generate_expression(item)
            self.emit(self.write_instruction(output_type))

    def generate_expression(self, expr):
        kind = expr[0]

        if kind == "leaf":
            self.generate_leaf(expr[1])

        elif kind == "var":
            self.emit(f"PUSHG {self.global_address(expr[1])}")

        elif kind == "array_ref":
            self.generate_array_address(expr[1], expr[2])
            self.emit("LOADN")

        elif kind == "string":
            self.generate_string(expr[1])

        elif kind == "binop":
            _, op, left_expr, right_expr = expr
            self.generate_expression(left_expr)
            self.generate_expression(right_expr)
            self.emit_binary_operator(op)

        elif kind == "unop":
            _, op, inner_expr = expr
            self.generate_expression(inner_expr)
            self.emit(self.unary_instruction(op))

        else:
            raise ValueError(f"Expressao nao suportada no codegen: {kind}")

    def generate_leaf(self, value):
        if isinstance(value, bool):
            self.emit(f"PUSHI {1 if value else 0}")

        elif isinstance(value, int):
            self.emit(f"PUSHI {value}")

        elif isinstance(value, float):
            self.emit(f"PUSHF {value}")

        else:
            raise ValueError(f"Literal nao suportado no codegen: {value}")

    def generate_string(self, value):
        escaped = value.replace('"', '\\"')
        self.emit(f'PUSHS "{escaped}"')

    # def generate_array_address(self, name, index_expr):
    #     self.emit("PUSHGP")
    #     self.emit(f"PUSHI {self.global_address(name)}")
    #     self.emit("PADD")
    #     self.generate_expression(index_expr)
    #     self.emit("PUSHI 1")
    #     self.emit("SUB")
    #     self.emit("PADD")

    def generate_array_address(self, name, index_expr):
        self.emit("PUSHGP")
        self.emit(f"PUSHI {self.global_address(name)}")
        self.emit("PADD")
        self.generate_expression(index_expr)
        self.emit("PUSHI 1")
        self.emit("SUB")

    def emit_binary_operator(self, op):
        if op == ".NE.":
            self.emit("EQUAL")
            self.emit("NOT")
            return

        instructions = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV",
            ".EQ.": "EQUAL",
            ".LT.": "INF",
            ".LE.": "INFEQ",
            ".GT.": "SUP",
            ".GE.": "SUPEQ",
            ".AND.": "AND",
            ".OR.": "OR",
        }

        if op not in instructions:
            raise ValueError(f"Operador binario nao suportado no codegen: {op}")

        self.emit(instructions[op])

    def unary_instruction(self, op):
        instructions = {
            "-": "NEG",
            ".NOT.": "NOT",
        }

        if op not in instructions:
            raise ValueError(f"Operador unario nao suportado no codegen: {op}")

        return instructions[op]

    def read_conversion_instruction(self, type_name):
        if type_name == "REAL":
            return "ATOF"

        return "ATOI"

    def write_instruction(self, type_name):
        if type_name == "STRING":
            return "WRITES"

        if type_name == "REAL":
            return "WRITEF"

        return "WRITEI"

    def expression_type(self, expr):
        kind = expr[0]

        if kind == "leaf":
            value = expr[1]
            if isinstance(value, bool):
                return "LOGICAL"
            if isinstance(value, int):
                return "INTEGER"
            if isinstance(value, float):
                return "REAL"
            return "UNKNOWN"

        if kind == "string":
            return "STRING"

        if kind == "var":
            return self.symbol_type(expr[1])

        if kind == "array_ref":
            return self.symbol_type(expr[1])

        if kind == "binop":
            op = expr[1]
            if op in [".EQ.", ".NE.", ".LT.", ".LE.", ".GT.", ".GE.", ".AND.", ".OR."]:
                return "LOGICAL"

            left_type = self.expression_type(expr[2])
            right_type = self.expression_type(expr[3])
            if left_type == "REAL" or right_type == "REAL":
                return "REAL"
            return "INTEGER"

        if kind == "unop":
            if expr[1] == ".NOT.":
                return "LOGICAL"
            return self.expression_type(expr[2])

        return "UNKNOWN"

    def target_type(self, target):
        if target[0] == "var":
            return self.symbol_type(target[1])

        if target[0] == "array_ref":
            return self.symbol_type(target[1])

        return "UNKNOWN"

    def symbol_type(self, name):
        return self.symbol_table.get(name, {}).get("type", "UNKNOWN")

    def global_address(self, name):
        if name not in self.global_addresses:
            raise ValueError(f"Variavel sem endereco global: {name}")

        return self.global_addresses[name]

    def flatten_items(self, node):
        if isinstance(node, list):
            return node

        if isinstance(node, tuple) and node and node[0] == "list":
            return node[1]

        return [node]


def generate_vm_code(ast, symbol_table=None):
    generator = CodeGenerator(symbol_table)
    return generator.generate(ast)
