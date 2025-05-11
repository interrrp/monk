from __future__ import annotations

from monk.token import Token, TokenKind, lookup_ident

_SINGLE_CHAR_TOKEN_KIND_MAP = {
    "=": TokenKind.ASSIGN,
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.ASTERISK,
    "/": TokenKind.SLASH,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    ";": TokenKind.SEMICOLON,
    ",": TokenKind.COMMA,
    "<": TokenKind.LT,
    ">": TokenKind.GT,
    "!": TokenKind.BANG,  # Added missing BANG token
}


class Lexer:
    def __init__(self, code: str) -> None:
        self._code = code
        self._pos = -1
        self._current_char = ""
        self._next_char = ""

    def __iter__(self) -> Lexer:
        return self

    def __next__(self) -> Token:
        self._advance()
        self._eat_whitespace()

        match self._current_char:
            case "=" if self._next_char == "=":
                self._advance()
                return Token(TokenKind.EQ, "==")

            case "!" if self._next_char == "=":  # Added NOT_EQ token
                self._advance()
                return Token(TokenKind.NOT_EQ, "!=")

            case _ if self._current_char in _SINGLE_CHAR_TOKEN_KIND_MAP:
                return Token(
                    kind=_SINGLE_CHAR_TOKEN_KIND_MAP[self._current_char],
                    literal=self._current_char,
                )

            case _ if self._current_char.isalpha():
                literal = self._eat_ident()
                kind = lookup_ident(literal)
                return Token(kind, literal)

            case _ if self._current_char.isdigit():
                return Token(TokenKind.INT, self._eat_int())

            case "":  # End of input
                raise StopIteration

            case _:
                return Token(TokenKind.ILLEGAL, self._current_char)

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

    def _advance(self) -> None:
        self._pos += 1

        if self._pos >= len(self._code):
            self._current_char = ""
            self._next_char = ""
            return

        self._current_char = self._code[self._pos]
        self._next_char = self._code[self._pos + 1] if self._pos + 1 < len(self._code) else ""
