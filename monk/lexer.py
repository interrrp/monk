from __future__ import annotations

import re
from typing import TYPE_CHECKING

from monk.token import Token, TokenType

if TYPE_CHECKING:
    from collections.abc import Generator

PATTERNS = {
    TokenType.LET: r"\blet\b",
    TokenType.FUNCTION: r"\bfn\b",
    TokenType.IF: r"\bif\b",
    TokenType.ELSE: r"\belse\b",
    TokenType.RETURN: r"\breturn\b",
    TokenType.TRUE: r"\btrue\b",
    TokenType.FALSE: r"\bfalse\b",
    TokenType.IDENTIFIER: r"[a-zA-Z_][a-zA-Z0-9_]*",
    TokenType.INTEGER: r"\d+",
    TokenType.STRING: r'"[^"]*"',
    TokenType.NOT_EQUAL: r"!=",
    TokenType.BANG: r"!",
    TokenType.EQUAL: r"==",
    TokenType.ASSIGN: r"=",
    TokenType.PLUS: r"\+",
    TokenType.MINUS: r"-",
    TokenType.ASTERISK: r"\*",
    TokenType.SLASH: r"/",
    TokenType.LESSER_THAN: r"<",
    TokenType.GREATER_THAN: r">",
    TokenType.LEFT_PAREN: r"\(",
    TokenType.RIGHT_PAREN: r"\)",
    TokenType.LEFT_BRACE: r"\{",
    TokenType.RIGHT_BRACE: r"\}",
    TokenType.COMMA: r",",
    TokenType.SEMICOLON: r";",
}


def lex(code: str) -> Generator[Token]:
    cursor = 0

    while cursor < len(code):
        current_char = code[cursor]

        # Skip whitespace
        if current_char.isspace():
            cursor += 1
            continue

        token = None

        for token_type, pattern in PATTERNS.items():
            regex = re.compile(pattern)
            match = regex.match(code, cursor)
            if match:
                literal = match.group()

                # Remove quotes around strings
                if token_type == TokenType.STRING:
                    literal = literal[1:-1]

                token = Token(token_type, literal)
                cursor = match.end()
                break

        # If none of the patterns matched, this character is unsupported/illegal
        if token is None:
            msg = f"Illegal character: {current_char}"
            raise SyntaxError(msg)

        yield token

    while True:
        yield Token(TokenType.END_OF_FILE, "")
