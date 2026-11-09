import pytest

from kvadapt.admission_bypass import choose_bypass_index


@pytest.mark.parametrize(
    ('required_blocks', 'available_blocks', 'bypass_count', 'max_bypasses', 'expected'),
    [
        ([10], 5, 0, 1, None),
        ([3, 2], 5, 0, 1, None),
        ([9, 3, 2], 5, 0, 1, 2),
        ([9, 6, 7], 5, 0, 1, None),
        ([9, 2, 4], 5, 1, 1, None),
        ([9, 2, 4], 5, 1, 2, 1),
    ],
)
def test_choose_bypass_index(
    required_blocks,
    available_blocks,
    bypass_count,
    max_bypasses,
    expected,
):
    result = choose_bypass_index(
        required_blocks,
        available_blocks,
        bypass_count=bypass_count,
        max_bypasses=max_bypasses,
    )

    assert result == expected
