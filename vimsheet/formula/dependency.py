"""Dependency DAG for formula recalculation."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterator


class CycleError(ValueError):
    """Raised when a cycle is detected in the dependency graph."""


class DependencyGraph:
    """Directed acyclic graph tracking formula cell dependencies.

    Nodes are ``(row, col)`` tuples. An edge ``(A → B)`` means cell A's
    formula references cell B (i.e. A *depends on* B).
    """

    def __init__(self) -> None:
        # cell → set of cells it depends on (references)
        self._deps: dict[tuple[int, int], set[tuple[int, int]]] = defaultdict(set)
        # cell → set of cells that depend on it (reverse edges)
        self._rdeps: dict[tuple[int, int], set[tuple[int, int]]] = defaultdict(set)

    # -----------------------------------------------------------------------
    # Edge management
    # -----------------------------------------------------------------------

    def set_dependencies(
        self,
        cell: tuple[int, int],
        deps: set[tuple[int, int]],
    ) -> None:
        """Replace all dependencies of *cell* with *deps*."""
        # Remove old reverse edges
        for old_dep in self._deps.get(cell, set()):
            self._rdeps[old_dep].discard(cell)
        # Set new forward edges
        self._deps[cell] = set(deps)
        # Add new reverse edges
        for dep in deps:
            self._rdeps[dep].add(cell)

    def remove_cell(self, cell: tuple[int, int]) -> None:
        """Remove *cell* from the graph entirely."""
        for dep in self._deps.pop(cell, set()):
            self._rdeps[dep].discard(cell)
        for dep in self._rdeps.pop(cell, set()):
            self._deps[dep].discard(cell)

    def dependents_of(self, cell: tuple[int, int]) -> set[tuple[int, int]]:
        """Return all cells that directly depend on *cell*."""
        return set(self._rdeps.get(cell, set()))

    def dependencies_of(self, cell: tuple[int, int]) -> set[tuple[int, int]]:
        """Return all cells that *cell* directly references."""
        return set(self._deps.get(cell, set()))

    # -----------------------------------------------------------------------
    # Topological sort (Kahn's algorithm)
    # -----------------------------------------------------------------------

    def evaluation_order(self, dirty: set[tuple[int, int]]) -> list[tuple[int, int]]:
        """Return cells in evaluation order for the subgraph reachable from *dirty*.

        Raises CycleError if a cycle is detected.
        """
        # BFS to find all cells that need re-evaluation
        affected: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque(dirty)
        while queue:
            cell = queue.popleft()
            if cell in affected:
                continue
            affected.add(cell)
            for dep in self._rdeps.get(cell, set()):
                queue.append(dep)

        # Kahn topological sort on the *affected* subgraph
        in_degree: dict[tuple[int, int], int] = {}
        for cell in affected:
            in_degree[cell] = 0
        for cell in affected:
            for dep in self._deps.get(cell, set()):
                if dep in affected:
                    in_degree[cell] += 1

        ready: deque[tuple[int, int]] = deque(c for c in affected if in_degree[c] == 0)
        order: list[tuple[int, int]] = []
        while ready:
            cell = ready.popleft()
            order.append(cell)
            for rdep in self._rdeps.get(cell, set()):
                if rdep not in affected:
                    continue
                in_degree[rdep] -= 1
                if in_degree[rdep] == 0:
                    ready.append(rdep)

        if len(order) != len(affected):
            raise CycleError("Circular reference detected")

        return order

    def iter_edges(self) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
        """Yield (dependent, dependency) pairs."""
        for cell, deps in self._deps.items():
            for dep in deps:
                yield cell, dep
