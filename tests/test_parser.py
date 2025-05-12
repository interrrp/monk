import pytest

from monk.ast import (
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
)
from monk.lexer import Lexer
from monk.parser import Parser


def parse_program(code: str) -> Program:
    lexer = Lexer(code)
    parser = Parser(lexer)
    return parser.parse_program()


def test_let_stmts() -> None:
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
    assert len(program.stmts) == len(expected_vars)

    for i, (expected_name, expected_value) in enumerate(expected_vars.items()):
        stmt = program.stmts[i]

        assert isinstance(stmt, LetStmt)
        assert stmt.token_literal() == "let"
        assert_ident(stmt.name, expected_name)
        assert_int_literal(stmt.value, expected_value)


def test_return_stmts() -> None:
    code = """
        return 5;
        return 10;
        return 993322;
    """
    expected_return_vals = [5, 10, 993322]

    program = parse_program(code)
    assert len(program.stmts) == len(expected_return_vals)

    for i, expected_return_val in enumerate(expected_return_vals):
        stmt = program.stmts[i]
        assert isinstance(stmt, ReturnStmt)
        assert stmt.token_literal() == "return"
        assert_int_literal(stmt.value, expected_return_val)


def test_ident_exprs() -> None:
    name = "foobar"

    program = parse_program(f"{name};")
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert_ident(stmt.expr, name)


def test_int() -> None:
    num = 42

    program = parse_program(f"{num};")
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert_int_literal(stmt.expr, num)


def test_bool() -> None:
    program = parse_program("true; false;")

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Bool)
    assert stmt.expr.value

    stmt = program.stmts[1]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Bool)
    assert not stmt.expr.value


@pytest.mark.parametrize(
    ("code", "operator", "value"),
    [
        ("!5;", "!", 5),
        ("-15;", "-", 15),
    ],
)
def test_prefix_exprs(code: str, operator: str, value: int) -> None:
    program = parse_program(code)
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, PrefixExpr)
    assert stmt.expr.operator == operator
    assert_int_literal(stmt.expr.right, value)


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
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, InfixExpr)
    assert stmt.expr.operator == operator
    assert_int_literal(stmt.expr.left, left)
    assert_int_literal(stmt.expr.right, right)


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


def test_if_stmts() -> None:
    program = parse_program("if (4 > 2) { x } else { y };")
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, IfExpr)
    assert isinstance(stmt.expr.condition, InfixExpr)

    assert len(stmt.expr.consequence.stmts) == 1
    consequence = stmt.expr.consequence.stmts[0]
    assert isinstance(consequence, ExprStmt)
    assert_ident(consequence.expr, "x")

    assert stmt.expr.alternative is not None
    assert len(stmt.expr.alternative.stmts) == 1
    alternative = stmt.expr.alternative.stmts[0]
    assert isinstance(alternative, ExprStmt)
    assert_ident(alternative.expr, "y")


def test_fn_literals() -> None:
    program = parse_program("fn(x, y) { x + y; }")
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, FnLiteral)

    fn = stmt.expr
    num_params = 2
    assert len(fn.params) == num_params
    assert fn.params[0].value == "x"
    assert fn.params[1].value == "y"

    assert str(fn.body) == "{\n    (x + y);\n}"


def test_call_exprs() -> None:
    program = parse_program("add(1, 2*3, 4+5)")
    assert len(program.stmts) == 1

    stmt = program.stmts[0]
    assert isinstance(stmt, ExprStmt)

    call = stmt.expr
    assert isinstance(call, CallExpr)
    assert_ident(call.fn, "add")

    num_args = 3
    assert len(call.args) == num_args
    assert_int_literal(call.args[0], 1)
    assert_infix_expr(call.args[1], 2, "*", 3)
    assert_infix_expr(call.args[2], 4, "+", 5)


def assert_ident(expr: Expr, value: str) -> None:
    assert isinstance(expr, Ident)
    assert expr.value == value
    assert expr.token_literal() == value


def assert_infix_expr(expr: Expr, left: int, operator: str, right: int) -> None:
    assert isinstance(expr, InfixExpr)
    assert_int_literal(expr.left, left)
    assert expr.operator == operator
    assert_int_literal(expr.right, right)


def assert_int_literal(expr: Expr, value: int) -> None:
    assert isinstance(expr, IntLiteral)
    assert expr.value == value
    assert expr.token_literal() == str(value)


def test_errors() -> None:
    lexer = Lexer("let = 5;")
    parser = Parser(lexer)

    with pytest.raises(SyntaxError):
        parser.parse_program()
