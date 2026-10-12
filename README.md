# MiniShield

A small programming language that runs exam-style pseudocode.

In exams and textbooks, algorithms are written in pseudocode, but you can't actually run pseudocode to check whether it's right. I wanted a way to write an algorithm the way I'd write it on paper and see if it works, so I built a small language for it, from the tokenizer to the interpreter.

```
// add the numbers from 1 to 10
SET total TO 0
FOR i FROM 1 TO 10
    SET total TO total + i
END FOR
PRINT "The total is", total
```

```
$ python ms_interpreter.py sum.msh
The total is 55
```

## Running a program

No installs needed, just Python 3.9+:

```bash
python ms_interpreter.py bubble_sort.msh
```

```
Before: [64, 25, 12, 22, 11]
After: [11, 12, 22, 25, 64]
```

## The language

| Feature | Example |
|---|---|
| Variables | `SET x TO 5` |
| Output | `PRINT "x is", x` |
| Maths | `+ - * / %` with normal priority and brackets |
| Comparisons | `= <> < > <= >=` |
| Logic | `AND`, `OR`, `NOT` |
| Decisions | `IF ... THEN ... ELSE ... END IF` |
| Loops | `FOR i FROM 1 TO 10 ... END FOR`, `WHILE ... DO ... END WHILE` |
| Lists | `SET nums TO [3, 1, 2]`, `nums[0]` (positions start at 0) |
| Functions | `LENGTH`, `ABS`, `SQRT`, `INT` |
| Comments | `// like this` |

## Friendly errors

Beginners get stuck on error messages more than on the algorithm itself, so MiniShield tries to explain what went wrong:

```
Error: the variable 'totl' has no value yet. Did you mean 'total'?
Error: line 3: expected 'TO' but found '10'
Error: position 5 does not exist in 'nums' (it has 3 items, positions 0 to 2)
Error: the program ran too long. Is there an infinite loop?
```

## How it works

MiniShield follows the same pipeline as larger languages, just smaller:

1. **Tokenizer** (`minishield.py`): splits the source into labelled tokens (keywords, names, numbers, strings, operators) using regular expressions.
2. **Parser** (`ms_parser.py`): a hand-written recursive descent parser that checks the grammar and builds a syntax tree. Operator priority (`*` before `+`, comparisons before `AND`/`OR`) comes from the order of the parsing functions.
3. **Interpreter** (`ms_interpreter.py`): walks the tree and runs it, keeping variables in a dictionary. A step counter stops runaway loops.

## Syntax colours in VS Code

The `vscode-extension` folder adds syntax highlighting for `.msh` files. To install it, copy the folder into your VS Code extensions folder:

```powershell
Copy-Item -Recurse vscode-extension "$env:USERPROFILE\.vscode\extensions\minishield"
```

Then reload VS Code.

## Tests

```bash
pip install pytest
pytest -v
```

18 tests cover maths priority, loops, conditions, the error messages, and three classic algorithms written in MiniShield: bubble sort, binary search and factorial.

## License

MIT