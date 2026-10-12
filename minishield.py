import re
import sys

KEYWORDS = {
    "SET", "TO", "PRINT",
    "IF", "THEN", "ELSE", "END",
    "FOR", "FROM", "WHILE", "DO",
    "AND", "OR", "NOT",
}

TOKEN_RULES = [
    ("NUMBER",  r"\d+(\.\d+)?"),
    ("STRING",  r'"[^"\n]*"'),
    ("NAME",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SKIP",    r"[ \t\r]+|//[^\n]*"),
    ("OP",      r"<=|>=|<>|[+\-*/%=<>()\[\],]"),
    ("NEWLINE", r"\n"),
    ("ERROR",   r"."),
]
TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_RULES))


def tokenize(source):
    """Cut pseudocode into tokens: (type, value, line)."""
    tokens = []
    line = 1
    for m in TOKEN_REGEX.finditer(source):
        kind, value = m.lastgroup, m.group()
        if kind == "NEWLINE":
            tokens.append(("NEWLINE", "", line))
            line += 1
        elif kind == "SKIP":
            continue
        elif kind == "ERROR":
            raise SyntaxError(f"line {line}: I don't understand the character {value!r}")
        else:
            if kind == "NAME" and value in KEYWORDS:
                kind = "KEYWORD"
            elif kind == "STRING":
                value = value[1:-1]
            tokens.append((kind, value, line))
    tokens.append(("EOF", "", line))
    return tokens


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        for token in tokenize(f.read()):
            if token[0] != "NEWLINE":
                print(token)