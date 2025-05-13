import pytest

from monk.ast import (
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
    StringLiteral,
)
from monk.lexer import lex
from monk.parser import Parser


def parse_program(code: str) -> Program:
    lexer = lex(code)
    parser = Parser(lexer)
    return parser.parse_program()


def test_let_statements() -> None:
    code = """
        let x = 5;
        let y = 10;
        let foobar = 838383;
    """
    expected_vars = {
        "x": 5,
        "y": 10,
        "foobar": 838383,
    }

    program = parse_program(code)
    assert len(program.statements) == len(expected_vars)

    for i, (expected_name, expected_value) in enumerate(expected_vars.items()):
        statement = program.statements[i]

        assert isinstance(statement, LetStatement)
        assert statement.token_literal() == "let"
        assert_identifier(statement.name, expected_name)
        assert_int_literal(statement.value, expected_value)


def test_return_statements() -> None:
    code = """
        return 5;
        return 10;
        return 993322;
    """
    expected_return_vals = [5, 10, 993322]

    program = parse_program(code)
    assert len(program.statements) == len(expected_return_vals)

    for i, expected_return_val in enumerate(expected_return_vals):
        statement = program.statements[i]
        assert isinstance(statement, ReturnStatement)
        assert statement.token_literal() == "return"
        assert_int_literal(statement.value, expected_return_val)


def test_ident_exprs() -> None:
    name = "foobar"

    program = parse_program(f"{name};")
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert_identifier(statement.expression, name)


def test_int() -> None:
    num = 42

    program = parse_program(f"{num};")
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert_int_literal(statement.expression, num)


def test_bool() -> None:
    program = parse_program("true; false;")

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, BooleanLiteral)
    assert statement.expression.value

    statement = program.statements[1]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, BooleanLiteral)
    assert not statement.expression.value


@pytest.mark.parametrize(
    ("code", "operator", "value"),
    [
        ("!5;", "!", 5),
        ("-15;", "-", 15),
    ],
)
def test_prefix_exprs(code: str, operator: str, value: int) -> None:
    program = parse_program(code)
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, PrefixExpression)
    assert statement.expression.operator == operator
    assert_int_literal(statement.expression.right, value)


@pytest.mark.parametrize(
    ("code", "left", "operator", "right"),
    [
        ("5 + 5;", 5, "+", 5),
        ("5 - 5;", 5, "-", 5),
        ("5 * 5;", 5, "*", 5),
        ("5 / 5;", 5, "/", 5),
        ("5 > 5;", 5, ">", 5),
        ("5 < 5;", 5, "<", 5),
        ("5 == 5;", 5, "==", 5),
        ("5 != 5;", 5, "!=", 5),
    ],
)
def test_infix_exprs(code: str, left: int, operator: str, right: int) -> None:
    program = parse_program(code)
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, InfixExpression)
    assert statement.expression.operator == operator
    assert_int_literal(statement.expression.left, left)
    assert_int_literal(statement.expression.right, right)


@pytest.mark.parametrize(
    ("code", "ast"),
    [
        ("1 + (2 + 3) + 4;", "((1 + (2 + 3)) + 4);"),
        ("(5 + 5) * 2;", "((5 + 5) * 2);"),
        ("2 / (5 + 5);", "(2 / (5 + 5));"),
        ("-(5 + 5);", "(-(5 + 5));"),
        ("!(true == true);", "(!(true == true));"),
    ],
)
def test_grouped_exprs(code: str, ast: str) -> None:
    program = parse_program(code)
    assert str(program) == ast


def test_if_statements() -> None:
    program = parse_program("if (4 > 2) { x } else { y };")
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, IfExpression)
    if_stmt = statement.expression

    assert isinstance(if_stmt.condition, InfixExpression)

    assert len(if_stmt.consequence.statements) == 1
    consequence = if_stmt.consequence.statements[0]
    assert isinstance(consequence, ExpressionStatement)
    assert_identifier(consequence.expression, "x")

    assert if_stmt.alternative is not None
    assert len(if_stmt.alternative.statements) == 1
    alternative = if_stmt.alternative.statements[0]
    assert isinstance(alternative, ExpressionStatement)
    assert_identifier(alternative.expression, "y")


def test_fn_literals() -> None:
    program = parse_program("fn(x, y) { x + y; }")
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, FunctionLiteral)

    fn = statement.expression
    num_params = 2
    assert len(fn.parameters) == num_params
    assert fn.parameters[0].value == "x"
    assert fn.parameters[1].value == "y"

    assert str(fn.body) == "{\n    (x + y);\n}"


def test_call_exprs() -> None:
    program = parse_program("add(1, 2*3, 4+5)")
    assert len(program.statements) == 1

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)

    call = statement.expression
    assert isinstance(call, CallExpression)
    assert_identifier(call.function, "add")

    num_args = 3
    assert len(call.arguments) == num_args
    assert_int_literal(call.arguments[0], 1)
    assert_infix_expr(call.arguments[1], 2, "*", 3)
    assert_infix_expr(call.arguments[2], 4, "+", 5)


def test_strings() -> None:
    program = parse_program('"hello world"')

    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)

    string = statement.expression
    assert isinstance(string, StringLiteral)
    assert string.value == "hello world"


def assert_identifier(expr: Expression, value: str) -> None:
    assert isinstance(expr, Identifier)
    assert expr.value == value
    assert expr.token_literal() == value


def assert_infix_expr(expr: Expression, left: int, operator: str, right: int) -> None:
    assert isinstance(expr, InfixExpression)
    assert_int_literal(expr.left, left)
    assert expr.operator == operator
    assert_int_literal(expr.right, right)


def assert_int_literal(expr: Expression, value: int) -> None:
    assert isinstance(expr, IntegerLiteral)
    assert expr.value == value
    assert expr.token_literal() == str(value)


def test_errors() -> None:
    lexer = lex("let = 5;")
    parser = Parser(lexer)

    with pytest.raises(SyntaxError):
        _ = parser.parse_program()
