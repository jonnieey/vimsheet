"""Recursive-descent parser — converts a Token list into an AST."""

from __future__ import annotations

from vimsheet.formula.ast_nodes import (
    BinaryNode,
    BoolNode,
    CellRefNode,
    ColRangeRefNode,
    Expr,
    FuncCallNode,
    NameNode,
    NumberNode,
    PercentNode,
    RangeRefNode,
    SheetCellRefNode,
    SheetRangeRefNode,
    StringNode,
    UnaryNode,
)
from vimsheet.formula.tokens import TT, Token


class ParseError(SyntaxError):
    pass


class Parser:
    """Parse a list of Tokens produced by the tokenizer.

    Usage::

        from vimsheet.formula.tokenizer import tokenize
        from vimsheet.formula.parser import Parser

        tokens = tokenize("A1 + SUM(B1:B5)")
        ast = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def parse(self) -> Expr:
        """Parse and return the root expression node."""
        node = self._expr()
        self._expect(TT.EOF)
        return node

    # -----------------------------------------------------------------------
    # Grammar rules
    # -----------------------------------------------------------------------

    def _expr(self) -> Expr:
        """expr ::= term (('+' | '-' | '&' | comparison_op) term)*"""
        node = self._term()
        while self._peek_op() in ("+", "-", "&", "<", ">", "=", "<>", "<=", ">="):
            op = self._consume_op()
            right = self._term()
            node = BinaryNode(op, node, right)
        return node

    def _term(self) -> Expr:
        """term ::= factor (('*' | '/' | '%') factor)*"""
        node = self._factor()
        while self._peek_op() in ("*", "/"):
            op = self._consume_op()
            right = self._factor()
            node = BinaryNode(op, node, right)
        return node

    def _factor(self) -> Expr:
        """factor ::= unary ('^' unary)*"""
        node = self._unary()
        while self._peek_op() == "^":
            op = self._consume_op()
            right = self._unary()
            node = BinaryNode(op, node, right)
        return node

    def _unary(self) -> Expr:
        """unary ::= ('-' | '+') unary | postfix"""
        if self._peek_op() in ("-", "+"):
            op = self._consume_op()
            return UnaryNode(op, self._unary())
        return self._postfix()

    def _postfix(self) -> Expr:
        """postfix ::= atom ('%')?"""
        node = self._atom()
        if self._peek_type() == TT.OP and self._peek_val() == "%":
            self._advance()
            node = PercentNode(node)
        return node

    def _atom(self) -> Expr:
        """atom ::= number | string | bool | range_ref | cell_ref | func_call | '(' expr ')'"""
        tok = self._current()

        if tok.type == TT.NUMBER:
            self._advance()
            return NumberNode(float(tok.value))

        if tok.type == TT.STRING:
            self._advance()
            # Strip outer quotes and unescape
            return StringNode(tok.value[1:-1].replace('\\"', '"').replace("\\\\", "\\"))

        if tok.type == TT.BOOL:
            self._advance()
            return BoolNode(tok.value == "TRUE")

        if tok.type == TT.SHEET_RANGE_REF:
            self._advance()
            sheet, ref = tok.value.split("!", 1)
            return SheetRangeRefNode(sheet, ref)

        if tok.type == TT.SHEET_CELL_REF:
            self._advance()
            sheet, ref = tok.value.split("!", 1)
            return SheetCellRefNode(sheet, ref)

        if tok.type == TT.COL_RANGE_REF:
            self._advance()
            return ColRangeRefNode(tok.value)

        if tok.type == TT.RANGE_REF:
            self._advance()
            return RangeRefNode(tok.value)

        if tok.type == TT.CELL_REF:
            self._advance()
            return CellRefNode(tok.value)

        if tok.type == TT.AT:
            # @FUNCNAME(args)
            self._advance()
            name_tok = self._current()
            if name_tok.type not in (TT.NAME, TT.CELL_REF):
                raise ParseError(f"Expected function name after '@' at pos {name_tok.pos}")
            self._advance()
            return self._func_call(name_tok.value.upper())

        if tok.type == TT.NAME:
            # Could be function call or named range
            name = tok.value.upper()
            self._advance()
            if self._peek_type() == TT.LPAREN:
                return self._func_call(name)
            return NameNode(name)

        if tok.type == TT.LPAREN:
            self._advance()
            node = self._expr()
            self._expect(TT.RPAREN)
            return node

        raise ParseError(f"Unexpected token {tok!r}")

    def _func_call(self, name: str) -> FuncCallNode:
        """Parse the argument list for a function call (LPAREN already consumed by caller)."""
        self._expect(TT.LPAREN)
        args: list[Expr] = []
        if self._peek_type() != TT.RPAREN:
            args.append(self._expr())
            while self._peek_type() == TT.COMMA:
                self._advance()  # consume comma
                args.append(self._expr())
        self._expect(TT.RPAREN)
        return FuncCallNode(name, args)

    # -----------------------------------------------------------------------
    # Token stream helpers
    # -----------------------------------------------------------------------

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek_type(self) -> TT:
        return self._tokens[self._pos].type

    def _peek_val(self) -> str:
        return self._tokens[self._pos].value

    def _peek_op(self) -> str:
        tok = self._tokens[self._pos]
        return tok.value if tok.type == TT.OP else ""

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, tt: TT) -> Token:
        tok = self._current()
        if tok.type != tt:
            raise ParseError(
                f"Expected {tt.name} but got {tok.type.name} ({tok.value!r}) at pos {tok.pos}"
            )
        return self._advance()

    def _consume_op(self) -> str:
        tok = self._advance()
        return tok.value


def parse_formula(source: str) -> Expr:
    """Convenience: tokenize and parse *source* (without leading '=').

    Raises ParseError on syntax errors.
    """
    from vimsheet.formula.tokenizer import tokenize

    tokens = tokenize(source)
    return Parser(tokens).parse()
