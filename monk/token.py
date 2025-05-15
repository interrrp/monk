from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    ILLEGAL = "ILLEGAL"
    END_OF_FILE = "END_OF_FILE"

    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    STRING = "STRING"

    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    SLASH = "/"
    ASTERISK = "*"
    BANG = "!"

    COMMA = ","
    SEMICOLON = ";"

    LEFT_PAREN = "("
    RIGHT_PAREN = ")"
    LEFT_BRACE = "{"
    RIGHT_BRACE = "}"
    LEFT_BRACKET = "["
    RIGHT_BRACKET = "]"

    LESSER_THAN = "<"
    GREATER_THAN = ">"

    EQUAL = "=="
    NOT_EQUAL = "!="

    TRUE = "true"
    FALSE = "false"
    FUNCTION = "fn"
    LET = "let"
    IF = "if"
    ELSE = "else"
    RETURN = "return"


@dataclass
class Token:
    type: TokenType
    literal: str


def lookup_ident(ident: str) -> TokenType:
    return {
        "fn": TokenType.FUNCTION,
        "let": TokenType.LET,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "return": TokenType.RETURN,
    }.get(ident, TokenType.IDENTIFIER)
