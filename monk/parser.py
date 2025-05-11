from collections.abc import Callable
from enum import IntEnum

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
from monk.lexer import Lexer
from monk.token import Token, TokenKind

PrefixParseFn = Callable[[], Expr | None]
InfixParseFn = Callable[[Expr | None], Expr | None]


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


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

        self._current_token = Token(TokenKind.EOF, "")
        self._next_token = Token(TokenKind.EOF, "")
        self._advance()
        self._advance()

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

    def _advance(self) -> None:
        self._current_token = self._next_token
        self._next_token = next(self._lexer)

    def parse_program(self) -> Program:
        prog = Program([])

        while self._current_token.kind != TokenKind.EOF:
            stmt = self._parse_stmt()
            if stmt is not None:
                prog.stmts.append(stmt)
            self._advance()

        return prog

    def _parse_stmt(self) -> Stmt | None:
        match self._current_token.kind:
            case TokenKind.LET:
                return self._parse_let_stmt()
            case TokenKind.RETURN:
                return self._parse_return_stmt()
            case _:
                return self._parse_expr_stmt()

    def _parse_let_stmt(self) -> LetStmt | None:
        token = self._current_token

        self._expect_next(TokenKind.IDENT)
        name = Ident(self._current_token, self._current_token.literal)

        self._expect_next(TokenKind.ASSIGN)
        self._advance()

        value = self._parse_expr()
        if value is None:
            msg = "Expected value for let statement"
            raise SyntaxError(msg)

        if self._next_token.kind == TokenKind.SEMICOLON:
            self._advance()

        return LetStmt(token, name, value)

    def _parse_return_stmt(self) -> ReturnStmt | None:
        token = self._current_token

        self._advance()

        value = self._parse_expr()
        if value is None:
            msg = "Expected value for return statement"
            raise SyntaxError(msg)

        if self._next_token.kind == TokenKind.SEMICOLON:
            self._advance()

        return ReturnStmt(token, value)

    def _parse_if_expr(self) -> Expr | None:
        token = self._current_token
        self._expect_next(TokenKind.LPAREN)
        self._advance()

        condition = self._parse_expr()
        if condition is None:
            return None

        self._expect_next(TokenKind.RPAREN)
        self._expect_next(TokenKind.LBRACE)

        consequence = self._parse_block_stmt()
        if consequence is None:
            msg = "Expected consequence to if statement"
            raise SyntaxError(msg)

        alternative = None
        if self._next_token.kind == TokenKind.ELSE:
            self._advance()
            self._expect_next(TokenKind.LBRACE)
            alternative = self._parse_block_stmt()
            if alternative is None:
                msg = "Expected alternative to if statement"
                raise SyntaxError(msg)

        return IfExpr(token, condition, consequence, alternative)

    def _parse_block_stmt(self) -> BlockStmt | None:
        token = self._current_token

        self._advance()

        stmts: list[Stmt] = []
        while self._current_token.kind not in (TokenKind.RBRACE, TokenKind.EOF):
            stmt = self._parse_stmt()
            if stmt is not None:
                stmts.append(stmt)
            self._advance()

        return BlockStmt(token, stmts)

    def _parse_expr_stmt(self) -> ExprStmt | None:
        token = self._current_token
        expr = self._parse_expr()
        if self._next_token.kind == TokenKind.SEMICOLON:
            self._advance()
        if expr is None:
            return None
        return ExprStmt(token, expr)

    def _parse_expr(self, precedence: Precedence = Precedence.LOWEST) -> Expr | None:
        prefix = self._prefix_parse_fns.get(self._current_token.kind)
        if prefix is None:
            msg = f"No prefix parse function for {self._current_token.kind}"
            raise SyntaxError(msg)
        left = prefix()

        while self._next_token.kind != TokenKind.SEMICOLON and precedence < self._next_precedence():
            infix = self._infix_parse_fns.get(self._next_token.kind)
            if infix is None:
                return left

            self._advance()
            left = infix(left)

        return left

    def _parse_prefix_expr(self) -> Expr | None:
        token = self._current_token
        operator = token.literal

        self._advance()

        right = self._parse_expr(Precedence.PREFIX)
        if right is None:
            return None

        return PrefixExpr(token, operator, right)

    def _parse_infix_expr(self, left: Expr | None) -> Expr | None:
        token = self._current_token
        operator = token.literal

        precedence = self._current_precedence()
        self._advance()
        right = self._parse_expr(precedence)

        if left is None or right is None:
            return None

        return InfixExpr(token, left, operator, right)

    def _parse_grouped_expr(self) -> Expr | None:
        self._advance()
        expr = self._parse_expr()
        self._expect_next(TokenKind.RPAREN)
        return expr

    def _parse_fn_literal(self) -> FnLiteral | None:
        token = self._current_token

        self._expect_next(TokenKind.LPAREN)
        params = self._parse_fn_params()

        self._expect_next(TokenKind.LBRACE)
        body = self._parse_block_stmt()
        if body is None:
            msg = "Expected body for function literal"
            raise SyntaxError(msg)

        return FnLiteral(token, params, body)

    def _parse_fn_params(self) -> list[Ident]:
        params: list[Ident] = []

        if self._next_token.kind == TokenKind.RPAREN:
            self._advance()
            return params

        self._advance()

        params.append(self._parse_ident())

        while self._next_token.kind == TokenKind.COMMA:
            self._advance()
            self._advance()
            params.append(self._parse_ident())

        self._expect_next(TokenKind.RPAREN)

        return params

    def _parse_call_expr(self, fn: Expr | None) -> CallExpr:
        if not isinstance(fn, Ident | FnLiteral):
            msg = "Expected identifier or function literal for function call"
            raise TypeError(msg)

        token = self._current_token
        args = self._parse_call_args()
        return CallExpr(token, fn, args)

    def _parse_call_args(self) -> list[Expr]:
        args: list[Expr] = []

        if self._next_token.kind == TokenKind.RPAREN:
            self._advance()
            return args

        self._advance()

        expr = self._parse_expr()
        if expr is not None:
            args.append(expr)

        while self._next_token.kind == TokenKind.COMMA:
            self._advance()
            self._advance()
            expr = self._parse_expr()
            if expr is not None:
                args.append(expr)

        self._expect_next(TokenKind.RPAREN)

        return args

    def _parse_ident(self) -> Ident:
        return Ident(self._current_token, self._current_token.literal)

    def _parse_int(self) -> IntLiteral:
        return IntLiteral(self._current_token, int(self._current_token.literal))

    def _parse_bool(self) -> Bool:
        return Bool(self._current_token, self._current_token.kind == TokenKind.TRUE)

    def _current_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._current_token.kind, Precedence.LOWEST)

    def _next_precedence(self) -> Precedence:
        return _PRECEDENCES.get(self._next_token.kind, Precedence.LOWEST)

    def _expect_next(self, kind: TokenKind) -> None:
        if self._next_token.kind == kind:
            self._advance()
        else:
            msg = f"Expected next token to be {kind}, got {self._next_token}"
            raise SyntaxError(msg)
