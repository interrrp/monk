from pathlib import Path
from sys import argv

from monk.evaluator import evaluate
from monk.lexer import lex
from monk.object import Environment
from monk.parser import Parser


def run(code: str, env: Environment) -> None:
    lexer = lex(code)
    parser = Parser(lexer)
    program = parser.parse_program()
    result = evaluate(program, env)
    print(result)


if __name__ == "__main__":
    env = Environment()

    if len(argv) > 1:
        code = Path(argv[1]).read_text()
        run(code, env)
    else:
        while True:
            run(input(">>> "), env)
