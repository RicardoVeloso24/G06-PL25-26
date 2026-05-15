import os
import sys

from codegen import generate_vm_code
from lexer import build_lexer
from parser import parser as m_parser
from semantic import SemanticAnalyzer
from utils import debug_print


def parse_source(source_code):
    lexer = build_lexer()
    lexer.lineno = 1
    ast = m_parser.parse(source_code, lexer=lexer)

    if lexer.errors:
        print("Erros lexicos:")
        for error in lexer.errors:
            print(f"- {error}")
        return None

    if ast is None:
        print("Erro sintatico: nao foi possivel gerar AST.")
        return None

    debug_print(f"AST:\n{ast}\n")
    return ast


def run_semantic_analysis(ast):
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    errors = analyzer.get_errors()
    if errors:
        print("Erros semanticos:")
        for error in errors:
            print(f"- {error}")
        return None

    symbols_table = analyzer.get_symbol_table()
    if symbols_table:
        debug_print(f"Tabela de simbolos:\n{symbols_table}\n")

    return analyzer


def generate_code(ast, analyzer):
    return generate_vm_code(ast, analyzer.get_symbol_table())


def fortran_compiler(source_code):
    try:
        ast = parse_source(source_code)
        if ast is None:
            return None

        analyzer = run_semantic_analysis(ast)
        if analyzer is None:
            return None

        return generate_code(ast, analyzer)

    except Exception as exc:
        print(f"Erro interno do compilador: {exc}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Uso: python fcompiler.py <ficheiro.f>")
        sys.exit(1)

    src_file_path = sys.argv[1]

    if not os.path.exists(src_file_path):
        print(f"Erro: ficheiro '{src_file_path}' nao encontrado.")
        sys.exit(1)

    with open(src_file_path, "r", encoding="utf-8") as source_file:
        source_content = source_file.read()

    vm_code = fortran_compiler(source_content)

    if vm_code is None:
        print("Compilacao falhou.")
        sys.exit(1)

    print(vm_code)
    print("Compilacao concluida com sucesso.")


if __name__ == "__main__":
    main()
