from monk.ast import Ident, LetStmt, Program
from monk.token import Token, TokenKind


def test_str() -> None:
    let = LetStmt(
        Token(TokenKind.LET, "let"),
        Ident(Token(TokenKind.IDENT, "myVar"), "myVar"),
        Ident(Token(TokenKind.IDENT, "anotherVar"), "anotherVar"),
    )
    program = Program([let])

    assert str(program) == "let myVar = anotherVar;"
