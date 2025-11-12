from functools import cache


@cache  # Enable top-down memoization (Dynamic Programming)
def fib(n: int) -> int:
    """Return the n-th Fibonacci number."""
    if n < 0:
        raise ValueError("n must be a non-negative integer.")

    if n == 0:
        return 0
    if n == 1:
        return 1

    return fib(n - 1) + fib(n - 2)
