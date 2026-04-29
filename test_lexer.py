import argparse
from pathlib import Path

from lexer import build_lexer


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_file", nargs="?")
    return parser.parse_args()


def example_source():
    return """PROGRAM DEMO
INTEGER A
LOGICAL FLAG
A = 10
FLAG = .TRUE.
IF (A .GT. 0 .AND. FLAG) THEN
    PRINT *, 'OK'
ENDIF
END
"""


def read_source(source_file):
    if source_file is None:
        return example_source(), "<example>"

    path = Path(source_file)

    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {path}")

    if path.suffix.lower() != ".f":
        raise ValueError("O ficheiro tem de ter extensao .f")

    return path.read_text(encoding="utf-8"), str(path)


def run_lexer(source_code):
    lexer = build_lexer()
    lexer.lineno = 1
    lexer.input(source_code)
    tokens = list(lexer)
    return tokens, lexer.errors


def print_tokens(tokens):
    if not tokens:
        print("(sem tokens)")
        return

    print("TOKENS")
    print("-" * 60)
    for tok in tokens:
        print(f"{tok.type:<15} {repr(tok.value):<20} linha={tok.lineno}")


def print_errors(errors):
    if not errors:
        print("\nSEM ERROS LEXICOS")
        return

    print("\nERROS LEXICOS")
    print("-" * 60)
    for err in errors:
        print(err)


# def main():  
#     args = parse_args()
#     print (read_source(args.source_file))
#     try:
#         source_code, source_name = read_source(args.source_file)
        
#     except (FileNotFoundError, ValueError) as exc:
#         print(exc)
#         raise SystemExit(1)

#     print(f"Fonte: {source_name}")
#     tokens, errors = run_lexer(source_code)

#     print_tokens(tokens)
#     print_errors(errors)


# if __name__ == "__main__":
#     main()