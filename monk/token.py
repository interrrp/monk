from dataclasses import dataclass
from enum import Enum


class TokenKind(Enum):
    ILLEGAL = "ILLEGAL"
    EOF = "EOF"

    IDENT = "IDENT"
    INT = "INT"
    STRING = "STRING"

    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    SLASH = "/"
    ASTERISK = "*"
    BANG = "!"

    COMMA = ","
    SEMICOLON = ";"

    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"

    LT = "<"
    GT = ">"

    EQ = "=="
    NOT_EQ = "!="

    TRUE = "true"
    FALSE = "false"
    FUNCTION = "fn"
    LET = "let"
    IF = "if"
    ELSE = "else"
    RETURN = "return"


@dataclass
class Token:
    kind: TokenKind
    literal: str


def lookup_ident(ident: str) -> TokenKind:
    return {
        "fn": TokenKind.FUNCTION,
        "let": TokenKind.LET,
        "true": TokenKind.TRUE,
        "false": TokenKind.FALSE,
        "if": TokenKind.IF,
        "else": TokenKind.ELSE,
        "return": TokenKind.RETURN,
    }.get(ident, TokenKind.IDENT)
