from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING

from monk.ast import (
    BlockStmt,
    Bool,
    CallExpr,
    Expr,
    ExprStmt,
    FnLiteral,
    Ident,
    IfExpr,
    InfixExpr,
    IntLiteral,
    LetStmt,
    PrefixExpr,
    Program,
    ReturnStmt,
    Stmt,
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


PrefixParseFn = Callable[[], Expr]
"""A prefix parsing function produces a node when it matches a certain prefix."""

InfixParseFn = Callable[[Expr], Expr]
"""
An infix parsing function produces a node when it matches in between two expressions.

Infix parsing functions take in the expression on the left. It is up to the function to
consume the expression on the right.
"""


class Parser:
    "A Pratt parser for Monkey."

    def __init__(self, lexer: Lexer) -> None:
        self._tokens = TokenIterator(lexer)

        self._prefix_parse_fns: dict[TokenKind, PrefixParseFn] = {
            TokenKind.IDENT: self._parse_ident,
            TokenKind.INT: self._parse_int,
            TokenKind.BANG: self._parse_prefix_expr,
            TokenKind.MINUS: self._parse_prefix_expr,
            TokenKind.TRUE: self._parse_bool,
            TokenKind.FALSE: self._parse_bool,
            TokenKind.LPAREN: self._parse_grouped_expr,
            TokenKind.IF: self._parse_if_expr,
            TokenKind.FUNCTION: self._parse_fn_literal,
        }

        self._infix_parse_fns: dict[TokenKind, InfixParseFn] = {
            TokenKind.EQ: self._parse_infix_expr,
            TokenKind.NOT_EQ: self._parse_infix_expr,
            TokenKind.LT: self._parse_infix_expr,
            TokenKind.GT: self._parse_infix_expr,
            TokenKind.PLUS: self._parse_infix_expr,
            TokenKind.MINUS: self._parse_infix_expr,
            TokenKind.SLASH: self._parse_infix_expr,
            TokenKind.ASTERISK: self._parse_infix_expr,
            TokenKind.LPAREN: self._parse_call_expr,
        }

    def parse_program(self) -> Program:
        prog = Program([])

        while not self._tokens.current_is(TokenKind.EOF):
            prog.stmts.append(self._parse_stmt())
            self._tokens.advance()

        return prog

    def _parse_stmt(self) -> Stmt:
        match self._tokens.current.kind:
            case TokenKind.LET:
                return self._parse_let_stmt()
            case TokenKind.RETURN:
                return self._parse_return_stmt()
            case _:
                return self._parse_expr_stmt()

    def _parse_let_stmt(self) -> LetStmt:
        # let
        token = self._tokens.current

        # let <name>
        self._tokens.expect_next(TokenKind.IDENT)
        name = self._parse_ident()

        # let <name> =
        self._tokens.expect_next(TokenKind.ASSIGN)
        self._tokens.advance()

        # let <name> = <value>
        value = self._parse_expr()

        # let <name> = value>;
        self._tokens.expect_next(TokenKind.SEMICOLON)

        return LetStmt(token, name, value)

    def _parse_return_stmt(self) -> ReturnStmt:
        token = self._tokens.current
        self._tokens.advance()

        # return <value>
        value = self._parse_expr()

        # return <value>;
        self._tokens.expect_next(TokenKind.SEMICOLON)

        return ReturnStmt(token, value)

    def _parse_expr_stmt(self) -> ExprStmt:
        expr = self._parse_expr()

        if self._tokens.next_is(TokenKind.SEMICOLON):
            self._tokens.advance()

        return ExprStmt(self._tokens.current, expr)

    def _parse_expr(self, precedence: Precedence = Precedence.LOWEST) -> Expr:
        prefix = self._prefix_parse_fns.get(self._tokens.current.kind)
        if prefix is None:
            msg = f"No prefix parse function for {self._tokens.current.kind}"
            raise SyntaxError(msg)
        left = prefix()

        while (
            self._tokens.next.kind != TokenKind.SEMICOLON and precedence < self._next_precedence()
        ):
            infix = self._infix_parse_fns.get(self._tokens.next.kind)
            if infix is None:
                return left

            self._tokens.advance()
            left = infix(left)

        return left

    def _parse_if_expr(self) -> Expr:
        # if
        token = self._tokens.current

        # if (
        self._tokens.expect_next(TokenKind.LPAREN)
        self._tokens.advance()

        # if (<condition>
        condition = self._parse_expr()

        # if (<condition>) {
        self._tokens.expect_next(TokenKind.RPAREN)
        self._tokens.expect_next(TokenKind.LBRACE)

        # if (<condition>) { <consequence> }
        consequence = self._parse_block_stmt()

        # if (<condition>) { <consequence> } else { <alternative> }
        alternative = None
        if self._tokens.next.kind == TokenKind.ELSE:
            self._tokens.advance()
            self._tokens.expect_next(TokenKind.LBRACE)
            alternative = self._parse_block_stmt()

        return IfExpr(token, condition, consequence, alternative)

    def _parse_block_stmt(self) -> BlockStmt:
        token = self._tokens.current

        self._tokens.advance()

        stmts: list[Stmt] = []
        while self._tokens.current.kind not in (TokenKind.RBRACE, TokenKind.EOF):
            stmts.append(self._parse_stmt())
            self._tokens.advance()

        return BlockStmt(token, stmts)

    def _parse_prefix_expr(self) -> Expr:
        token = self._tokens.current
        operator = token.literal

        self._tokens.advance()
        right = self._parse_expr(Precedence.PREFIX)

        return PrefixExpr(token, operator, right)

    def _parse_infix_expr(self, left: Expr) -> Expr:
        token = self._tokens.current
        operator = token.literal

        precedence = self._current_precedence()
        self._tokens.advance()
        right = self._parse_expr(precedence)

        return InfixExpr(token, left, operator, right)

    def _parse_grouped_expr(self) -> Expr:
        self._tokens.advance()
        expr = self._parse_expr()
        self._tokens.expect_next(TokenKind.RPAREN)
        return expr

    def _parse_fn_literal(self) -> FnLiteral:
        token = self._tokens.current

        self._tokens.expect_next(TokenKind.LPAREN)
        params = self._parse_fn_params()

        self._tokens.expect_next(TokenKind.LBRACE)
        body = self._parse_block_stmt()

        return FnLiteral(token, params, body)

    def _parse_fn_params(self) -> list[Ident]:
        params: list[Ident] = []

        if self._tokens.next.kind == TokenKind.RPAREN:
            self._tokens.advance()
            return params

        self._tokens.advance()

        params.append(self._parse_ident())

        while self._tokens.next.kind == TokenKind.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            params.append(self._parse_ident())

        self._tokens.expect_next(TokenKind.RPAREN)

        return params

    def _parse_call_expr(self, fn: Expr) -> CallExpr:
        if not isinstance(fn, Ident | FnLiteral):
            msg = "Expected identifier or function literal for function call"
            raise TypeError(msg)

        token = self._tokens.current
        args = self._parse_call_args()
        return CallExpr(token, fn, args)

    def _parse_call_args(self) -> list[Expr]:
        args: list[Expr] = []

        if self._tokens.next.kind == TokenKind.RPAREN:
            self._tokens.advance()
            return args

        self._tokens.advance()

        args.append(self._parse_expr())

        while self._tokens.next.kind == TokenKind.COMMA:
            self._tokens.advance()
            self._tokens.advance()
            args.append(self._parse_expr())

        self._tokens.expect_next(TokenKind.RPAREN)

        return args

    def _parse_ident(self) -> Ident:
        return Ident(self._tokens.current, self._tokens.current.literal)

    def _parse_int(self) -> IntLiteral:
        return IntLiteral(self._tokens.current, int(self._tokens.current.literal))

    def _parse_bool(self) -> Bool:
        return Bool(self._tokens.current, self._tokens.current.kind == TokenKind.TRUE)

    def _current_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.current.kind, Precedence.LOWEST)

    def _next_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._tokens.next.kind, Precedence.LOWEST)
