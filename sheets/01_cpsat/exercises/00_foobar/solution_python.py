from data_schema import Instance, Solution


def solve(instance: Instance) -> Solution:
    """
    Implement your solver for the problem here!
    """
    numbers = instance.numbers
    return Solution(
        number_a=max(numbers),
        number_b=min(numbers),
        distance=abs(max(numbers) - min(numbers)),
    )
