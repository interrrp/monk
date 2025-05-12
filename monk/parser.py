from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING, final

from monk.ast import (
    BlockStatement,
    BooleanLiteral,
    CallExpression,
    Expression,
    ExpressionStatement,
    FunctionLiteral,
    Identifier,
    IfExpression,
    InfixExpression,
    IntegerLiteral,
    LetStatement,
    PrefixExpression,
    Program,
    ReturnStatement,
    Statement,
)
from monk.token import Token, TokenKind

if TYPE_CHECKING:
    from monk.lexer import Lexer


class Precedence(IntEnum):
    LOWEST = 1
    EQUALS = 2
    LESSGREATER = 3
    SUM = 4
    PRODUCT = 5
    PREFIX = 6
    CALL = 7


_PRECEDENCES: dict[TokenKind, Precedence] = {
    TokenKind.EQ: Precedence.EQUALS,
    TokenKind.NOT_EQ: Precedence.EQUALS,
    TokenKind.LT: Precedence.LESSGREATER,
    TokenKind.GT: Precedence.LESSGREATER,
    TokenKind.PLUS: Precedence.SUM,
    TokenKind.MINUS: Precedence.SUM,
    TokenKind.SLASH: Precedence.PRODUCT,
    TokenKind.ASTERISK: Precedence.PRODUCT,
    TokenKind.LPAREN: Precedence.CALL,
}


@final
class TokenIterator:
    """
    Abstracts iteration over a lexer.

    - `current`: The current token.
    - `next`: The next token (a.k.a. "peek token").
    """

    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

        self.current = Token(TokenKind.ILLEGAL, "")
        self.next = Token(TokenKind.ILLEGAL, "")

        self.advance()  # Populate next token
        self.advance()  # Populate current token

    def advance(self) -> None:
        "Advance by one token."
        self.current = self.next
        self.next = next(self._lexer)

    def current_is(self, kind: TokenKind) -> bool:
        "Return whether the current token is of the given kind."
        return self.current.kind == kind

    def next_is(self, kind: TokenKind) -> bool:
        "Return whether the next token is of the given kind."
        return self.next.kind == kind

    def expect_next(self, kind: TokenKind) -> None:
        """
        Expect the next token to be of the given kind.

        If it is, the iterator will be advanced.
        If it is not, a `SyntaxError` will be raised.
        """

        if self.next.kind != kind:
            msg = f"Expected next token to be {kind}, got {self.next.kind}"
            raise SyntaxError(msg)

        self.advance()


PrefixParseFn = Callable[[], Expression]
"""A prefix parsing function produces a node when it matches a certain prefix."""

InfixParseFn = Callable[[Expression], Expression]
"""
An infix parsing function produces a node when it matches in between two expressions.

Infix parsing functions take in the expression on the left. It is up to the function to
consume the expression on the right.
"""


