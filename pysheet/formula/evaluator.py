"""Formula evaluator — walks the AST and resolves values."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from pysheet.formula.ast_nodes import (
    BinaryNode, BoolNode, CellRefNode, ColRangeRefNode, Expr,
    FuncCallNode, NameNode, NumberNode, PercentNode,
    RangeRefNode, SheetCellRefNode, SheetRangeRefNode, StringNode, UnaryNode,
)
from pysheet.formula.dependency import DependencyGraph
from pysheet.model.range import CellRange, a1_to_rowcol

if TYPE_CHECKING:
    from pysheet.model.sheet import Sheet

# Error sentinels
ERR   = "#ERR"
DIV0  = "#DIV/0"
REF   = "#REF"
NAME  = "#NAME"
CIRC  = "#CIRC"
TYPE_ERR = "#TYPE"
NA    = "#N/A"

_ERRORS = {ERR, DIV0, REF, NAME, CIRC, TYPE_ERR, NA}

# Sheet context for script functions that need to write back results
_current_sheet: "Sheet | None" = None


class EvalError(Exception):
    """Internal error raised during evaluation; converted to a sentinel string."""
    def __init__(self, sentinel: str) -> None:
        self.sentinel = sentinel


class Evaluator:
    """Evaluate a formula AST in the context of a Sheet.

    Usage::

        ev = Evaluator(sheet)
        result = ev.eval_formula("=SUM(A1:A5)")
    """

    def __init__(self, sheet: "Sheet", workbook: "Any | None" = None) -> None:
        self._sheet = sheet
        self._workbook = workbook
        self._call_stack: set[tuple[int, int]] = set()  # cycle detection
        global _current_sheet
        _current_sheet = sheet

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def eval_formula(self, formula: str, row: int = 0, col: int = 0) -> Any:
        """Parse and evaluate *formula* (must start with '=').

        Returns the computed value, or an error sentinel string on failure.
        """
        if not formula.startswith("="):
            return formula
        try:
            from pysheet.formula.parser import parse_formula
            ast = parse_formula(formula[1:])
            return self._eval(ast, row, col)
        except EvalError as e:
            return e.sentinel
        except ZeroDivisionError:
            return DIV0
        except Exception:
            return ERR

    def collect_deps(self, formula: str) -> set[tuple[int, int]]:
        """Return the set of (row, col) cells referenced by *formula*."""
        if not formula.startswith("="):
            return set()
        try:
            from pysheet.formula.parser import parse_formula
            ast = parse_formula(formula[1:])
            deps: set[tuple[int, int]] = set()
            self._collect(ast, deps)
            return deps
        except Exception:
            return set()

    # -----------------------------------------------------------------------
    # AST walker
    # -----------------------------------------------------------------------

    def _eval(self, node: Expr, row: int, col: int) -> Any:
        match node:
            case NumberNode(value=v):
                return v

            case StringNode(value=v):
                return v

            case BoolNode(value=v):
                return v

            case PercentNode(operand=op):
                return self._eval(op, row, col) / 100.0

            case CellRefNode(ref=ref):
                r, c = self._resolve_ref(ref)
                return self._cell_value(r, c)

            case RangeRefNode(ref=ref):
                return self._range_values(ref)

            case ColRangeRefNode(ref=ref):
                return self._col_range_values(ref)

            case SheetCellRefNode(sheet=sname, ref=ref):
                return self._cross_sheet_cell(sname, ref)

            case SheetRangeRefNode(sheet=sname, ref=ref):
                return self._cross_sheet_range(sname, ref)

            case NameNode(name=name):
                # Check named ranges
                nr = self._sheet.named_ranges.resolve(name)
                if nr:
                    try:
                        return self._range_values(nr)
                    except Exception:
                        pass
                raise EvalError(NAME)

            case UnaryNode(op=op, operand=operand):
                v = self._eval(operand, row, col)
                if isinstance(v, str) and v in _ERRORS:
                    return v
                if op == "-":
                    return -float(v)
                return float(v)

            case BinaryNode(op=op, left=left, right=right):
                return self._eval_binary(op, left, right, row, col)

            case FuncCallNode(name=name, args=args):
                return self._eval_func(name, args, row, col)

            case _:
                raise EvalError(ERR)

    def _eval_binary(self, op: str, left: Expr, right: Expr, row: int, col: int) -> Any:
        lv = self._eval(left, row, col)
        rv = self._eval(right, row, col)

        # Propagate errors
        if isinstance(lv, str) and lv in _ERRORS:
            return lv
        if isinstance(rv, str) and rv in _ERRORS:
            return rv

        match op:
            case "+":
                try: return float(lv) + float(rv)
                except (TypeError, ValueError): return TYPE_ERR
            case "-":
                try: return float(lv) - float(rv)
                except (TypeError, ValueError): return TYPE_ERR
            case "*":
                try: return float(lv) * float(rv)
                except (TypeError, ValueError): return TYPE_ERR
            case "/":
                try:
                    r = float(rv)
                    if r == 0: return DIV0
                    return float(lv) / r
                except (TypeError, ValueError): return TYPE_ERR
            case "^":
                try: return float(lv) ** float(rv)
                except (TypeError, ValueError): return TYPE_ERR
            case "%":
                try:
                    r = float(rv)
                    if r == 0: return DIV0
                    return float(lv) % r
                except (TypeError, ValueError): return TYPE_ERR
            case "&":
                return str(lv if lv is not None else "") + str(rv if rv is not None else "")
            case "=":
                return lv == rv
            case "<>":
                return lv != rv
            case "<":
                try: return float(lv) < float(rv)
                except (TypeError, ValueError): return str(lv) < str(rv)
            case ">":
                try: return float(lv) > float(rv)
                except (TypeError, ValueError): return str(lv) > str(rv)
            case "<=":
                try: return float(lv) <= float(rv)
                except (TypeError, ValueError): return str(lv) <= str(rv)
            case ">=":
                try: return float(lv) >= float(rv)
                except (TypeError, ValueError): return str(lv) >= str(rv)
            case _:
                return ERR

    def _eval_func(self, name: str, arg_nodes: list[Expr], row: int, col: int) -> Any:
        import pysheet.formula.functions  # ensure registry populated
        from pysheet.formula.functions.registry import get as registry_get

        fn = registry_get(name)
        if fn is None:
            raise EvalError(NAME)

        # Evaluate arguments (ranges evaluate to 2-D lists)
        args = [self._eval(a, row, col) for a in arg_nodes]

        # Special context injection for ROW/COL
        if name in ("ROW", "COL") and not args:
            if name == "ROW":
                return row + 1
            return col + 1

        # For script functions that write back: pass source range info
        if getattr(fn, "_is_script_func", False) and arg_nodes:
            from pysheet.formula.ast_nodes import RangeRefNode, CellRefNode
            source_ranges = []
            for node in arg_nodes:
                if isinstance(node, RangeRefNode):
                    source_ranges.append(node.ref)
                elif isinstance(node, CellRefNode):
                    source_ranges.append(node.ref)
            try:
                return fn(*args, _source_ranges=source_ranges, _sheet=self._sheet)
            except EvalError:
                raise
            except ZeroDivisionError:
                return DIV0
            except Exception:
                return ERR

        try:
            return fn(*args)
        except EvalError:
            raise
        except ZeroDivisionError:
            return DIV0
        except Exception:
            return ERR

    # -----------------------------------------------------------------------
    # Reference resolution
    # -----------------------------------------------------------------------

    def _resolve_ref(self, ref: str) -> tuple[int, int]:
        """Parse an A1 reference (possibly absolute $A$1) to (row, col)."""
        clean = ref.replace("$", "")
        return a1_to_rowcol(clean)

    def _cell_value(self, row: int, col: int) -> Any:
        cell = self._sheet.get_cell(row, col)
        if cell is None:
            return None
        if cell.formula:
            # Check cycle
            key = (row, col)
            if key in self._call_stack:
                return CIRC
            self._call_stack.add(key)
            try:
                return self.eval_formula(cell.formula, row, col)
            finally:
                self._call_stack.discard(key)
        return cell.value

    def _range_values(self, ref: str) -> list[list[Any]]:
        """Return a 2-D list of values for a range reference string."""
        cr = CellRange.from_a1(ref.replace("$", ""))
        result = []
        for r in range(cr.start_row, cr.end_row + 1):
            row_vals = []
            for c in range(cr.start_col, cr.end_col + 1):
                row_vals.append(self._cell_value(r, c))
            result.append(row_vals)
        return result

    def _col_range_values(self, ref: str) -> list[list[Any]]:
        """Return all values for a whole-column reference (A$, A$:B$, A:B)."""
        import re
        # Normalise: strip $ and split into one or two column letters
        clean = ref.replace("$", "").upper()
        parts = clean.split(":")
        col_a_str = parts[0].strip()
        col_b_str = parts[1].strip() if len(parts) > 1 else col_a_str
        # Convert column letters to 0-based indices
        _, c1 = a1_to_rowcol(col_a_str + "1")
        _, c2 = a1_to_rowcol(col_b_str + "1")
        max_row = max(self._sheet.max_row, 0)
        result = []
        for r in range(max_row + 1):
            row_vals = []
            for c in range(c1, c2 + 1):
                row_vals.append(self._cell_value(r, c))
            result.append(row_vals)
        return result

    # -----------------------------------------------------------------------
    # Dependency collection
    # -----------------------------------------------------------------------

    def _get_sheet(self, name: str) -> "Any | None":
        """Look up a sheet by name via the workbook, case-insensitively."""
        if self._workbook is None:
            return None
        for sheet in self._workbook.sheets:
            if sheet.name.lower() == name.lower():
                return sheet
        return None

    def _cross_sheet_cell(self, sheet_name: str, ref: str) -> "Any":
        sheet = self._get_sheet(sheet_name)
        if sheet is None:
            raise EvalError(REF)
        r, c = self._resolve_ref(ref)
        cell = sheet.get_cell(r, c)
        if cell is None:
            return None
        if cell.formula:
            ev2 = Evaluator(sheet, self._workbook)
            return ev2.eval_formula(cell.formula, r, c)
        return cell.value

    def _cross_sheet_range(self, sheet_name: str, ref: str) -> "list[list[Any]]":
        sheet = self._get_sheet(sheet_name)
        if sheet is None:
            raise EvalError(REF)
        cr = CellRange.from_a1(ref.replace("$", ""))
        result = []
        for r in range(cr.start_row, cr.end_row + 1):
            row_vals = []
            for c in range(cr.start_col, cr.end_col + 1):
                cell = sheet.get_cell(r, c)
                if cell and cell.formula:
                    ev2 = Evaluator(sheet, self._workbook)
                    row_vals.append(ev2.eval_formula(cell.formula, r, c))
                else:
                    row_vals.append(cell.value if cell else None)
            result.append(row_vals)
        return result

    def _collect(self, node: Expr, deps: set[tuple[int, int]]) -> None:
        match node:
            case CellRefNode(ref=ref):
                r, c = self._resolve_ref(ref)
                deps.add((r, c))
            case RangeRefNode(ref=ref):
                try:
                    cr = CellRange.from_a1(ref.replace("$", ""))
                    for r in range(cr.start_row, cr.end_row + 1):
                        for c in range(cr.start_col, cr.end_col + 1):
                            deps.add((r, c))
                except ValueError:
                    pass
            case UnaryNode(operand=op):
                self._collect(op, deps)
            case BinaryNode(left=lv, right=rv):
                self._collect(lv, deps)
                self._collect(rv, deps)
            case PercentNode(operand=op):
                self._collect(op, deps)
            case FuncCallNode(args=args):
                for a in args:
                    self._collect(a, deps)
            case _:
                pass


# ---------------------------------------------------------------------------
# Sheet-level recalculation
# ---------------------------------------------------------------------------

def recalculate(sheet: "Sheet", graph: DependencyGraph) -> None:
    """Recalculate all formula cells in *sheet* using *graph* for ordering.

    Updates each cell's ``value`` and ``display`` in topological order.
    Cells in a cycle receive ``#CIRC``.
    """
    from pysheet.formula.dependency import CycleError

    # Identify all formula cells
    formula_cells = {pos for pos, cell in sheet.cells.items() if cell.formula}

    # Update dependency graph
    wb = getattr(sheet, "_workbook", None)
    ev = Evaluator(sheet, wb)
    for pos in formula_cells:
        cell = sheet.cells[pos]
        deps = ev.collect_deps(cell.formula or "")
        graph.set_dependencies(pos, deps)

    # Get evaluation order
    try:
        order = graph.evaluation_order(formula_cells)
    except CycleError:
        # Mark all formula cells as circular
        for pos in formula_cells:
            cell = sheet.cells[pos]
            cell.value = CIRC
            cell.display = CIRC
        return

    # Evaluate in order
    for pos in order:
        if pos not in sheet.cells:
            continue
        cell = sheet.cells[pos]
        if cell.formula:
            ev2 = Evaluator(sheet, wb)
            val = ev2.eval_formula(cell.formula, pos[0], pos[1])
            cell.value = val
            cell.display = cell.format_value()
