from __future__ import annotations

from typing import final

from monk.token import Token, TokenType, lookup_ident

_SINGLE_CHAR_TOKEN_TYPE_MAP = {
    "=": TokenType.ASSIGN,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.ASTERISK,
    "/": TokenType.SLASH,
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ";": TokenType.SEMICOLON,
    ",": TokenType.COMMA,
    "<": TokenType.LESSER_THAN,
    ">": TokenType.GREATER_THAN,
    "!": TokenType.BANG,
}


@final
class Lexer:
    """
    The lexer (a.k.a. "tokenizer").

    A `Lexer` is an iterator. Once a `Lexer` is constructed, `next(lexer)` may be called
    to retrieve the next token. No errors are raised.
    """

    def __init__(self, code: str) -> None:
        self._code = code
        self._pos = -1
        self._current_char = ""
        self._next_char = ""
        self._advance()

    def __iter__(self) -> Lexer:
        return self

    def __next__(self) -> Token:
        self._eat_whitespace()

        token = Token(TokenType.ILLEGAL, "")

        match self._current_char:
            case "=" if self._next_char == "=":
                self._advance()
                self._advance()
                token = Token(TokenType.EQUAL, "==")

            case "!" if self._next_char == "=":
                self._advance()
                self._advance()
                token = Token(TokenType.NOT_EQUAL, "!=")

            case '"':
                token = Token(TokenType.STRING, self._eat_string())

            case _ if self._current_char in _SINGLE_CHAR_TOKEN_TYPE_MAP:
                token = Token(
                    type=_SINGLE_CHAR_TOKEN_TYPE_MAP[self._current_char],
                    literal=self._current_char,
                )

            case _ if self._current_char.isalpha():
                literal = self._eat_ident()
                type_ = lookup_ident(literal)
                token = Token(type_, literal)

            case _ if self._current_char.isdigit():
                token = Token(TokenType.INTEGER, self._eat_int())

            case "":
                return Token(TokenType.END_OF_FILE, "")

            case _:
                token = Token(TokenType.ILLEGAL, self._current_char)

        self._advance()
        return token

    def _eat_whitespace(self) -> None:
        while self._current_char.isspace():
            self._advance()

    def _eat_ident(self) -> str:
        orig_pos = self._pos
        while self._next_char.isalnum():
            self._advance()
        return self._code[orig_pos : self._pos + 1]

    def _eat_int(self) -> str:
        orig_pos = self._pos
        while self._next_char.isdigit():
            self._advance()
        return self._code[orig_pos : self._pos + 1]

    def _eat_string(self) -> str:
        self._advance()

        if self._current_char == '"':
            return ""

        orig_pos = self._pos
        while self._next_char not in ('"', ""):
            self._advance()
        self._advance()
        return self._code[orig_pos : self._pos]

    def _advance(self) -> None:
        """
        Advance the cursor.

        If the cursor would be out of bounds, `self._current_char` or `self._next_char`
        may be an empty string (`""`).
        """

        self._pos += 1

        if self._pos >= len(self._code):
            self._current_char = ""
            self._next_char = ""
            return

        self._current_char = self._code[self._pos]
        self._next_char = self._code[self._pos + 1] if self._pos + 1 < len(self._code) else ""
