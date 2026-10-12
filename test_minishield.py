import pytest

from minishield import tokenize
from ms_interpreter import MiniShieldError, run_source


def run(code):
    """Run MiniShield code and return everything it printed, as a list of lines."""
    lines = []
    run_source(code, output=lines.append)
    return lines


# ---------- tokenizer ----------
def test_tokenizer_labels_words():
    kinds = [kind for kind, _, _ in tokenize("SET x TO 5") if kind != "EOF"]
    assert kinds == ["KEYWORD", "NAME", "KEYWORD", "NUMBER"]


def test_comments_are_ignored():
    assert run("// just a comment\nPRINT 1") == ["1"]


# ---------- maths ----------
def test_multiplication_before_addition():
    assert run("PRINT 2 + 3 * 4") == ["14"]


def test_brackets_change_order():
    assert run("PRINT (2 + 3) * 4") == ["20"]


def test_division_gives_clean_numbers():
    assert run("PRINT 10 / 2, 7 / 2") == ["5 3.5"]


# ---------- control flow ----------
def test_if_else():
    code = """
SET age TO 20
IF age >= 18 THEN
    PRINT "adult"
ELSE
    PRINT "child"
END IF
"""
    assert run(code) == ["adult"]


def test_for_loop_sum():
    code = """
SET total TO 0
FOR i FROM 1 TO 10
    SET total TO total + i
END FOR
PRINT total
"""
    assert run(code) == ["55"]


def test_while_loop():
    code = """
SET n TO 3
WHILE n > 0 DO
    PRINT n
    SET n TO n - 1
END WHILE
"""
    assert run(code) == ["3", "2", "1"]


def test_and_or_not():
    assert run("PRINT 1 < 2 AND 3 > 2, NOT 1 = 1, 1 > 2 OR 2 > 1") == ["TRUE FALSE TRUE"]


# ---------- real algorithms ----------
def test_bubble_sort():
    code = """
SET nums TO [64, 25, 12, 22, 11]
SET n TO LENGTH(nums)
FOR i FROM 0 TO n - 2
    FOR j FROM 0 TO n - i - 2
        IF nums[j] > nums[j + 1] THEN
            SET temp TO nums[j]
            SET nums[j] TO nums[j + 1]
            SET nums[j + 1] TO temp
        END IF
    END FOR
END FOR
PRINT nums
"""
    assert run(code) == ["[11, 12, 22, 25, 64]"]


def test_binary_search():
    code = """
SET nums TO [3, 8, 15, 23, 42, 56, 77]
SET target TO 42
SET low TO 0
SET high TO LENGTH(nums) - 1
SET found TO -1
WHILE low <= high AND found = -1 DO
    SET mid TO INT((low + high) / 2)
    IF nums[mid] = target THEN
        SET found TO mid
    ELSE
        IF nums[mid] < target THEN
            SET low TO mid + 1
        ELSE
            SET high TO mid - 1
        END IF
    END IF
END WHILE
PRINT found
"""
    assert run(code) == ["4"]


def test_factorial():
    code = """
SET result TO 1
FOR i FROM 1 TO 5
    SET result TO result * i
END FOR
PRINT result
"""
    assert run(code) == ["120"]


# ---------- friendly errors ----------
def test_typo_suggests_correct_name():
    with pytest.raises(MiniShieldError, match="Did you mean 'total'"):
        run("SET total TO 5\nPRINT totl")


def test_infinite_loop_is_stopped():
    with pytest.raises(MiniShieldError, match="infinite loop"):
        run("SET x TO 1\nWHILE x > 0 DO\n    SET x TO x + 1\nEND WHILE")


def test_divide_by_zero():
    with pytest.raises(MiniShieldError, match="divide by zero"):
        run("PRINT 5 / 0")


def test_list_position_out_of_range():
    with pytest.raises(MiniShieldError, match="positions 0 to 2"):
        run("SET a TO [1, 2, 3]\nPRINT a[5]")


def test_missing_keyword_gives_line_number():
    with pytest.raises(SyntaxError, match="line 1: expected 'TO'"):
        run("FOR i FROM 1 10\nEND FOR")


def test_unknown_character():
    with pytest.raises(SyntaxError, match="line 1"):
        run("PRINT 5 @ 3")