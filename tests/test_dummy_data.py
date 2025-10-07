import pandas as pd

from misophonia_dataset.dummy_data import create_dummy_data


def test_create_dummy_data():
    data = create_dummy_data(seed=42)

    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert {
        "rating",
        "subject_uuid",
        "pair_uuid",
        "is_trig",
        "is_declared_trig",
        "order",
        "is_foams",
        "is_reused",
        "did_identify",
    }.issubset(data.columns)
