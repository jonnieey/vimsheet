"""Unit tests for pysheet.formula.dependency.DependencyGraph."""

import pytest

from pysheet.formula.dependency import CycleError, DependencyGraph


A = (0, 0)
B = (0, 1)
C = (0, 2)
D = (0, 3)


class TestSetDependencies:
    def test_add_deps(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        assert g.dependencies_of(B) == {A}
        assert g.dependents_of(A) == {B}

    def test_replace_deps(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(B, {C})
        assert g.dependencies_of(B) == {C}
        assert g.dependents_of(A) == set()
        assert g.dependents_of(C) == {B}

    def test_empty_deps(self):
        g = DependencyGraph()
        g.set_dependencies(A, set())
        assert g.dependencies_of(A) == set()
        assert g.dependents_of(A) == set()

    def test_multiple_dependents(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {A})
        assert g.dependents_of(A) == {B, C}


class TestRemoveCell:
    def test_remove_formula_cell(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.remove_cell(B)
        assert g.dependencies_of(B) == set()
        assert g.dependents_of(A) == set()

    def test_remove_nonexistent(self):
        g = DependencyGraph()
        g.remove_cell(A)  # should not raise

    def test_remove_cleans_reverse_edges(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {B})
        g.remove_cell(B)
        assert g.dependencies_of(C) == set()  # C no longer has deps via B


class TestEvaluationOrder:
    def test_single_cell(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        order = g.evaluation_order({B})
        assert order == [B]

    def test_linear_chain(self):
        # A ← B ← C  (C depends on B, B depends on A)
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {B})
        order = g.evaluation_order({B, C})
        assert order.index(B) < order.index(C)

    def test_diamond(self):
        # A ← B, A ← C, B ← D, C ← D
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {A})
        g.set_dependencies(D, {B, C})
        order = g.evaluation_order({B, C, D})
        assert order.index(B) < order.index(D)
        assert order.index(C) < order.index(D)

    def test_no_deps_returns_node_itself(self):
        g = DependencyGraph()
        order = g.evaluation_order({A})
        assert A in order

    def test_empty_set(self):
        g = DependencyGraph()
        order = g.evaluation_order(set())
        assert order == []

    def test_transitive_reachability(self):
        # A ← B ← C; ask for {B}, should include C too
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {B})
        order = g.evaluation_order({B})
        assert B in order
        assert C in order
        assert order.index(B) < order.index(C)


class TestCycleDetection:
    def test_self_cycle(self):
        g = DependencyGraph()
        g.set_dependencies(A, {A})
        with pytest.raises(CycleError):
            g.evaluation_order({A})

    def test_two_cell_cycle(self):
        g = DependencyGraph()
        g.set_dependencies(A, {B})
        g.set_dependencies(B, {A})
        with pytest.raises(CycleError):
            g.evaluation_order({A, B})

    def test_indirect_cycle(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        g.set_dependencies(C, {B})
        g.set_dependencies(A, {C})
        with pytest.raises(CycleError):
            g.evaluation_order({A, B, C})


class TestDependentsOf:
    def test_no_dependents(self):
        g = DependencyGraph()
        assert g.dependents_of(A) == set()

    def test_direct_dependent(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        assert g.dependents_of(A) == {B}

    def test_returns_copy(self):
        g = DependencyGraph()
        g.set_dependencies(B, {A})
        deps = g.dependents_of(A)
        deps.add(C)
        assert g.dependents_of(A) == {B}  # original not mutated
