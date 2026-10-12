import difflib
import sys

from ms_parser import parse

MAX_STEPS = 1_000_000  # stops infinite loops


class MiniShieldError(Exception):
    pass


def show(value):
    """Turn a value into text the way a human expects to read it."""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        return "[" + ", ".join(show(v) for v in value) + "]"
    return str(value)


BUILTINS = {
    "LENGTH": lambda x: len(x),
    "ABS": lambda x: abs(x),
    "SQRT": lambda x: x ** 0.5,
    "INT": lambda x: int(x),
}


class Interpreter:
    """Walks through the tree and actually does what each part says."""

    def __init__(self, output=print):
        self.variables = {}
        self.output = output
        self.steps = 0

    def run(self, tree):
        _, body = tree
        self.run_block(body)

    def run_block(self, statements):
        for statement in statements:
            self.run_statement(statement)

    def tick(self):
        self.steps += 1
        if self.steps > MAX_STEPS:
            raise MiniShieldError("the program ran too long. Is there an infinite loop?")

    # ---------- statements ----------
    def run_statement(self, node):
        self.tick()
        kind = node[0]

        if kind == "set":
            _, name, index, expr = node
            value = self.evaluate(expr)
            if index is None:
                self.variables[name] = value
            else:
                items = self.lookup(name)
                i = self.check_index(items, self.evaluate(index), name)
                items[i] = value

        elif kind == "print":
            _, exprs = node
            self.output(" ".join(show(self.evaluate(e)) for e in exprs))

        elif kind == "if":
            _, condition, then_body, else_body = node
            if self.evaluate(condition):
                self.run_block(then_body)
            else:
                self.run_block(else_body)

        elif kind == "for":
            _, var, start, end, body = node
            i = self.evaluate(start)
            last = self.evaluate(end)
            while i <= last:
                self.tick()
                self.variables[var] = i
                self.run_block(body)
                i += 1

        elif kind == "while":
            _, condition, body = node
            while self.evaluate(condition):
                self.tick()
                self.run_block(body)

    # ---------- expressions ----------
    def evaluate(self, node):
        kind = node[0]

        if kind in ("number", "string"):
            return node[1]

        if kind == "var":
            return self.lookup(node[1])

        if kind == "list":
            return [self.evaluate(item) for item in node[1]]

        if kind == "index":
            _, target, index = node
            items = self.evaluate(target)
            name = target[1] if target[0] == "var" else "list"
            return items[self.check_index(items, self.evaluate(index), name)]

        if kind == "neg":
            return -self.evaluate(node[1])

        if kind == "not":
            return not self.evaluate(node[1])

        if kind == "call":
            _, name, args = node
            if name not in BUILTINS:
                raise MiniShieldError(f"unknown function {name}(). Available: {', '.join(BUILTINS)}")
            return BUILTINS[name](*[self.evaluate(a) for a in args])

        if kind == "binop":
            _, op, left_node, right_node = node
            left = self.evaluate(left_node)
            if op == "AND":
                return bool(left) and bool(self.evaluate(right_node))
            if op == "OR":
                return bool(left) or bool(self.evaluate(right_node))
            right = self.evaluate(right_node)
            return self.calculate(op, left, right)

        raise MiniShieldError(f"internal error: unknown node {kind}")

    def calculate(self, op, left, right):
        try:
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return show(left) + show(right)
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise MiniShieldError("you tried to divide by zero")
                result = left / right
                return int(result) if result == int(result) else result
            if op == "%":
                return left % right
            if op == "=":
                return left == right
            if op == "<>":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
        except TypeError:
            raise MiniShieldError(f"cannot use {op!r} on {show(left)!r} and {show(right)!r}")
        raise MiniShieldError(f"unknown operator {op!r}")

    # ---------- helpers with friendly errors ----------
    def lookup(self, name):
        if name in self.variables:
            return self.variables[name]
        message = f"the variable {name!r} has no value yet"
        close = difflib.get_close_matches(name, self.variables, n=1)
        if close:
            message += f". Did you mean {close[0]!r}?"
        raise MiniShieldError(message)

    def check_index(self, items, index, name):
        if not isinstance(items, list):
            raise MiniShieldError(f"{name!r} is not a list")
        if not isinstance(index, int) or not 0 <= index < len(items):
            raise MiniShieldError(
                f"position {show(index)} does not exist in {name!r} "
                f"(it has {len(items)} items, positions 0 to {len(items) - 1})"
            )
        return index


def run_source(source, output=print):
    Interpreter(output).run(parse(source))


def main():
    if len(sys.argv) != 2:
        print("Usage: python ms_interpreter.py program.msh")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        source = f.read()
    try:
        run_source(source)
    except (SyntaxError, MiniShieldError) as err:
        print(f"Error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()