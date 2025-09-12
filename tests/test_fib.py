import pytest

from misophonia_dataset.fib import fib


@pytest.mark.parametrize(
    "test_input,expected",
    [(0, 0), (1, 1), (2, 1), (3, 2), (4, 3), (5, 5), (6, 8), (7, 13)],
)
def test_will_return_correct_known_values(test_input: int, expected: int):
    assert fib(test_input) == expected


def test_will_fail_on_invalid_input():
    with pytest.raises(ValueError):
        fib(-1)
