from monk.lexer import Lexer
from monk.token import Token, TokenType


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
        ""
    """

    expected_tokens = [
        Token(TokenType.LET, "let"),
        Token(TokenType.IDENTIFIER, "five"),
        Token(TokenType.ASSIGN, "="),
        Token(TokenType.INTEGER, "5"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.LET, "let"),
        Token(TokenType.IDENTIFIER, "ten"),
        Token(TokenType.ASSIGN, "="),
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.LET, "let"),
        Token(TokenType.IDENTIFIER, "add"),
        Token(TokenType.ASSIGN, "="),
        Token(TokenType.FUNCTION, "fn"),
        Token(TokenType.LEFT_PAREN, "("),
        Token(TokenType.IDENTIFIER, "x"),
        Token(TokenType.COMMA, ","),
        Token(TokenType.IDENTIFIER, "y"),
        Token(TokenType.RIGHT_PAREN, ")"),
        Token(TokenType.LEFT_BRACE, "{"),
        ##
        Token(TokenType.IDENTIFIER, "x"),
        Token(TokenType.PLUS, "+"),
        Token(TokenType.IDENTIFIER, "y"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.RIGHT_BRACE, "}"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.LET, "let"),
        Token(TokenType.IDENTIFIER, "result"),
        Token(TokenType.ASSIGN, "="),
        Token(TokenType.IDENTIFIER, "add"),
        Token(TokenType.LEFT_PAREN, "("),
        Token(TokenType.IDENTIFIER, "five"),
        Token(TokenType.COMMA, ","),
        Token(TokenType.IDENTIFIER, "ten"),
        Token(TokenType.RIGHT_PAREN, ")"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.BANG, "!"),
        Token(TokenType.MINUS, "-"),
        Token(TokenType.SLASH, "/"),
        Token(TokenType.ASTERISK, "*"),
        Token(TokenType.INTEGER, "5"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.INTEGER, "5"),
        Token(TokenType.LESSER_THAN, "<"),
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.GREATER_THAN, ">"),
        Token(TokenType.INTEGER, "5"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.IF, "if"),
        Token(TokenType.LEFT_PAREN, "("),
        Token(TokenType.INTEGER, "5"),
        Token(TokenType.LESSER_THAN, "<"),
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.RIGHT_PAREN, ")"),
        Token(TokenType.LEFT_BRACE, "{"),
        ##
        Token(TokenType.RETURN, "return"),
        Token(TokenType.TRUE, "true"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.RIGHT_BRACE, "}"),
        Token(TokenType.ELSE, "else"),
        Token(TokenType.LEFT_BRACE, "{"),
        ##
        Token(TokenType.RETURN, "return"),
        Token(TokenType.FALSE, "false"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.RIGHT_BRACE, "}"),
        ##
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.EQUAL, "=="),
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.INTEGER, "10"),
        Token(TokenType.NOT_EQUAL, "!="),
        Token(TokenType.INTEGER, "9"),
        Token(TokenType.SEMICOLON, ";"),
        ##
        Token(TokenType.STRING, "foobar"),
        Token(TokenType.STRING, " foo bar "),
        Token(TokenType.STRING, ""),
        ##
        Token(TokenType.END_OF_FILE, ""),
    ]

    lexer = Lexer(code)

    for i, expected_token in enumerate(expected_tokens):
        actual_token = next(lexer)
        assert expected_token == actual_token, f"Token #{i + 1} mismatch"