@final
class Parser:
    "A Pratt parser for Monkey."

    def __init__(self, lexer: Lexer) -> None:
        self._tokens = TokenIterator(lexer)

        self._prefix_parse_fns: dict[TokenKind, PrefixParseFn] = {
            TokenKind.IDENT: self._parse_identifier,
            TokenKind.INT: self._parse_integer,
            TokenKind.BANG: self._parse_prefix_expression,
            TokenKind.MINUS: self._parse_prefix_expression,
            TokenKind.TRUE: self._parse_boolean,
            TokenKind.FALSE: self._parse_boolean,
            TokenKind.LPAREN: self._parse_grouped_expression,
            TokenKind.IF: self._parse_if_expression,
            TokenKind.FUNCTION: self._parse_function_literal,
        }

        self._infix_parse_fns: dict[TokenKind, InfixParseFn] = {
            TokenKind.EQ: self._parse_infix_expression,
            TokenKind.NOT_EQ: self._parse_infix_expression,
            TokenKind.LT: self._parse_infix_expression,
            TokenKind.GT: self._parse_infix_expression,
            TokenKind.PLUS: self._parse_infix_expression,
            TokenKind.MINUS: self._parse_infix_expression,
            TokenKind.SLASH: self._parse_infix_expression,
            TokenKind.ASTERISK: self._parse_infix_expression,
            TokenKind.LPAREN: self._parse_call_expression,
        }

    def parse_program(self) -> Program:
        program = Program([])

        while not self._tokens.current_is(TokenKind.EOF):
            program.statements.append(self._parse_statement())
            self._tokens.advance()

        return program

    def _parse_statement(self) -> Statement:
        match self._tokens.current.kind:
            case TokenKind.LET:
                return self._parse_let_statement()
            case TokenKind.RETURN:
                return self._parse_return_statement()
            case _:
                return self._parse_expression_statement()

    def _parse_let_statement(self) -> LetStatement:
        # let
        token = self._tokens.current

        # let <name>
        self._tokens.expect_next(TokenKind.IDENT)
        name = self._parse_identifier()

        # let <name> =
        self._tokens.expect_next(TokenKind.ASSIGN)
        self._tokens.advance()

        # let <name> = <value>
        value = self._parse_expression()

        # let <name> = value>;
        self._tokens.expect_next(TokenKind.SEMICOLON)

        return LetStatement(token, name, value)

    def _parse_return_statement(self) -> ReturnStatement:
        token = self._tokens.current
        self._tokens.advance()

        # return <value>
        value = self._parse_expression()

        # return <value>;
        self._tokens.expect_next(TokenKind.SEMICOLON)

        return ReturnStatement(token, value)

    def _parse_expression_statement(self) -> ExpressionStatement:
        expr = self._parse_expression()

        if self._tokens.next_is(TokenKind.SEMICOLON):
            self._tokens.advance()

        return ExpressionStatement(self._tokens.current, expr)

    def _parse_expression(self, precedence: Precedence = Precedence.LOWEST) -> Expression:
        prefix_fn = self._prefix_parse_fns.get(self._tokens.current.kind)
        if prefix_fn is None:
            msg = f"No prefix parse function for {self._tokens.current.kind}"
            raise SyntaxError(msg)
        left = prefix_fn()

        while (
            self._tokens.next.kind != TokenKind.SEMICOLON and precedence < self._next_precedence()
        ):
            infix_fn = self._infix_parse_fns.get(self._tokens.next.kind)
            if infix_fn is None:
                return left

            self._tokens.advance()
            left = infix_fn(left)

        return left

    def _parse_if_expression(self) -> Expression:
        # if
        token = self._tokens.current

        # if (
        self._tokens.expect_next(TokenKind.LPAREN)
        self._tokens.advance()

        # if (<condition>
        condition = self._parse_expression()

        # if (<condition>) {
        self._tokens.expect_next(TokenKind.RPAREN)
        self._tokens.expect_next(TokenKind.LBRACE)

        # if (<condition>) { <consequence> }
        consequence = self._parse_block_statement()

        # if (<condition>) { <consequence> } else { <alternative> }
        alternative = None
        if self._tokens.next.kind == TokenKind.ELSE:
            self._tokens.advance()
            self._tokens.expect_next(TokenKind.LBRACE)
            alternative = self._parse_block_statement()

        return IfExpression(token, condition, consequence, alternative)

    def _parse_block_statement(self) -> BlockStatement:
        token = self._tokens.current

        self._tokens.advance()

        statements: list[Statement] = []
        while self._tokens.current.kind not in (TokenKind.RBRACE, TokenKind.EOF):
            statements.append(self._parse_statement())
            self._tokens.advance()

        return BlockStatement(token, statements)

    def _parse_prefix_expression(self) -> Expression:
        token = self._tokens.current
        operator = token.literal

        self._tokens.advance()
        right = self._parse_expression(Precedence.PREFIX)

        return PrefixExpression(token, operator, right)

    def _parse_infix_expression(self, left: Expression) -> Expression:
        token = self._tokens.current
        operator = token.literal

        precedence = self._current_precedence()
        self._tokens.advance()
        right = self._parse_expression(precedence)

        return InfixExpression(token, left, operator, right)

    def _parse_grouped_expression(self) -> Expression:
        self._tokens.advance()
        expr = self._parse_expression()
        self._tokens.expect_next(TokenKind.RPAREN)
        return expr

    def _parse_function_literal(self) -> FunctionLiteral:
        token = self._tokens.current

        self._tokens.expect_next(TokenKind.LPAREN)
        params = self._parse_function_parameters()

        self._tokens.expect_next(TokenKind.LBRACE)
        body = self._parse_block_statement()

        return FunctionLiteral(token, params, body)

    def _parse_function_parameters(self) -> list[Identifier]:
        params: list[Identifier] = []

        if self._tokens.next.kind == TokenKind.RPAREN:
            self._tokens.advance()
            return params

        self._tokens.advance()

        params.append(self._parse_identifier())

        while self._tokens.next.kind == TokenKind.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            params.append(self._parse_identifier())

        self._tokens.expect_next(TokenKind.RPAREN)

        return params

    def _parse_call_expression(self, fn: Expression) -> CallExpression:
        if not isinstance(fn, Identifier | FunctionLiteral):
            msg = "Expected identifier or function literal for function call"
            raise TypeError(msg)

        token = self._tokens.current
        args = self._parse_call_arguments()
        return CallExpression(token, fn, args)

    def _parse_call_arguments(self) -> list[Expression]:
        args: list[Expression] = []

        if self._tokens.next.kind == TokenKind.RPAREN:
            self._tokens.advance()
            return args

        self._tokens.advance()

        args.append(self._parse_expression())

        while self._tokens.next.kind == TokenKind.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            args.append(self._parse_expression())

        self._tokens.expect_next(TokenKind.RPAREN)

        return args

    def _parse_identifier(self) -> Identifier:
        return Identifier(self._tokens.current, self._tokens.current.literal)

    def _parse_integer(self) -> IntegerLiteral:
        return IntegerLiteral(self._tokens.current, int(self._tokens.current.literal))

    def _parse_boolean(self) -> BooleanLiteral:
        return BooleanLiteral(self._tokens.current, self._tokens.current.kind == TokenKind.TRUE)

    def _current_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.current.kind, Precedence.LOWEST)

    def _next_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.next.kind, Precedence.LOWEST)
