from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, final, override

from monk.utils import join_commas

if TYPE_CHECKING:
    from monk.ast import BlockStatement, Identifier


class ObjectType(Enum):
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    FUNCTION = "FUNCTION"

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


@final
class Environment:
    def __init__(self, outer: Environment | None = None) -> None:
        self._outer = outer
        self._map: dict[str, Object] = {}

    def __getitem__(self, name: str) -> Object:
        if name in self._map:
            return self._map[name]
        if self._outer is not None:
            return self._outer[name]
        msg = f"Unknown identifier {name}"
        raise KeyError(msg)

    def __setitem__(self, name: str, obj: Object) -> None:
        self._map[name] = obj
