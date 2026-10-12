import sys
from pprint import pprint

from minishield import tokenize


class Parser:
    """Turns the list of tokens into a tree that shows what the program means."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- small helpers ----------
    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def check(self, kind, value=None):
        tok_kind, tok_value, _ = self.peek()
        return tok_kind == kind and (value is None or tok_value == value)

    def expect(self, kind, value=None):
        if self.check(kind, value):
            return self.advance()
        _, found, line = self.peek()
        wanted = value or kind.lower()
        raise SyntaxError(f"line {line}: expected {wanted!r} but found {found or 'end of line'!r}")

    def skip_newlines(self):
        while self.check("NEWLINE"):
            self.advance()

    # ---------- statements ----------
    def parse_program(self):
        body = self.parse_block(stop_words=())
        self.expect("EOF")
        return ("program", body)

    def parse_block(self, stop_words):
        """Read statements until END / ELSE (or the end of the file)."""
        statements = []
        self.skip_newlines()
        while not self.check("EOF") and not any(self.check("KEYWORD", w) for w in stop_words):
            statements.append(self.parse_statement())
            self.skip_newlines()
        return statements

    def parse_statement(self):
        kind, value, line = self.peek()
        if kind == "KEYWORD" and value == "SET":
            return self.parse_set()
        if kind == "KEYWORD" and value == "PRINT":
            return self.parse_print()
        if kind == "KEYWORD" and value == "IF":
            return self.parse_if()
        if kind == "KEYWORD" and value == "FOR":
            return self.parse_for()
        if kind == "KEYWORD" and value == "WHILE":
            return self.parse_while()
        raise SyntaxError(f"line {line}: a line must start with SET, PRINT, IF, FOR or WHILE, not {value!r}")

    def parse_set(self):
        self.expect("KEYWORD", "SET")
        name = self.expect("NAME")[1]
        index = None
        if self.check("OP", "["):
            self.advance()
            index = self.parse_expression()
            self.expect("OP", "]")
        self.expect("KEYWORD", "TO")
        return ("set", name, index, self.parse_expression())

    def parse_print(self):
        self.expect("KEYWORD", "PRINT")
        values = [self.parse_expression()]
        while self.check("OP", ","):
            self.advance()
            values.append(self.parse_expression())
        return ("print", values)

    def parse_if(self):
        self.expect("KEYWORD", "IF")
        condition = self.parse_expression()
        self.expect("KEYWORD", "THEN")
        then_body = self.parse_block(stop_words=("ELSE", "END"))
        else_body = []
        if self.check("KEYWORD", "ELSE"):
            self.advance()
            else_body = self.parse_block(stop_words=("END",))
        self.expect("KEYWORD", "END")
        self.expect("KEYWORD", "IF")
        return ("if", condition, then_body, else_body)

    def parse_for(self):
        self.expect("KEYWORD", "FOR")
        var = self.expect("NAME")[1]
        self.expect("KEYWORD", "FROM")
        start = self.parse_expression()
        self.expect("KEYWORD", "TO")
        end = self.parse_expression()
        body = self.parse_block(stop_words=("END",))
        self.expect("KEYWORD", "END")
        self.expect("KEYWORD", "FOR")
        return ("for", var, start, end, body)

    def parse_while(self):
        self.expect("KEYWORD", "WHILE")
        condition = self.parse_expression()
        self.expect("KEYWORD", "DO")
        body = self.parse_block(stop_words=("END",))
        self.expect("KEYWORD", "END")
        self.expect("KEYWORD", "WHILE")
        return ("while", condition, body)

    # ---------- expressions (lowest priority first) ----------
    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check("KEYWORD", "OR"):
            self.advance()
            left = ("binop", "OR", left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.check("KEYWORD", "AND"):
            self.advance()
            left = ("binop", "AND", left, self.parse_not())
        return left

    def parse_not(self):
        if self.check("KEYWORD", "NOT"):
            self.advance()
            return ("not", self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_sum()
        for op in ("=", "<>", "<", ">", "<=", ">="):
            if self.check("OP", op):
                self.advance()
                return ("binop", op, left, self.parse_sum())
        return left

    def parse_sum(self):
        left = self.parse_term()
        while self.check("OP", "+") or self.check("OP", "-"):
            op = self.advance()[1]
            left = ("binop", op, left, self.parse_term())
        return left

    def parse_term(self):
        left = self.parse_unary()
        while self.check("OP", "*") or self.check("OP", "/") or self.check("OP", "%"):
            op = self.advance()[1]
            left = ("binop", op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.check("OP", "-"):
            self.advance()
            return ("neg", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while self.check("OP", "["):
            self.advance()
            index = self.parse_expression()
            self.expect("OP", "]")
            node = ("index", node, index)
        return node

    def parse_primary(self):
        kind, value, line = self.peek()
        if kind == "NUMBER":
            self.advance()
            return ("number", float(value) if "." in value else int(value))
        if kind == "STRING":
            self.advance()
            return ("string", value)
        if kind == "NAME":
            self.advance()
            if self.check("OP", "("):
                self.advance()
                args = []
                if not self.check("OP", ")"):
                    args.append(self.parse_expression())
                    while self.check("OP", ","):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect("OP", ")")
                return ("call", value, args)
            return ("var", value)
        if kind == "OP" and value == "(":
            self.advance()
            node = self.parse_expression()
            self.expect("OP", ")")
            return node
        if kind == "OP" and value == "[":
            self.advance()
            items = []
            if not self.check("OP", "]"):
                items.append(self.parse_expression())
                while self.check("OP", ","):
                    self.advance()
                    items.append(self.parse_expression())
            self.expect("OP", "]")
            return ("list", items)
        raise SyntaxError(f"line {line}: expected a value but found {value or 'end of line'!r}")


def parse(source):
    return Parser(tokenize(source)).parse_program()


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        pprint(parse(f.read()), width=70)