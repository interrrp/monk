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
    StringLiteral,
)
from monk.token import Token, TokenType

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


_PRECEDENCES: dict[TokenType, Precedence] = {
    TokenType.EQUAL: Precedence.EQUALS,
    TokenType.NOT_EQUAL: Precedence.EQUALS,
    TokenType.LESSER_THAN: Precedence.LESSGREATER,
    TokenType.GREATER_THAN: Precedence.LESSGREATER,
    TokenType.PLUS: Precedence.SUM,
    TokenType.MINUS: Precedence.SUM,
    TokenType.SLASH: Precedence.PRODUCT,
    TokenType.ASTERISK: Precedence.PRODUCT,
    TokenType.LEFT_PAREN: Precedence.CALL,
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

        self.current = Token(TokenType.ILLEGAL, "")
        self.next = Token(TokenType.ILLEGAL, "")

        self.advance()  # Populate next token
        self.advance()  # Populate current token

    def advance(self) -> None:
        "Advance by one token."
        self.current = self.next
        self.next = next(self._lexer)

    def current_is(self, t: TokenType) -> bool:
        "Return whether the current token is of the given type."
        return self.current.type == t

    def next_is(self, t: TokenType) -> bool:
        "Return whether the next token is of the given type."
        return self.next.type == t

    def expect_next(self, t: TokenType) -> None:
        """
        Expect the next token to be of the given type.

        If it is, the iterator will be advanced.
        If it is not, a `SyntaxError` will be raised.
        """

        if self.next.type != t:
            msg = f"Expected next token to be {t}, got {self.next.type}"
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

        self._prefix_parse_fns: dict[TokenType, PrefixParseFn] = {
            TokenType.IDENTIFIER: self._parse_identifier,
            TokenType.INTEGER: self._parse_integer_literal,
            TokenType.STRING: self._parse_string_literal,
            TokenType.FUNCTION: self._parse_function_literal,
            TokenType.BANG: self._parse_prefix_expression,
            TokenType.MINUS: self._parse_prefix_expression,
            TokenType.TRUE: self._parse_boolean,
            TokenType.FALSE: self._parse_boolean,
            TokenType.LEFT_PAREN: self._parse_grouped_expression,
            TokenType.IF: self._parse_if_expression,
        }

        self._infix_parse_fns: dict[TokenType, InfixParseFn] = {
            TokenType.EQUAL: self._parse_infix_expression,
            TokenType.NOT_EQUAL: self._parse_infix_expression,
            TokenType.LESSER_THAN: self._parse_infix_expression,
            TokenType.GREATER_THAN: self._parse_infix_expression,
            TokenType.PLUS: self._parse_infix_expression,
            TokenType.MINUS: self._parse_infix_expression,
            TokenType.SLASH: self._parse_infix_expression,
            TokenType.ASTERISK: self._parse_infix_expression,
            TokenType.LEFT_PAREN: self._parse_call_expression,
        }

    def parse_program(self) -> Program:
        program = Program([])

        while not self._tokens.current_is(TokenType.END_OF_FILE):
            program.statements.append(self._parse_statement())
            self._tokens.advance()

        return program

    def _parse_statement(self) -> Statement:
        match self._tokens.current.type:
            case TokenType.LET:
                return self._parse_let_statement()
            case TokenType.RETURN:
                return self._parse_return_statement()
            case _:
                return self._parse_expression_statement()

    def _parse_let_statement(self) -> LetStatement:
        # let
        token = self._tokens.current

        # let <name>
        self._tokens.expect_next(TokenType.IDENTIFIER)
        name = self._parse_identifier()

        # let <name> =
        self._tokens.expect_next(TokenType.ASSIGN)
        self._tokens.advance()

        # let <name> = <value>
        value = self._parse_expression()

        # let <name> = value>;
        self._tokens.expect_next(TokenType.SEMICOLON)

        return LetStatement(token, name, value)

    def _parse_return_statement(self) -> ReturnStatement:
        token = self._tokens.current
        self._tokens.advance()

        # return <value>
        value = self._parse_expression()

        # return <value>;
        self._tokens.expect_next(TokenType.SEMICOLON)

        return ReturnStatement(token, value)

    def _parse_expression_statement(self) -> ExpressionStatement:
        expr = self._parse_expression()

        if self._tokens.next_is(TokenType.SEMICOLON):
            self._tokens.advance()

        return ExpressionStatement(self._tokens.current, expr)

    def _parse_expression(self, precedence: Precedence = Precedence.LOWEST) -> Expression:
        prefix_fn = self._prefix_parse_fns.get(self._tokens.current.type)
        if prefix_fn is None:
            msg = f"No prefix parse function for {self._tokens.current.type}"
            raise SyntaxError(msg)
        left = prefix_fn()

        while (
            self._tokens.next.type != TokenType.SEMICOLON and precedence < self._next_precedence()
        ):
            infix_fn = self._infix_parse_fns.get(self._tokens.next.type)
            if infix_fn is None:
                return left

            self._tokens.advance()
            left = infix_fn(left)

        return left

    def _parse_if_expression(self) -> Expression:
        # if
        token = self._tokens.current

        # if (
        self._tokens.expect_next(TokenType.LEFT_PAREN)
        self._tokens.advance()

        # if (<condition>
        condition = self._parse_expression()

        # if (<condition>) {
        self._tokens.expect_next(TokenType.RIGHT_PAREN)
        self._tokens.expect_next(TokenType.LEFT_BRACE)

        # if (<condition>) { <consequence> }
        consequence = self._parse_block_statement()

        # if (<condition>) { <consequence> } else { <alternative> }
        alternative = None
        if self._tokens.next.type == TokenType.ELSE:
            self._tokens.advance()
            self._tokens.expect_next(TokenType.LEFT_BRACE)
            alternative = self._parse_block_statement()

        return IfExpression(token, condition, consequence, alternative)

    def _parse_block_statement(self) -> BlockStatement:
        token = self._tokens.current

        self._tokens.advance()

        statements: list[Statement] = []
        while self._tokens.current.type not in (TokenType.RIGHT_BRACE, TokenType.END_OF_FILE):
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
        self._tokens.expect_next(TokenType.RIGHT_PAREN)
        return expr

    def _parse_function_literal(self) -> FunctionLiteral:
        token = self._tokens.current

        self._tokens.expect_next(TokenType.LEFT_PAREN)
        params = self._parse_function_parameters()

        self._tokens.expect_next(TokenType.LEFT_BRACE)
        body = self._parse_block_statement()

        return FunctionLiteral(token, params, body)

    def _parse_function_parameters(self) -> list[Identifier]:
        params: list[Identifier] = []

        if self._tokens.next.type == TokenType.RIGHT_PAREN:
            self._tokens.advance()
            return params

        self._tokens.advance()

        params.append(self._parse_identifier())

        while self._tokens.next.type == TokenType.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            params.append(self._parse_identifier())

        self._tokens.expect_next(TokenType.RIGHT_PAREN)

        return params

    def _parse_string_literal(self) -> StringLiteral:
        return StringLiteral(self._tokens.current, self._tokens.current.literal)

    def _parse_call_expression(self, fn: Expression) -> CallExpression:
        if not isinstance(fn, Identifier | FunctionLiteral):
            msg = "Expected identifier or function literal for function call"
            raise TypeError(msg)

        token = self._tokens.current
        args = self._parse_call_arguments()
        return CallExpression(token, fn, args)

    def _parse_call_arguments(self) -> list[Expression]:
        args: list[Expression] = []

        if self._tokens.next.type == TokenType.RIGHT_PAREN:
            self._tokens.advance()
            return args

        self._tokens.advance()

        args.append(self._parse_expression())

        while self._tokens.next.type == TokenType.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            args.append(self._parse_expression())

        self._tokens.expect_next(TokenType.RIGHT_PAREN)

        return args

    def _parse_identifier(self) -> Identifier:
        return Identifier(self._tokens.current, self._tokens.current.literal)

    def _parse_integer_literal(self) -> IntegerLiteral:
        return IntegerLiteral(self._tokens.current, int(self._tokens.current.literal))

    def _parse_boolean(self) -> BooleanLiteral:
        return BooleanLiteral(self._tokens.current, self._tokens.current.type == TokenType.TRUE)

    def _current_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.current.type, Precedence.LOWEST)

    def _next_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.next.type, Precedence.LOWEST)
