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
    Node,
    PrefixExpression,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
)
from monk.object import (
    Boolean,
    Builtin,
    Environment,
    Function,
    Integer,
    Null,
    Object,
    ReturnValue,
    String,
)

NULL = Null()
TRUE = Boolean(value=True)
FALSE = Boolean(value=False)


def builtin_len(*args: Object) -> Object:
    if len(args) != 1:
        msg = f"len takes 1 argument, got {len(args)}"
        raise TypeError(msg)

    if not isinstance(args[0], String):
        msg = f"len takes a string, got {args[0].type}"
        raise TypeError(msg)

    return Integer(len(args[0].value))


def builtin_puts(*args: Object) -> Object:
    for arg in args:
        print(arg)
    return NULL


def builtin_input(*args: Object) -> Object:
    prompt = ""
    if len(args) == 1:
        if not isinstance(args[0], String):
            msg = f"Input prompt should be a string, got {args[0].type}"
            raise TypeError(msg)
        prompt = args[0].value

    return String(input(prompt))


builtins: dict[str, Builtin] = {
    "len": Builtin(builtin_len),
    "puts": Builtin(builtin_puts),
    "input": Builtin(builtin_input),
}


def evaluate(node: Node, env: Environment) -> Object:  # noqa: PLR0911, PLR0912, C901
    match node:
        case Program():
            return evaluate_program(env, node.statements)

        case BlockStatement():
            return evaluate_block_statement(env, node.statements)

        case ExpressionStatement():
            return evaluate(node.expression, env)

        case IntegerLiteral():
            return Integer(node.value)

        case StringLiteral():
            return String(node.value)

        case Identifier():
            if v := env.get(node.value):
                return v

            if builtin := builtins.get(node.value):
                return builtin

            msg = f"Unknown identifier {node.value}"
            raise NameError(msg)

        case BooleanLiteral():
            return TRUE if node.value else FALSE

        case PrefixExpression():
            right = evaluate(node.right, env)
            return evaluate_prefix_expression(node.operator, right)

        case InfixExpression():
            left = evaluate(node.left, env)
            right = evaluate(node.right, env)
            return evaluate_infix_expression(node.operator, left, right)

        case IfExpression():
            if is_truthy(evaluate(node.condition, env)):
                return evaluate(node.consequence, env)
            if node.alternative is not None:
                return evaluate(node.alternative, env)
            return NULL

        case FunctionLiteral():
            return Function(node.parameters, node.body, env)

        case CallExpression():
            function = evaluate(node.function, env)
            args = evaluate_expressions(node.arguments, env)

            match function:
                case Builtin():
                    return function.fn(*args)

                case Function():
                    scope_env = Environment(outer=function.environment)
                    for i, param in enumerate(function.parameters):
                        scope_env[param.value] = args[i]

                    result = evaluate(function.body, scope_env)
                    if isinstance(result, ReturnValue):
                        return result.value
                    return result

                case _:
                    msg = f"Cannot call {function.type}"
                    raise TypeError(msg)

        case LetStatement():
            val = evaluate(node.value, env)
            env[node.name.value] = val
            return NULL

        case ReturnStatement():
            return ReturnValue(evaluate(node.value, env))

        case _:
            msg = f"Cannot evaluate {type(node)}"
            raise TypeError(msg)


def is_truthy(obj: Object) -> bool:
    return obj not in (NULL, FALSE)


def evaluate_expressions(expressions: list[Expression], env: Environment) -> list[Object]:
    return [evaluate(expression, env) for expression in expressions]


def evaluate_prefix_expression(operator: str, right: Object) -> Object:
    match operator:
        case "!":
            return evaluate_bang_expression(right)
        case "-" if isinstance(right, Integer):
            return evaluate_integer_minus_expression(right)
        case _:
            msg = f"Unknown operator: {operator}{right.type}"
            raise SyntaxError(msg)


def evaluate_bang_expression(right: Object) -> Object:
    if right in (FALSE, NULL):
        return TRUE
    return FALSE


def evaluate_integer_minus_expression(right: Integer) -> Object:
    return Integer(-right.value)


def evaluate_infix_expression(operator: str, left: Object, right: Object) -> Object:
    if left.type != right.type:
        msg = f"Type mismatch: {left.type} {operator} {right.type}"
        raise TypeError(msg)

    lhs = getattr(left, "value", None)
    rhs = getattr(right, "value", None)

    if not isinstance(lhs, int | bool | str) or not isinstance(rhs, int | bool | str):
        msg = "Infix expression values must be integers, booleans, or strings"
        raise TypeError(msg)

    if operator == "==":
        return Boolean(lhs == rhs)
    if operator == "!=":
        return Boolean(lhs != rhs)

    if operator == "+" and isinstance(lhs, str) and isinstance(rhs, str):
        return String(lhs + rhs)

    if isinstance(left, Integer) and isinstance(right, Integer):
        return evaluate_integer_infix_expression(operator, left, right)

    msg = f"Unknown operator: {left.type} {operator} {right.type}"
    raise SyntaxError(msg)


def evaluate_integer_infix_expression(operator: str, left: Integer, right: Integer) -> Object:
    lhs = left.value
    rhs = right.value
    obj = NULL

    match operator:
        case "+":
            obj = Integer(lhs + rhs)
        case "-":
            obj = Integer(lhs - rhs)
        case "*":
            obj = Integer(lhs * rhs)
        case "/":
            obj = Integer(lhs // rhs)
        case ">":
            obj = Boolean(lhs > rhs)
        case "<":
            obj = Boolean(lhs < rhs)
        case _:
            obj = NULL

    return obj


def evaluate_program(env: Environment, statements: list[Statement]) -> Object:
    result = Null()

    for statement in statements:
        result = evaluate(statement, env)

        if isinstance(result, ReturnValue):
            return result.value

    return result


def evaluate_block_statement(env: Environment, statements: list[Statement]) -> Object:
    result = Null()

    for statement in statements:
        result = evaluate(statement, env)

        if isinstance(result, ReturnValue):
            return result

    return result
