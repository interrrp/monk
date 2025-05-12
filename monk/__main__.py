from monk.evaluator import evaluate
from monk.lexer import Lexer
from monk.object import Environment
from monk.parser import Parser

if __name__ == "__main__":
    env = Environment()

    while True:
        code = input(">>> ")
        lexer = Lexer(code)

        parser = Parser(lexer)
        program = parser.parse_program()

        result = evaluate(program, env)
        print(result)  # noqa: T201
