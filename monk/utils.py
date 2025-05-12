from collections.abc import Sequence


def join_commas(xs: Sequence[object]) -> str:
    return ", ".join(str(x) for x in xs)
