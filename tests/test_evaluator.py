import re

import pytest

from monk.evaluator import NULL, evaluate
from monk.lexer import Lexer
from monk.object import Boolean, Environment, Function, Integer, Object, String
from monk.parser import Parser


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("5", 5),
        ("10", 10),
        ("-10", -10),
        ("-0", 0),
    ],
)
def test_int_exprs(code: str, expected_val: int) -> None:
    result = do_eval(code)
    assert_integer_obj(result, expected_val)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("true", True),
        ("false", False),
        ("1 < 2", True),
        ("1 > 2", False),
        ("1 < 1", False),
        ("1 > 1", False),
        ("1 == 1", True),
        ("1 != 1", False),
        ("1 == 2", False),
        ("1 != 2", True),
        ("true == true", True),
        ("false == false", True),
        ("true == false", False),
        ("true != false", True),
        ("false != true", True),
        ("(1 < 2) == true", True),
        ("(1 < 2) == false", False),
        ("(1 > 2) == true", False),
        ("(1 > 2) == false", True),
    ],
)
def test_bool_exprs(code: str, expected_val: bool) -> None:
    result = do_eval(code)
    assert_boolean_obj(result, expected_val)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("!true", False),
        ("!false", True),
        ("!5", False),
        ("!!true", True),
        ("!!false", False),
        ("!!5", True),
    ],
)
def test_bang(code: str, expected_val: bool) -> None:
    result = do_eval(code)
    assert_boolean_obj(result, expected_val)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("5", 5),
        ("10", 10),
        ("-5", -5),
        ("-10", -10),
        ("5 + 5 + 5 + 5 - 10", 10),
        ("2 * 2 * 2 * 2 * 2", 32),
        ("-50 + 100 + -50", 0),
        ("5 * 2 + 10", 20),
        ("5 + 2 * 10", 25),
        ("20 + 2 * -10", 0),
        ("50 / 2 * 2 + 10", 60),
        ("2 * (5 + 10)", 30),
        ("3 * 3 * 3 + 10", 37),
        ("3 * (3 * 3) + 10", 37),
        ("(5 + 10 * 2 + 15 / 3) * 2 + -10", 50),
    ],
)
def test_int_infix_exprs(code: str, expected_val: int) -> None:
    result = do_eval(code)
    assert_integer_obj(result, expected_val)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("if (true) { 10 }", 10),
        ("if (false) { 10 }", None),
        ("if (1) { 10 }", 10),
        ("if (1 < 2) { 10 }", 10),
        ("if (1 > 2) { 10 }", None),
        ("if (1 > 2) { 10 } else { 20 }", 20),
        ("if (1 < 2) { 10 } else { 20 }", 10),
    ],
)
def test_if_exprs(code: str, expected_val: int | None) -> None:
    result = do_eval(code)
    if expected_val is None:
        assert result == NULL
    else:
        assert result == Integer(expected_val)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("return 10;", 10),
        ("return 10; 9;", 10),
        ("return 2 * 5; 9;", 10),
        ("9; return 2 * 5; 9;", 10),
        (
            """
            if (10 > 1) {
                if (10 > 1) {
                    return 10;
                }
                return 1;
            }
            """,
            10,
        ),
    ],
)
def test_return_statements(code: str, expected_val: int) -> None:
    result = do_eval(code)
    assert_integer_obj(result, expected_val)


@pytest.mark.parametrize(
    ("code", "expected_msg"),
    [
        (
            "5 + true;",
            "Type mismatch: INTEGER + BOOLEAN",
        ),
        (
            "5 + true; 5;",
            "Type mismatch: INTEGER + BOOLEAN",
        ),
        (
            "-true",
            "Unknown operator: -BOOLEAN",
        ),
        (
            "true + false;",
            "Unknown operator: BOOLEAN + BOOLEAN",
        ),
        (
            "5; true + false; 5",
            "Unknown operator: BOOLEAN + BOOLEAN",
        ),
        (
            "if (10 > 1) { true + false; }",
            "Unknown operator: BOOLEAN + BOOLEAN",
        ),
        (
            '"hello" - "world"',
            "Unknown operator: STRING - STRING",
        ),
        (
            """
            if (10 > 1) {
                if (10 > 1) {
                    return true + false;
                }
                return 1;
            }
            """,
            "Unknown operator: BOOLEAN + BOOLEAN",
        ),
    ],
)
def test_errors(code: str, expected_msg: str) -> None:
    with pytest.raises((SyntaxError, TypeError), match=re.escape(expected_msg)):
        _ = do_eval(code)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("let a = 5; a;", 5),
        ("let a = 5 * 5; a;", 25),
        ("let a = 5; let b = a; b;", 5),
        ("let a = 5; let b = a; let c = a + b + 5; c;", 15),
    ],
)
def test_let_statements(code: str, expected_val: int) -> None:
    result = do_eval(code)
    assert_integer_obj(result, expected_val)


def test_function_objects() -> None:
    result = do_eval("fn(x) { x + 2; }")
    assert isinstance(result, Function)
    assert len(result.parameters) == 1
    assert str(result.parameters[0]) == "x"
    assert "(x + 2)" in str(result.body)


@pytest.mark.parametrize(
    ("code", "expected_val"),
    [
        ("let identity = fn(x) { x; }; identity(5);", 5),
        ("let identity = fn(x) { return x; }; identity(5);", 5),
        ("let double = fn(x) { x * 2; }; double(5);", 10),
        ("let add = fn(x, y) { x + y; }; add(5, 5);", 10),
        ("let add = fn(x, y) { x + y; }; add(5 + 5, add(5, 5));", 20),
        ("fn(x) { x; }(5)", 5),
    ],
)
def test_function_application(code: str, expected_val: int) -> None:
    result = do_eval(code)
    assert_integer_obj(result, expected_val)


def test_strings() -> None:
    result = do_eval('"hello world"')
    assert isinstance(result, String)
    assert result.value == "hello world"


def test_string_concatenation() -> None:
    result = do_eval('"hello" + " " + "world"')
    assert isinstance(result, String)
    assert result.value == "hello world"


def assert_integer_obj(obj: Object, val: int) -> None:
    assert isinstance(obj, Integer)
    assert obj.value == val


def assert_boolean_obj(obj: Object, val: bool) -> None:
    assert isinstance(obj, Boolean)
    assert obj.value == val


def do_eval(code: str) -> Object:
    lexer = Lexer(code)
    parser = Parser(lexer)
    program = parser.parse_program()
    env = Environment()
    return evaluate(program, env)
