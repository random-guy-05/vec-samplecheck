import numpy as np
import pytest

from vec_samplecheck.core import parse_int_list, subsample_indices, summarize


def test_parse_int_list_deduplicates_and_sorts():
    assert parse_int_list("2000,1000,2000") == [1000, 2000]


def test_subsample_is_deterministic():
    first = subsample_indices(100, 10, 7)
    second = subsample_indices(100, 10, 7)
    assert np.array_equal(first, second)
    assert len(set(first)) == 10


def test_too_many_cells_rejected():
    with pytest.raises(ValueError):
        subsample_indices(10, 11, 0)


def test_summary_ignores_none_private_and_nonfinite_metrics():
    rows = [
        {"cells": 1000, "seed": 0, "metrics": {"m": 1.0, "_private": 9}},
        {"cells": 1000, "seed": 1, "metrics": {"m": 3.0, "x": None}},
        {"cells": 2000, "seed": 0, "metrics": {"m": 2.0}},
    ]
    summary = summarize(rows)
    assert summary[0]["m_mean"] == 2.0
    assert summary[0]["m_sd"] == 1.0
    assert "_private_mean" not in summary[0]
    assert "x_mean" not in summary[0]
