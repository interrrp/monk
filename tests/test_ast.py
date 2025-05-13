from monk.ast import Identifier, LetStatement, Program
from monk.token import Token, TokenType


def test_str() -> None:
    let = LetStatement(
        Token(TokenType.LET, "let"),
        Identifier(Token(TokenType.IDENTIFIER, "myVar"), "myVar"),
        Identifier(Token(TokenType.IDENTIFIER, "anotherVar"), "anotherVar"),
    )
    program = Program([let])

    assert str(program) == "let myVar = anotherVar;"
