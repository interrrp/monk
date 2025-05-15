from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, override

from monk.utils import join_commas

if TYPE_CHECKING:
    from monk.ast import BlockStatement, Identifier


class ObjectType(Enum):
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    FUNCTION = "FUNCTION"
    STRING = "STRING"
    ARRAY = "ARRAY"
    BUILTIN = "BUILTIN"

    @override
    def __str__(self) -> str:
        return self.value


class Object(ABC):
    @property
    @abstractmethod
    def type(self) -> ObjectType: ...

    @abstractmethod
    @override
    def __str__(self) -> str: ...


@dataclass(frozen=True)
class Integer(Object):
    value: int

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.INTEGER

    @override
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Boolean(Object):
    value: bool

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    @override
    def __str__(self) -> str:
        return str(self.value).lower()


@dataclass(frozen=True)
class Null(Object):
    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.NULL

    @override
    def __str__(self) -> str:
        return "null"


@dataclass(frozen=True)
class ReturnValue(Object):
    value: Object

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.RETURN_VALUE

    @override
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Function(Object):
    parameters: list[Identifier]
    body: BlockStatement
    environment: Environment

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.FUNCTION

    @override
    def __str__(self) -> str:
        return f"fn({join_commas(self.parameters)}) {self.body}"


@dataclass(frozen=True)
class String(Object):
    value: str

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.STRING

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Array(Object):
    values: list[Object]

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.ARRAY

    @override
    def __str__(self) -> str:
        return f"[{join_commas([str(v) for v in self.values])}]"


class BuiltinFunction(Protocol):
    def __call__(self, *args: Object) -> Object: ...


@dataclass(frozen=True)
class Builtin(Object):
    function: BuiltinFunction

    @property
    @override
    def type(self) -> ObjectType:
        return ObjectType.BUILTIN

    @override
    def __str__(self) -> str:
        return "builtin function"


Environment = dict[str, Object]
