import io
import unittest
from contextlib import redirect_stdout

from codegen import generate_vm_code
from fcompiler import fortran_compiler
from lexer import build_lexer
from parser import parser as parser_instance
from semantic import SemanticAnalyzer


def lex_source(source):
    lexer = build_lexer()
    lexer.lineno = 1
    lexer.input(source)
    return list(lexer), lexer.errors


def parse_source(source):
    lexer = build_lexer()
    lexer.lineno = 1
    return parser_instance.parse(source, lexer=lexer)


def analyze_source(source):
    ast = parse_source(source)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return ast, analyzer


class LexerTests(unittest.TestCase):
    def test_basic_program_tokens(self):
        tokens, errors = lex_source("PROGRAM hello\nPRINT *, 'Ola'\nEND\n")

        self.assertEqual(errors, [])
        self.assertEqual(
            [token.type for token in tokens],
            ["PROGRAM", "ID", "PRINT", "TIMES", "COMMA", "STRING_LITERAL", "END"],
        )
        self.assertEqual(tokens[1].value, "HELLO")
        self.assertEqual(tokens[5].value, "Ola")

    def test_logical_and_relational_tokens(self):
        tokens, errors = lex_source("IF (A .GT. 0 .AND. .TRUE.) THEN\nENDIF\n")

        self.assertEqual(errors, [])
        self.assertIn("GT_OP", [token.type for token in tokens])
        self.assertIn("AND_OP", [token.type for token in tokens])
        self.assertIn("TRUE_LITERAL", [token.type for token in tokens])


class ParserTests(unittest.TestCase):
    def test_parser_keeps_expected_program_shape(self):
        ast = parse_source(
            """PROGRAM TEST
INTEGER A
A = 1
END
"""
        )

        self.assertEqual(ast[0], "program")
        self.assertEqual(ast[1], "TEST")
        self.assertIn("declarations", ast[2])
        self.assertIn("statements", ast[2])

    def test_parser_supports_arrays_and_io_lists(self):
        ast = parse_source(
            """PROGRAM TEST
INTEGER A(10), B
READ *, A, B
PRINT *, A, B, 'OK'
END
"""
        )

        body = ast[2]
        self.assertEqual(
            body["declarations"],
            [("decl", "INTEGER", [("array_decl", "A", 10), "B"])],
        )
        self.assertEqual(body["statements"][0][0], "read")
        self.assertEqual(body["statements"][0][1][0], "list")
        self.assertEqual(len(body["statements"][0][1][1]), 2)
        self.assertEqual(body["statements"][1][0], "print")
        self.assertEqual(len(body["statements"][1][1][1]), 3)

    def test_parser_keeps_array_reference(self):
        ast = parse_source(
            """PROGRAM TEST
INTEGER A(10), I
A(I) = 1
PRINT *, A(I)
END
"""
        )

        statements = ast[2]["statements"]
        self.assertEqual(statements[0][1][0], "array_ref")
        self.assertEqual(statements[0][1][1], "A")
        self.assertEqual(statements[1][1][1][0][0], "array_ref")

    def test_parser_reports_syntax_error(self):
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            ast = parse_source(
                """PROGRAM BAD
INTEGER A
A =
END
"""
            )

        self.assertIsNone(ast)
        self.assertIn("Syntax Error", buffer.getvalue())


class SemanticTests(unittest.TestCase):
    def test_valid_program_has_no_semantic_errors(self):
        _, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A
LOGICAL OK
A = 3
OK = A .GT. 0
IF (OK) THEN
PRINT *, A
ENDIF
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])

    def test_undeclared_variable_is_reported(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A
A = B
END
"""
        )

        self.assertIn("Variavel 'B' nao declarada.", analyzer.get_errors())

    def test_type_mismatch_is_reported(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A
A = .TRUE.
END
"""
        )

        self.assertIn(
            "Incompatibilidade de tipos: 'A' e INTEGER, recebeu LOGICAL.",
            analyzer.get_errors(),
        )

    def test_goto_to_missing_label_is_reported(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A
GOTO 10
A = 1
END
"""
        )

        self.assertIn("Label 10 usada mas nao definida.", analyzer.get_errors())

    def test_do_with_different_continue_label_reports_missing_label(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER I
DO 10 I = 1, 3
20 CONTINUE
END
"""
        )

        self.assertIn("Label 10 usada mas nao definida.", analyzer.get_errors())

    def test_do_label_must_point_to_continue(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER I
DO 10 I = 1, 3
10 PRINT *, I
END
"""
        )

        self.assertIn(
            "Label 10 usada em DO tem de corresponder a CONTINUE.",
            analyzer.get_errors(),
        )

    def test_logical_operators_require_logical_operands(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A
A = 1 .AND. 2
END
"""
        )

        self.assertIn(
            "Operador logico '.AND.' exige operandos LOGICAL.",
            analyzer.get_errors(),
        )

    def test_array_access_is_semantically_validated(self):
        _, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A(10), I
