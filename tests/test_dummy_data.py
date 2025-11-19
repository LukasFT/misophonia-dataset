import pandas as pd

from experiment.py_analysis.dummy_data import create_dummy_data


def test_create_dummy_data():
    data = create_dummy_data(seed=42, n_subjects=100)

    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert {
        "rating",
        "subject_uuid",
        "pair_uuid",
        "is_trig",
        "is_declared_trig",
        "is_declared_trig_pair",
        "order",
        "is_foams",
        "is_reused",
        "did_identify",
        "pair_category",
        "category",
        "version",
    }.issubset(data.columns)
    assert data.query("is_foams == 1 and is_trig == 0").empty
    assert data.query("is_trig == 0 and category != 'ctrl'").empty
    assert data.groupby("pair_uuid")["pair_category"].nunique().max() == 1
    assert data.query("is_trig == 1")["is_declared_trig"].equals(data.query("is_trig == 1")["is_declared_trig_pair"])
    assert data.query("is_trig == 0")["is_declared_trig"].sum() == 0
    assert data.query("is_declared_trig_pair == 1 and is_trig == 0").shape[0] > 0
