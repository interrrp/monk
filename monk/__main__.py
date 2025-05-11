from monk.lexer import Lexer
from monk.parser import Parser

if __name__ == "__main__":
    while True:
        code = input(">>> ")
        lexer = Lexer(code)
        parser = Parser(lexer)
        print(parser.parse_program())
