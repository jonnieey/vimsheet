"""Formula engine performance benchmarks.

Measures formula tokenization, parsing, evaluation, dependency graph updates,
range aggregation, VLOOKUP, chained formula recalculation, and topology sorting.
"""

from __future__ import annotations

import contextlib
import gc

import pytest

from vimsheet.formula.dependency import CycleError, DependencyGraph
from vimsheet.formula.evaluator import Evaluator
from vimsheet.formula.parser import Parser
from vimsheet.formula.tokenizer import tokenize
from vimsheet.model.sheet import Sheet

from .conftest import (
    measure,
    populate_chain,
    populate_numbers,
    result_json,
)


@pytest.mark.benchmark
class TestTokenizePerformance:
    """Formula tokenization benchmarks."""

    def test_tokenize_simple(self) -> None:
        """Time tokenize('=SUM(A1:A10)')."""

        def tok() -> None:
            list(tokenize("=SUM(A1:A10)"))

        stats = measure(tok, iterations=2000, label="tokenize_simple")
        result = result_json(
            "formula.tokenize_simple",
            "formula",
            stats,
            dataset="=SUM(A1:A10)",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 0.05, f"Tokenize {stats['mean_ms']:.4f}ms exceeds 0.05ms target"

    def test_tokenize_complex(self) -> None:
        """Time tokenize of a complex nested formula."""

        def tok() -> None:
            list(tokenize("=@IF(A1>0, @SUM(B1:B100), @VLOOKUP(C1, B1:B100, 2, FALSE))"))

        stats = measure(tok, iterations=2000, label="tokenize_complex")
        result = result_json(
            "formula.tokenize_complex",
            "formula",
            stats,
            dataset="complex IF/SUM/VLOOKUP",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.1
        ), f"Complex tokenize {stats['mean_ms']:.4f}ms exceeds 0.1ms target"


@pytest.mark.benchmark
class TestParsePerformance:
    """Formula parsing benchmarks."""

    def test_parse_simple(self) -> None:
        """Time parsing '@SUM(A1:A10)' (without leading '=')."""
        tokens = list(tokenize("@SUM(A1:A10)"))

        def parse() -> None:
            Parser(tokens).parse()

        stats = measure(parse, iterations=2000, label="parse_simple")
        result = result_json(
            "formula.parse_simple",
            "formula",
            stats,
            dataset="=SUM(A1:A10)",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 0.05, f"Parse {stats['mean_ms']:.4f}ms exceeds 0.05ms target"

    def test_parse_complex(self) -> None:
        """Time parsing a complex nested formula (without leading '=')."""
        tokens = list(tokenize("@IF(A1>0, @SUM(B1:B100), @VLOOKUP(C1, B1:B100, 2, FALSE))"))

        def parse() -> None:
            Parser(tokens).parse()

        stats = measure(parse, iterations=2000, label="parse_complex")
        result = result_json(
            "formula.parse_complex",
            "formula",
            stats,
            dataset="complex IF/SUM/VLOOKUP",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.1
        ), f"Complex parse {stats['mean_ms']:.4f}ms exceeds 0.1ms target"


@pytest.mark.benchmark
class TestEvalPerformance:
    """Formula evaluation benchmarks."""

    def test_eval_single_number(self) -> None:
        """Time evaluating a literal number."""
        sheet = Sheet(name="E")
        sheet.set_cell_value(0, 0, 42)
        evaluator = Evaluator(sheet)

        def eval_literal() -> None:
            evaluator.eval_formula("42")

        stats = measure(eval_literal, iterations=2000, label="eval_literal")
        result = result_json(
            "formula.eval_literal",
            "formula",
            stats,
            dataset="literal 42",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.05
        ), f"Literal eval {stats['mean_ms']:.4f}ms exceeds 0.05ms target"

    def test_eval_sum_range_10k(self) -> None:
        """Time =@SUM(A1:A10000)."""
        sheet = Sheet(name="E")
        populate_numbers(sheet, 10000, 1)
        evaluator = Evaluator(sheet)

        def eval_sum() -> None:
            evaluator.eval_formula("=@SUM(A1:A10000)")

        gc.collect()
        stats = measure(eval_sum, iterations=200, label="eval_sum_10k")
        result = result_json(
            "formula.eval_sum_range_10k",
            "formula",
            stats,
            dataset="10K numbers in A column",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 30.0, f"SUM 10K eval {stats['mean_ms']:.1f}ms exceeds 30ms target"

    def test_eval_sum_range_100k(self) -> None:
        """Time =@SUM(A1:A100000)."""
        sheet = Sheet(name="E")
        populate_numbers(sheet, 100000, 1)
        evaluator = Evaluator(sheet)

        def eval_sum() -> None:
            evaluator.eval_formula("=@SUM(A1:A100000)")

        gc.collect()
        stats = measure(eval_sum, iterations=50, label="eval_sum_100k")
        result = result_json(
            "formula.eval_sum_range_100k",
            "formula",
            stats,
            dataset="100K numbers in A column",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 300.0
        ), f"SUM 100K eval {stats['mean_ms']:.1f}ms exceeds 300ms target"

    def test_eval_vlookup_10k(self) -> None:
        """Time =@VLOOKUP(A1, A:B, 2, FALSE) on 10K rows."""
        sheet = Sheet(name="E")
        populate_numbers(sheet, 10000, 1)
        for i in range(10000):
            sheet.set_cell_value(i, 1, i * 10)
        evaluator = Evaluator(sheet)
        sheet.set_cell_value(0, 0, 5000)

        def eval_vlookup() -> None:
            evaluator.eval_formula("=@VLOOKUP(A1, A:B, 2, FALSE)")

        gc.collect()
        stats = measure(eval_vlookup, iterations=200, label="eval_vlookup")
        result = result_json(
            "formula.eval_vlookup_10k",
            "formula",
            stats,
            dataset="VLOOKUP on 10K-row table",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 25.0, f"VLOOKUP {stats['mean_ms']:.1f}ms exceeds 25ms target"

    def test_eval_chained_formula(self) -> None:
        """Time evaluating a formula deep in a chain: A10000 = A9999+1."""
        sheet = Sheet(name="Chain")
        populate_chain(sheet, 10000)
        evaluator = Evaluator(sheet)

        def eval_chain() -> None:
            evaluator.eval_formula("=A9999+1")

        gc.collect()
        stats = measure(eval_chain, iterations=200, label="eval_chain")
        result = result_json(
            "formula.eval_chained_10k",
            "formula",
            stats,
            dataset="A10000 = A9999+1 in 10K chain",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 15.0, f"Chain eval {stats['mean_ms']:.1f}ms exceeds 15ms target"


@pytest.mark.benchmark
class TestRecalcPerformance:
    """Recalculation cascade benchmarks."""

    def test_incremental_recalc_chain_10k(self, sheet_chain_10k: Sheet) -> None:
        """Change A1 in a 10K chain, measure recalc time."""

        def recalc() -> None:
            sheet_chain_10k.set_cell_value(0, 0, 42)

        # Warm up first call (builds dep graph)
        recalc()

        gc.collect()
        stats = measure(recalc, iterations=20, label="recalc_chain_10k")
        result = result_json(
            "formula.recalc_chain_10k",
            "formula",
            stats,
            dataset="10K cell chain, change root",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 100
        ), f"10K chain recalc {stats['mean_ms']:.1f}ms exceeds 100ms target"

    @pytest.mark.slow
    def test_incremental_recalc_chain_100k(self, sheet_chain_100k: Sheet) -> None:
        """Change A1 in a 100K chain, measure recalc time."""

        def recalc() -> None:
            sheet_chain_100k.set_cell_value(0, 0, 42)

        recalc()  # warm
        gc.collect()
        stats = measure(recalc, iterations=5, label="recalc_chain_100k")
        result = result_json(
            "formula.recalc_chain_100k",
            "formula",
            stats,
            dataset="100K cell chain, change root",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 5000
        ), f"100K chain recalc {stats['mean_ms']:.1f}ms exceeds 5s target"

    def test_volatile_function_eval(self) -> None:
        """Time =@TODAY() evaluation."""
        sheet = Sheet(name="V")
        evaluator = Evaluator(sheet)
        tokens = list(tokenize("=@TODAY()"))
        ast = Parser().parse(tokens)

        def eval_today() -> None:
            evaluator.eval(ast)

        stats = measure(eval_today, iterations=500, label="eval_today")
        result = result_json(
            "formula.eval_today",
            "formula",
            stats,
            dataset="=@TODAY()",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 0.5, f"TODAY() eval {stats['mean_ms']:.4f}ms exceeds 0.5ms target"


@pytest.mark.benchmark
class TestDependencyGraphPerformance:
    """Dependency graph benchmarks."""

    def test_dep_graph_set_10k(self) -> None:
        """Time setting 10 000 dependency edges."""
        dg = DependencyGraph()

        def set_deps() -> None:
            for i in range(1, 10001):
                dg.set_dependencies((i, 0), {(i - 1, 0)})

        gc.collect()
        stats = measure(set_deps, iterations=10, label="dep_graph_set_10k")
        result = result_json(
            "formula.dep_graph_set_10k",
            "deps",
            stats,
            dataset="10K edges, sequential",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 100
        ), f"Dep graph 10K set {stats['mean_ms']:.1f}ms exceeds 100ms target"

    def test_evaluation_order_10k(self) -> None:
        """Time Kahn's algorithm on a 10K-node graph."""
        dg = DependencyGraph()
        for i in range(1, 10001):
            dg.set_dependencies((i, 0), {(i - 1, 0)})
        dg.set_dependencies((0, 0), set())

        def order() -> None:
            dg.evaluation_order({(0, 0)})

        stats = measure(order, iterations=200, label="eval_order_10k")
        result = result_json(
            "formula.eval_order_10k",
            "deps",
            stats,
            dataset="10K-node linear graph",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Eval order {stats['mean_ms']:.3f}ms exceeds 5ms target"

    def test_circular_detection(self) -> None:
        """Time to detect a cycle in a small graph."""
        dg = DependencyGraph()
        dg.set_dependencies((0, 0), {(1, 0)})
        dg.set_dependencies((1, 0), {(0, 0)})

        def detect() -> None:
            with contextlib.suppress(CycleError):
                dg.evaluation_order({(0, 0)})

        stats = measure(detect, iterations=500, label="cycle_detect")
        result = result_json(
            "formula.circular_detection",
            "deps",
            stats,
            dataset="2-node cycle",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.5
        ), f"Cycle detection {stats['mean_ms']:.4f}ms exceeds 0.5ms target"
