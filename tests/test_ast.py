from monk.ast import Identifier, LetStatement, Program
from monk.token import Token, TokenKind


def test_str() -> None:
    let = LetStatement(
        Token(TokenKind.LET, "let"),
        Identifier(Token(TokenKind.IDENT, "myVar"), "myVar"),
        Identifier(Token(TokenKind.IDENT, "anotherVar"), "anotherVar"),
    )
    program = Program([let])

    assert str(program) == "let myVar = anotherVar;"
