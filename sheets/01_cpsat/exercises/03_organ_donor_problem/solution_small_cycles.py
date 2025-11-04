import math

from data_schema import Solution, Donation
from database import TransplantDatabase
from ortools.sat.python import cp_model
import networkx as nx


class CycleLimitingCrossoverTransplantSolver:
    def __init__(self, database: TransplantDatabase) -> None:
        """
        Constructs a new solver instance, using the instance data from the given database instance.
        :param Database database: The organ donor/recipients database.
        """

        self.database = database
        # TODO: Implement me!

        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = True

        self.model = cp_model.CpModel()

    def optimize(self, timelimit: float = math.inf) -> Solution:
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
        # TODO: Implement me!

        recipients = self.database.get_all_recipients()

        # directed graph so we can use predecessors/successors
        G = nx.DiGraph()
        # create node for each recipient
        G.add_nodes_from(recipients)

        for recipient in recipients:
            donors = self.database.get_partner_donors(recipient)
            for donor in donors:
                matches = self.database.get_compatible_recipients(donor)
                for match in matches:
                    G.add_edge(recipient, match, donor=donor)

        # find all simple cycles of at most length 3
        cycles = list(nx.simple_cycles(G, length_bound=3))

        # decision variable: x = 1 if cycle is used in the solution
        x = {}
        for idx, cycle in enumerate(cycles):
            x[idx] = self.model.new_bool_var(f"x_{idx}")

        # constraint: donors donate only one organ
        for donor in G.nodes:
            self.model.add_at_most_one(
                x[idx] for idx, cycle in enumerate(cycles) if donor in cycle
            )

        # objective: maximize number of transplants
        self.model.maximize(
            sum(x[idx] * len(cycles[idx]) for idx, _ in enumerate(cycles))
        )

        status = self.solver.solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            donations = []
            for idx, cycle in enumerate(cycles):
                if self.solver.value(x[idx]) == 1:
                    for i in range(len(cycle)):
                        donor = G[cycle[i]][cycle[(i + 1) % len(cycle)]]["donor"]
                        recipient = cycle[(i + 1) % len(cycle)]
                        donations.append(Donation(donor=donor, recipient=recipient))

        return Solution(donations=donations)
