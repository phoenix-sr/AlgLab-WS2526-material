from data_schema import Instance, Solution
from ortools.sat.python import cp_model


def solve(instance: Instance) -> Solution:
    """
    Implement your solver for the problem here!
    """
    numbers = instance.numbers
    model = cp_model.CpModel()
    domain = cp_model.Domain.from_values(numbers)
    x = model.new_int_var_from_domain(domain, "x")
    y = model.new_int_var_from_domain(domain, "y")
    distance = x - y
    model.maximize(distance)
    solver = cp_model.CpSolver()
    solver.solve(model)

    return Solution(
        number_a=solver.value(x),
        number_b=solver.value(y),
        distance=solver.value(distance),
    )
