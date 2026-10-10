import math

import pandas as pd


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def values_match(gold, pred) -> bool:
    g, p = _num(gold), _num(pred)
    if g is not None and p is not None:
        return math.isclose(g, p, rel_tol=0.005, abs_tol=0.05)
    return str(gold).strip().lower() == str(pred).strip().lower()


def results_match(gold: pd.DataFrame, pred: pd.DataFrame) -> bool:
    """Same number of rows, order ignored, extra columns allowed.
    Every gold value in a row must appear (within 0.5%) somewhere in a distinct predicted row."""
    if len(gold) != len(pred):
        return False
    unused = list(range(len(pred)))
    for _, grow in gold.iterrows():
        found = None
        for i in unused:
            prow = pred.iloc[i].tolist()
            if all(any(values_match(g, p) for p in prow) for g in grow.tolist()):
                found = i
                break
        if found is None:
            return False
        unused.remove(found)
    return True
