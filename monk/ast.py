from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from monk.utils import join_commas

if TYPE_CHECKING:
    from monk.token import Token


class Node(ABC):
    @abstractmethod
    def token_literal(self) -> str: ...

    @abstractmethod
    @override
    def __str__(self) -> str: ...


class Statement(Node, ABC):
    """A node that does not produce any value."""


class Expression(Node, ABC):
    """A node that produces a value."""


@dataclass(frozen=True)
class Program(Node):
    statements: list[Statement]

    @override
    def token_literal(self) -> str:
        return self.statements[0].token_literal()

    @override
    def __str__(self) -> str:
        return "\n".join(str(s) for s in self.statements)


@dataclass(frozen=True)
class LetStatement(Statement):
    token: Token
    name: Identifier
    value: Expression

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal()} {self.name.value} = {self.value};"


@dataclass(frozen=True)
class ReturnStatement(Statement):
    token: Token
    value: Expression

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal()} {self.value}"


@dataclass(frozen=True)
class ExpressionStatement(Statement):
    token: Token
    expression: Expression

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return str(self.expression) + ";"


@dataclass(frozen=True)
class BlockStatement(Statement):
    token: Token
    statements: list[Statement]

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{{\n    {'\n    '.join(str(s) for s in self.statements)}\n}}"


@dataclass(frozen=True)
class Identifier(Expression):
    token: Token
    value: str

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    token: Token
    value: int

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.token.literal


@dataclass(frozen=True)
class BooleanLiteral(Expression):
    token: Token
    value: bool

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return self.token.literal


@dataclass(frozen=True)
class StringLiteral(Expression):
    token: Token
    value: str

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f'"{self.value}"'


@dataclass(frozen=True)
class FunctionLiteral(Expression):
    token: Token
    parameters: list[Identifier]
    body: BlockStatement

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.token_literal}({join_commas(self.parameters)}) {self.body}"


@dataclass(frozen=True)
class PrefixExpression(Expression):
    token: Token
    operator: str
    right: Expression

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"({self.operator}{self.right})"


@dataclass(frozen=True)
class InfixExpression(Expression):
    token: Token
    left: Expression
    operator: str
    right: Expression

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass(frozen=True)
class IfExpression(Expression):
    token: Token
    condition: Expression
    consequence: BlockStatement
    alternative: BlockStatement | None

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
class CallExpression(Expression):
    token: Token
    function: Identifier | FunctionLiteral
    arguments: list[Expression]

    @override
    def token_literal(self) -> str:
        return self.token.literal

    @override
    def __str__(self) -> str:
        return f"{self.function}({join_commas(self.arguments)})"
