import bisect
import logging
import math
from typing import Iterable

import networkx as nx
from pysat.solvers import Solver as SATSolver

logging.basicConfig(level=logging.INFO)

# Define the node ID type. It is an integer but this helps to make the code more readable.
NodeId = int


class Distances:
    """
    This class provides a convenient interface to query distances between nodes in a graph.
    All distances are precomputed and stored in a dictionary, making lookups efficient.
    """

    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self._distances = dict(nx.all_pairs_dijkstra_path_length(self.graph))

    def all_vertices(self) -> Iterable[NodeId]:
        """Returns an iterable of all node IDs in the graph."""
        return self._distances.keys()

    def dist(self, u: NodeId, v: NodeId) -> float:
        """Returns the distance between nodes `u` and `v`."""
        return self._distances[u].get(v, math.inf)

    def max_dist(self, centers: Iterable[NodeId]) -> float:
        """Returns the maximum distance from any node to the closest center."""
        return max(min(self.dist(c, u) for c in centers) for u in self.all_vertices())

    def vertices_in_range(self, u: NodeId, limit: float) -> Iterable[NodeId]:
        """Returns an iterable of nodes within `limit` distance from node `u`."""
        return (v for v, d in self._distances[u].items() if d <= limit)

    def sorted_distances(self) -> list[float]:
        """Returns a sorted list of all pairwise distances in the graph."""
        return sorted(
            dist
            for dist_dict in self._distances.values()
            for dist in dist_dict.values()
        )


class KCenterDecisionVariant:
    def __init__(self, distances: Distances, k: int) -> None:
        self.distances = distances
        self.k = k

        self.vars = {v: i+1 for i,v in enumerate(self.distances.all_vertices())}
        self.solver = SATSolver("Gluecard4")

        # Solution model
        self._solution: list[NodeId] | None = None

    def limit_distance(self, limit: float) -> None:
        """Adds constraints to the SAT solver to ensure coverage within the given distance."""
        # logging.info("Limiting to distance: %f", limit)
        for v in self.distances.all_vertices():
            in_range = list(self.distances.vertices_in_range(v, limit))
            if len(in_range) == 0:
                self.solver.add_clause([])
                self._solution = None
                continue

            clause = [self.vars[u] for u in in_range]
            self.solver.add_clause(clause)


    def solve(self) -> list[NodeId] | None:
        """Solves the SAT problem and returns the list of selected nodes, if feasible."""
        self.solver.add_atmost(list(self.vars.values()), self.k)

        if self.solver.solve():
            model = self.solver.get_model()
            self._solution = [v for v, var in self.vars.items() if model[var - 1] > 0]

            return self._solution
        else:
            return None

    def get_solution(self) -> list[NodeId]:
        """Returns the solution if available; raises an error otherwise."""
        if self._solution is None:
            msg = "No solution available. Ensure `solve` is called first."
            raise ValueError(msg)
        return self._solution




class KCentersSolver:
    def __init__(self, graph: nx.Graph) -> None:
        """
        Creates a solver for the k-centers problem on the given networkx graph.
        The graph may not be complete, and edge weights are used to represent distances.
        """
        self.graph = graph
        self.distances = Distances(self.graph)
        self.sorted_dists = self.distances.sorted_distances()
        # TODO: Implement me!

    def solve_heur(self, k: int) -> list[NodeId]:
        """
        Calculate a heuristic solution to the k-centers problem.
        Returns the k selected centers as a list of node IDs.
        """
        nodes = list(self.graph.nodes)
        if not nodes:
            return []
        
        n = len(nodes)
        start = nodes[(n-1) // 2]
        centers = [start]
        closest_center = {node: self.distances.dist(nodes[0], node) for node in nodes}

        while len(centers) < k:
            farthest_node = max(closest_center, key=lambda n: closest_center[n])
            centers.append(farthest_node)

            for node in nodes:
                closest_center[node] = min(closest_center[node], self.distances.dist(farthest_node, node))

        return centers


    def solve(self, k: int) -> list[NodeId]:
        """
        Calculate the optimal solution to the k-centers problem for the given k.
        Returns the selected centers as a list of node IDs.
        """
        
        # Start with a heuristic solution
        centers = self.solve_heur(k)
        obj = self.distances.max_dist(centers)

        candidates = list(c for c in self.sorted_dists if c <= obj)

        low = 0
        high = len(candidates) - 1

        while low <= high:
            m = (low + high) // 2
            c = candidates[m]

            decision = KCenterDecisionVariant(self.distances, k)
            decision.limit_distance(c)
            solution = decision.solve()

            if solution is not None:
                centers = solution
                high = m - 1
            else:
                low = m + 1
        return centers
