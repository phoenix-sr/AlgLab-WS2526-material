import math

from data_schema import Instance, Solution
from ortools.sat.python import cp_model


class MultiKnapsackSolver:
    """
    This class can be used to solve the Multi-Knapsack problem
    (also the standard knapsack problem, if only one capacity is used).

    Attributes:
    - instance (Instance): The multi-knapsack instance
        - items (List[Item]): a list of Item objects representing the items to be packed.
        - capacities (List[int]): a list of integers representing the capacities of the knapsacks.
    - model (CpModel): a CpModel object representing the constraint programming model.
    - solver (CpSolver): a CpSolver object representing the constraint programming solver.
    """

    def __init__(self, instance: Instance, activate_toxic: bool = False):
        """
        Initialize the solver with the given Multi-Knapsack instance.

        Args:
        - instance (Instance): an Instance object representing the Multi-Knapsack instance.
        """
        self.items = instance.items
        self.activate_toxic = activate_toxic
        self.capacities = instance.capacities
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = True
        self.solution = []
        # TODO: Implement me!

    def solve(self, timelimit: float = math.inf) -> Solution:
        """
        Solve the Multi-Knapsack instance with the given time limit.

        Args:
        - timelimit (float): time limit in seconds for the cp-sat solver.

        Returns:
        - Solution: a list of lists of Item objects representing the items packed in each knapsack
        """
        # handle given time limit
        if timelimit <= 0.0:
            return Solution(trucks=[])  # empty solution
        if timelimit < math.inf:
            self.solver.parameters.max_time_in_seconds = timelimit
            # TODO: Implement me!
            # Mostly taken from Google's example implementation of a multi-knapsack problem

            num_items = len(self.items)
            all_items = range(num_items)

            num_bins = len(self.capacities)
            all_bins = range(num_bins)

            # create boolean vars for each item, x[i, b] = 1 if item i is packed in bin/truck b
            x = {}
            for i in all_items:
                for b in all_bins:
                    x[i, b] = self.model.new_bool_var(f"x_{i}_{b}")

            # constraint to only pack each item in at most one bin/truck
            for i in all_items:
                self.model.add_at_most_one(x[i, b] for b in all_bins)

            # constraint for truck/bin capacity
            for b in all_bins:
                self.model.add(sum(x[i, b] * self.items[i].weight for i in all_items) <= self.capacities[b])

            if self.activate_toxic:
                toxic_items = [item.toxic for item in self.items]
                # variables to track whether a truck/bin is used for toxic items
                toxic_bins = [self.model.new_bool_var(f"t_{b}") for b in all_bins]

                # if an iterm is in bin/truck b, make sure the items toxicity matches the trucks'/bin's
                for b in all_bins:
                    for i in all_items:
                        self.model.add(toxic_bins[b] == toxic_items[i]).only_enforce_if(x[i, b])

            # objective to maximize total value
            objective = []
            for i in all_items:
                for b in all_bins:
                    objective.append(x[i, b] * self.items[i].value)
            self.model.maximize(sum(objective))

            status = self.solver.solve(self.model)

            # create list of lists of items per truck for solution
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                for b in all_bins:
                    self.solution.append([])

                    for i in all_items:
                        if self.solver.value(x[i, b]) > 0:
                            self.solution[b].append(self.items[i])

                return Solution(trucks=self.solution)

        return Solution(trucks=[])  # empty solution
