"""Formula lexer — converts a formula string into a list of Tokens."""

from __future__ import annotations

import re

from pysheet.formula.tokens import TT, Token

# ---------------------------------------------------------------------------
# Patterns (order matters — more specific first)
# ---------------------------------------------------------------------------

_SHEET_RANGE_PAT = re.compile(
    r"([A-Za-z_][A-Za-z0-9_ .]*)!(\$?[A-Za-z]{1,3}\$?\d+:\$?[A-Za-z]{1,3}\$?\d+)"
)
_SHEET_CELL_PAT  = re.compile(
    r"([A-Za-z_][A-Za-z0-9_ .]*)!(\$?[A-Za-z]{1,3}\$?\d+)"
)
_RANGE_PAT  = re.compile(r"\$?[A-Za-z]{1,3}\$?\d+:\$?[A-Za-z]{1,3}\$?\d+")
_CELL_PAT   = re.compile(r"\$?[A-Za-z]{1,3}\$?\d+")
_NAME_PAT   = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_NUMBER_PAT = re.compile(r"\d+\.?\d*([eE][+-]?\d+)?|\.\d+([eE][+-]?\d+)?")
_STRING_PAT = re.compile(r'"(?:[^"\\]|\\.)*"')
_OP_PAT     = re.compile(r"<>|<=|>=|[+\-*/^%&<>=|]")
_WS_PAT     = re.compile(r"\s+")


class TokenizeError(ValueError):
    pass


def tokenize(source: str) -> list[Token]:
    """Lex *source* (without the leading '=') and return a Token list.

    The list is always terminated with a TT.EOF token.
    """
    tokens: list[Token] = []
    i = 0
    n = len(source)

    while i < n:
        # Skip whitespace
        m = _WS_PAT.match(source, i)
        if m:
            i = m.end()
            continue

        ch = source[i]

        # Single-char punctuation
        if ch == "(":
            tokens.append(Token(TT.LPAREN, "(", i)); i += 1; continue
        if ch == ")":
            tokens.append(Token(TT.RPAREN, ")", i)); i += 1; continue
        if ch == ",":
            tokens.append(Token(TT.COMMA, ",", i)); i += 1; continue
        if ch == "@":
            tokens.append(Token(TT.AT, "@", i)); i += 1; continue

        # String literal
        m = _STRING_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.STRING, m.group(), i))
            i = m.end()
            continue

        # Number literal (before name/cell, digits can start both)
        m = _NUMBER_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.NUMBER, m.group(), i))
            i = m.end()
            continue

        # Cross-sheet range ref (SheetName!A1:B2) — check before plain range/cell
        m = _SHEET_RANGE_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.SHEET_RANGE_REF, m.group(), i))
            i = m.end()
            continue

        # Cross-sheet cell ref (SheetName!A1)
        m = _SHEET_CELL_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.SHEET_CELL_REF, m.group(), i))
            i = m.end()
            continue

        # Range reference (before cell ref — must check longer pattern first)
        m = _RANGE_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.RANGE_REF, m.group(), i))
            i = m.end()
            continue

        # Cell reference
        m = _CELL_PAT.match(source, i)
        if m:
            val = m.group()
            upper = val.upper()
            if upper in ("TRUE", "FALSE"):
                tokens.append(Token(TT.BOOL, upper, i))
            else:
                tokens.append(Token(TT.CELL_REF, val, i))
            i = m.end()
            continue

        # Named identifier (function name or named range)
        m = _NAME_PAT.match(source, i)
        if m:
            val = m.group()
            upper = val.upper()
            if upper in ("TRUE", "FALSE"):
                tokens.append(Token(TT.BOOL, upper, i))
            else:
                tokens.append(Token(TT.NAME, val, i))
            i = m.end()
            continue

        # Operator / comparison
        m = _OP_PAT.match(source, i)
        if m:
            tokens.append(Token(TT.OP, m.group(), i))
            i = m.end()
            continue

        raise TokenizeError(f"Unexpected character {ch!r} at position {i}")

    tokens.append(Token(TT.EOF, "", n))
    return tokens
