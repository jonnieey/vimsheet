"""Unit tests for pysheet.formula.parser."""

import pytest

from pysheet.formula.ast_nodes import (
    BinaryNode,
    BoolNode,
    CellRefNode,
    FuncCallNode,
    NameNode,
    NumberNode,
    PercentNode,
    RangeRefNode,
    StringNode,
    UnaryNode,
)
from pysheet.formula.parser import parse_formula

# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------


class TestLiterals:
    def test_integer(self):
        assert parse_formula("42") == NumberNode(42)

    def test_float(self):
        node = parse_formula("3.14")
        assert isinstance(node, NumberNode)
        assert abs(node.value - 3.14) < 1e-9

    def test_negative_literal(self):
        node = parse_formula("-5")
        assert isinstance(node, UnaryNode)
        assert node.op == "-"
        assert node.operand == NumberNode(5)

    def test_string(self):
        assert parse_formula('"hello"') == StringNode("hello")

    def test_string_empty(self):
        assert parse_formula('""') == StringNode("")

    def test_bool_true(self):
        assert parse_formula("TRUE") == BoolNode(True)

    def test_bool_false(self):
        assert parse_formula("FALSE") == BoolNode(False)

    def test_percent(self):
        node = parse_formula("50%")
        assert isinstance(node, PercentNode)
        assert node.operand == NumberNode(50)


# ---------------------------------------------------------------------------
# Cell and range references
# ---------------------------------------------------------------------------


class TestReferences:
    def test_simple_cell_ref(self):
        assert parse_formula("A1") == CellRefNode("A1")

    def test_absolute_cell_ref(self):
        assert parse_formula("$B$2") == CellRefNode("$B$2")

    def test_mixed_ref(self):
        assert parse_formula("$C3") == CellRefNode("$C3")

    def test_lowercase_ref(self):
        node = parse_formula("a1")
        assert isinstance(node, CellRefNode)
        assert node.ref.upper() == "A1"

    def test_range_ref(self):
        assert parse_formula("A1:B5") == RangeRefNode("A1:B5")

    def test_absolute_range_ref(self):
        node = parse_formula("$A$1:$C$10")
        assert isinstance(node, RangeRefNode)

    def test_name_node(self):
        node = parse_formula("MyRange")
        assert isinstance(node, NameNode)
        assert node.name.upper() == "MYRANGE"


# ---------------------------------------------------------------------------
# Arithmetic operators
# ---------------------------------------------------------------------------


class TestArithmetic:
    def test_addition(self):
        node = parse_formula("1+2")
        assert isinstance(node, BinaryNode)
        assert node.op == "+"
        assert node.left == NumberNode(1)
        assert node.right == NumberNode(2)

    def test_subtraction(self):
        node = parse_formula("10-3")
        assert node.op == "-"

    def test_multiplication(self):
        node = parse_formula("4*5")
        assert node.op == "*"

    def test_division(self):
        node = parse_formula("8/2")
        assert node.op == "/"

    def test_power(self):
        node = parse_formula("2^10")
        assert node.op == "^"

    def test_string_concat(self):
        node = parse_formula('"a"&"b"')
        assert node.op == "&"

    def test_precedence_mul_over_add(self):
        # 2+3*4 → +(2, *(3,4))
        node = parse_formula("2+3*4")
        assert node.op == "+"
        assert isinstance(node.right, BinaryNode)
        assert node.right.op == "*"

    def test_parentheses_override_precedence(self):
        # (2+3)*4 → *(+(2,3), 4)
        node = parse_formula("(2+3)*4")
        assert node.op == "*"
        assert isinstance(node.left, BinaryNode)
        assert node.left.op == "+"


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


class TestComparisons:
    def test_eq(self):
        assert parse_formula("A1=B1").op == "="

    def test_ne(self):
        assert parse_formula("A1<>B1").op == "<>"

    def test_lt(self):
        assert parse_formula("A1<B1").op == "<"

    def test_le(self):
        assert parse_formula("A1<=B1").op == "<="

    def test_gt(self):
        assert parse_formula("A1>B1").op == ">"

    def test_ge(self):
        assert parse_formula("A1>=B1").op == ">="


# ---------------------------------------------------------------------------
# Function calls
# ---------------------------------------------------------------------------


class TestFunctions:
    def test_no_args(self):
        node = parse_formula("TODAY()")
        assert isinstance(node, FuncCallNode)
        assert node.name == "TODAY"
        assert node.args == []

    def test_one_arg(self):
        node = parse_formula("ABS(-5)")
        assert isinstance(node, FuncCallNode)
        assert node.name == "ABS"
        assert len(node.args) == 1

    def test_multiple_args(self):
        node = parse_formula("IF(A1>0,1,-1)")
        assert isinstance(node, FuncCallNode)
        assert node.name == "IF"
        assert len(node.args) == 3

    def test_range_arg(self):
        node = parse_formula("SUM(A1:A10)")
        assert isinstance(node, FuncCallNode)
        assert node.name == "SUM"
        assert isinstance(node.args[0], RangeRefNode)

    def test_nested_functions(self):
        node = parse_formula("MAX(MIN(A1,B1),0)")
        assert isinstance(node, FuncCallNode)
        assert node.name == "MAX"
        assert isinstance(node.args[0], FuncCallNode)
        assert node.args[0].name == "MIN"

    def test_at_prefix_function(self):
        # @SUM(...) is valid Excel-style
        node = parse_formula("@SUM(A1:A5)")
        assert isinstance(node, FuncCallNode)
        assert node.name == "SUM"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestParseErrors:
    def test_empty_string_raises(self):
        with pytest.raises(SyntaxError):
            parse_formula("")

    def test_unmatched_paren_raises(self):
        with pytest.raises(SyntaxError):
            parse_formula("(1+2")
