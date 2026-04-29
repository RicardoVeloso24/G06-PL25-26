import sys
import os
from utils import debug_print
from lexer import lexer as m_lexer 
from parser import parser as m_parser
from semantic import SemanticAnalyzer

def fortran_compiler(source_code):
    try:
        ast = m_parser.parse(source_code, lexer=m_lexer)
        
        if ast:
            debug_print(f"AST:\n {ast}\n")
                
            analyzer = SemanticAnalyzer() 
            analyzer.analyze(ast)
            
            symbols_table = analyzer.get_symbol_table()

            if symbols_table:
                debug_print(f"Tabel of Symbols:\n{symbols_table}")

        else:
            debug_print("Error generating AST.\n")
            return None
                
        return ast 

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


def main():
    if len(sys.argv) == 2: 
        debug_print(sys.argv)

        #base_path = os.path.dirname(__file__) #caminho até main.py
        #src_file_path = os.path.join(base_path, sys.argv[1]) #"examples/hello.f" #sys.argv[1]
        src_file_path = sys.argv[1]
        
        if not os.path.exists(src_file_path):
            print(f"Error: Ficheiro '{src_file_path}' não encontrado.")
            sys.exit(1)

        with open(src_file_path, 'r') as f:
            source_content = f.read()

        #ast = fortran_compiler(source_content)
        vm_code = fortran_compiler(source_content)

        if vm_code:
            print("VM Code generated successfully.\n")
        else:
            print("Error generating VM Code.\n")        
    else:
        print("Invalid number of arguments.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()