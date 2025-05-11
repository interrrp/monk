from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from monk.token import Token


class Node(ABC):
    @abstractmethod
    def token_literal(self) -> str: ...

    @abstractmethod
    def __str__(self) -> str: ...


class Stmt(Node): ...


class Expr(Node): ...


@dataclass(frozen=True)
class Program(Node):
    stmts: list[Stmt]

    @override
    def token_literal(self) -> str:
        return self.stmts[0].token_literal()

    @override
    def __str__(self) -> str:
        return "\n".join(str(s) for s in self.stmts)


@dataclass(frozen=True)
class Ident(Expr):
    token: Token
    value: str

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LetStmt(Stmt):
    token: Token
    name: Ident
    value: Expr

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal()} {self.name.value} = {self.value};"


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    token: Token
    value: Expr

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal()} {self.value}"


@dataclass(frozen=True)
class ExprStmt(Stmt):
    token: Token
    expr: Expr

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return str(self.expr) + ";"


@dataclass(frozen=True)
class IntLiteral(Expr):
    token: Token
    value: int

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.token.literal


@dataclass(frozen=True)
class PrefixExpr(Expr):
    token: Token
    operator: str
    right: Expr

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"({self.operator}{self.right})"


@dataclass(frozen=True)
class InfixExpr(Expr):
    token: Token
    left: Expr
    operator: str
    right: Expr

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass(frozen=True)
class Bool(Expr):
    token: Token
    value: bool

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.token.literal


@dataclass(frozen=True)
class BlockStmt(Stmt):
    token: Token
    stmts: list[Stmt]

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{{\n    {'\n    '.join(str(s) for s in self.stmts)}\n}}"


@dataclass(frozen=True)
class IfExpr(Expr):
    token: Token
    condition: Expr
    consequence: BlockStmt
    alternative: BlockStmt | None

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        s = f"if {self.condition} {self.consequence}"

        if self.alternative is not None:
            s += f" else {self.alternative}"

        return s


@dataclass(frozen=True)
class FnLiteral(Expr):
    token: Token
    params: list[Ident]
    body: BlockStmt

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal}({_join_commas(self.params)}) {self.body}"


@dataclass(frozen=True)
class CallExpr(Expr):
    token: Token
    fn: Ident | FnLiteral
    args: list[Expr]

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.fn}({_join_commas(self.args)})"


def _join_commas(xs: Sequence[Expr]) -> str:
    return ", ".join(str(x) for x in xs)
