import math

from data_schema import Solution, Donation
from database import TransplantDatabase
from ortools.sat.python import cp_model
import networkx as nx


class CrossoverTransplantSolver:
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
        """
        Solves the constraint programming model and returns the optimal solution (if found within time limit).
        :param timelimit: The maximum time limit for the solver.
        :return: A list of Donation objects representing the best solution, or None if no solution was found.
        """
        if timelimit <= 0.0:
            return Solution(donations=[])
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit

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

        # decision variable: x = 1 if donor i donates to recipient j
        x = {}
        for donor, recipient in G.edges:
            x[donor, recipient] = self.model.new_bool_var(f"x_{donor}_{recipient}")

        # constraint: donors donate only one organ
        for donor in G.nodes:
            self.model.add_at_most_one(
                x[donor, recipient] for recipient in G.successors(donor)
            )

        # constraint: recipients receive only one organ
        for recipient in G.nodes:
            self.model.add_at_most_one(
                x[donor, recipient] for donor in G.predecessors(recipient)
            )

        # constraint: donor only donates if their partner recieves an organ
        for donor in G.nodes:
            # get outgoing and incoming edges for the donor
            outgoing = [x[donor, recipient] for recipient in G.successors(donor)]
            incoming = [x[k, donor] for k in G.predecessors(donor)]

            # booleans to track if the donor donates or receives an organ
            y_out = self.model.new_bool_var(f"out_{donor}")
            y_in = self.model.new_bool_var(f"in_{donor}")

            self.model.add(sum(outgoing) == y_out)
            self.model.add(sum(incoming) == y_in)
            self.model.add(y_out <= y_in)

        # objective: maximize number of transplants
        self.model.maximize(sum(x.values()))

        status = self.solver.solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            donations = []
            for donor, recipient in x:
                if self.solver.value(x[donor, recipient]) == 1:
                    donor = G[donor][recipient]["donor"]
                    recipient = recipient
                    donations.append(Donation(donor=donor, recipient=recipient))

        return Solution(donations=donations)
