
import pytest
from kvadapt.metrics import output_throughput

def test_output_throughput():
    assert output_throughput(1000, 2.0) == 500.0

def test_invalid_duration():
    with pytest.raises(ValueError):
        output_throughput(1000, 0)
