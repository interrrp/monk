from monk.lexer import Lexer
from monk.token import Token, TokenKind


def test_next_token() -> None:
    code = """
        let five = 5;
        let ten = 10;

        let add = fn(x, y) {
                x + y;
        };

        let result = add(five, ten);

        !-/*5;
        5 < 10 > 5;

        if (5 < 10) {
                return true;
        } else {
                return false;
        }

        10 == 10;
        10 != 9;

        "foobar"
        " foo bar "
    """

    expected_tokens = [
        Token(TokenKind.LET, "let"),
        Token(TokenKind.IDENT, "five"),
        Token(TokenKind.ASSIGN, "="),
        Token(TokenKind.INT, "5"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.LET, "let"),
        Token(TokenKind.IDENT, "ten"),
        Token(TokenKind.ASSIGN, "="),
        Token(TokenKind.INT, "10"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.LET, "let"),
        Token(TokenKind.IDENT, "add"),
        Token(TokenKind.ASSIGN, "="),
        Token(TokenKind.FUNCTION, "fn"),
        Token(TokenKind.LPAREN, "("),
        Token(TokenKind.IDENT, "x"),
        Token(TokenKind.COMMA, ","),
        Token(TokenKind.IDENT, "y"),
        Token(TokenKind.RPAREN, ")"),
        Token(TokenKind.LBRACE, "{"),
        ##
        Token(TokenKind.IDENT, "x"),
        Token(TokenKind.PLUS, "+"),
        Token(TokenKind.IDENT, "y"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.RBRACE, "}"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.LET, "let"),
        Token(TokenKind.IDENT, "result"),
        Token(TokenKind.ASSIGN, "="),
        Token(TokenKind.IDENT, "add"),
        Token(TokenKind.LPAREN, "("),
        Token(TokenKind.IDENT, "five"),
        Token(TokenKind.COMMA, ","),
        Token(TokenKind.IDENT, "ten"),
        Token(TokenKind.RPAREN, ")"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.BANG, "!"),
        Token(TokenKind.MINUS, "-"),
        Token(TokenKind.SLASH, "/"),
        Token(TokenKind.ASTERISK, "*"),
        Token(TokenKind.INT, "5"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.INT, "5"),
        Token(TokenKind.LT, "<"),
        Token(TokenKind.INT, "10"),
        Token(TokenKind.GT, ">"),
        Token(TokenKind.INT, "5"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.IF, "if"),
        Token(TokenKind.LPAREN, "("),
        Token(TokenKind.INT, "5"),
        Token(TokenKind.LT, "<"),
        Token(TokenKind.INT, "10"),
        Token(TokenKind.RPAREN, ")"),
        Token(TokenKind.LBRACE, "{"),
        ##
        Token(TokenKind.RETURN, "return"),
        Token(TokenKind.TRUE, "true"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.RBRACE, "}"),
        Token(TokenKind.ELSE, "else"),
        Token(TokenKind.LBRACE, "{"),
        ##
        Token(TokenKind.RETURN, "return"),
        Token(TokenKind.FALSE, "false"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.RBRACE, "}"),
        ##
        Token(TokenKind.INT, "10"),
        Token(TokenKind.EQ, "=="),
        Token(TokenKind.INT, "10"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.INT, "10"),
        Token(TokenKind.NOT_EQ, "!="),
        Token(TokenKind.INT, "9"),
        Token(TokenKind.SEMICOLON, ";"),
        ##
        Token(TokenKind.STRING, "foobar"),
        Token(TokenKind.STRING, " foo bar "),
        ##
        Token(TokenKind.EOF, ""),
    ]

    lexer = Lexer(code)

    for i, expected_token in enumerate(expected_tokens):
        actual_token = next(lexer)
        assert expected_token == actual_token, f"Token #{i + 1} mismatch"