I = 1
A(I) = 3
PRINT *, A(I)
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        self.assertEqual(analyzer.get_symbol_table()["A"]["kind"], "array")
        self.assertEqual(analyzer.get_symbol_table()["A"]["size"], 10)

    def test_scalar_cannot_be_used_as_array(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A, I
A(I) = 3
END
"""
        )

        self.assertIn("Variavel escalar 'A' usada como array.", analyzer.get_errors())

    def test_array_cannot_be_used_without_index(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A(10)
A = 3
END
"""
        )

        self.assertIn("Array 'A' usado sem indice.", analyzer.get_errors())

    def test_array_index_must_be_numeric(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A(10)
LOGICAL I
I = .TRUE.
A(I) = 3
END
"""
        )

        self.assertIn("Indice do array 'A' tem de ser numerico.", analyzer.get_errors())

    def test_undeclared_array_is_reported(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER I
I = 1
A(I) = 3
END
"""
        )

        self.assertIn("Variavel 'A' nao declarada.", analyzer.get_errors())

    def test_array_index_with_undeclared_variable_is_reported(self):
        _, analyzer = analyze_source(
            """PROGRAM BAD
INTEGER A(10)
A(I) = 3
END
"""
        )

        self.assertIn("Variavel 'I' nao declarada.", analyzer.get_errors())
        self.assertIn("Indice do array 'A' tem de ser numerico.", analyzer.get_errors())


class CodegenTests(unittest.TestCase):
    def test_codegen_generates_stack_vm_for_assignment_and_print(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A
A = 2 + 3
PRINT *, A
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("PUSHN 1", vm_code)
        self.assertIn("PUSHI 2", vm_code)
        self.assertIn("PUSHI 3", vm_code)
        self.assertIn("ADD", vm_code)
        self.assertIn("STOREG 0", vm_code)
        self.assertIn("PUSHG 0", vm_code)
        self.assertIn("WRITEI", vm_code)
        self.assertTrue(vm_code.endswith("STOP"))

    def test_codegen_generates_control_flow_and_io(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A
READ *, A
IF (A .GT. 0) THEN
PRINT *, 'POS'
ELSE
PRINT *, 'NEG'
ENDIF
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("READ", vm_code)
        self.assertIn("ATOI", vm_code)
        self.assertIn("STOREG 0", vm_code)
        self.assertIn("SUP", vm_code)
        self.assertIn("JZ IF_ELSE_", vm_code)
        self.assertIn('PUSHS "POS"', vm_code)
        self.assertIn('PUSHS "NEG"', vm_code)
        self.assertIn("WRITES", vm_code)

    def test_codegen_generates_do_loop(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER I
DO 10 I = 1, 3
10 CONTINUE
PRINT *, I
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("DO_10_START_", vm_code)
        self.assertIn("L10:", vm_code)
        self.assertIn("JUMP DO_10_START_", vm_code)
        self.assertIn("DO_10_END_", vm_code)

    def test_string_literal_is_not_confused_with_variable(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A
A = 1
PRINT *, 'A', A
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn('PUSHS "A"', vm_code)
        self.assertIn("PUSHG 0", vm_code)

    def test_codegen_distinguishes_array_operations(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A(10), I
I = 1
A(I) = 3
PRINT *, A(I)
READ *, A(I)
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("PUSHN 11", vm_code)
        self.assertIn("STOREN", vm_code)
        self.assertIn("LOADN", vm_code)
        self.assertIn("READ", vm_code)
        self.assertIn("ATOI", vm_code)

    def test_codegen_prints_mixed_string_variable_and_array(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A, B(5), I
A = 2
I = 1
B(I) = 4
PRINT *, 'VALUES', A, B(I)
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn('PUSHS "VALUES"', vm_code)
        self.assertIn("PUSHG 0", vm_code)
        self.assertIn("LOADN", vm_code)

    def test_codegen_reads_scalar_and_array_access(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A, B(5), I
I = 1
READ *, A, B(I)
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("STOREG 0", vm_code)
        self.assertIn("STOREN", vm_code)

    def test_codegen_array_program_with_if_and_do(self):
        ast, analyzer = analyze_source(
            """PROGRAM TEST
INTEGER A(5), I
LOGICAL OK
OK = .TRUE.
DO 10 I = 1, 3
A(I) = I
10 CONTINUE
IF (OK) THEN
PRINT *, A(I)
ENDIF
END
"""
        )

        self.assertEqual(analyzer.get_errors(), [])
        vm_code = generate_vm_code(ast, analyzer.get_symbol_table())

        self.assertIn("PUSHN 7", vm_code)
        self.assertIn("STOREN", vm_code)
        self.assertIn("LOADN", vm_code)
        self.assertIn("JZ IF_END_", vm_code)


class CompilerFlowTests(unittest.TestCase):
    def test_lexical_errors_fail_compilation(self):
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            result = fortran_compiler(
                """PROGRAM BAD
@
END
"""
            )

        self.assertIsNone(result)
        self.assertIn("Erros lexicos:", buffer.getvalue())

    def test_syntax_errors_fail_compilation(self):
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            result = fortran_compiler(
                """PROGRAM BAD
INTEGER A
A =
END
"""
            )

        self.assertIsNone(result)
        self.assertIn("Erro sintatico", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
