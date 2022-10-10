import pytest
from src.extract_data import read_from_csv

@pytest.mark.parametrize("", read_from_csv())
def test_read_from_csv():
    print()