import numpy as np
from mmd import data, signals, scanner


def test_setup_scores_higher_than_noise():
    hot = signals.analyze("HOT", data.synthetic("HOT", seed=1, setup=True))
    cold = signals.analyze("COLD", data.synthetic("COLD", seed=1, setup=False))
    assert hot.score > cold.score + 15
    assert hot.bias == "UP"
    assert hot.level in ("WATCH", "HIGH")


def test_short_history_rejected():
    import pytest
    with pytest.raises(ValueError):
        signals.analyze("X", data.synthetic("X", bars=30))


def test_scan_ranks_and_logs(tmp_path):
    res, err = scanner.scan(["DEMO", "AAA2"], source="demo")
    assert not err and res[0].score >= res[1].score
    log = tmp_path / "a.csv"
    scanner.log_alerts(res, str(log), threshold=0)
    assert log.read_text().count("\n") == 3


def test_backtest_runs_on_synthetic():
    from mmd import backtest
    t = backtest.walk("DEMO", data.synthetic("DEMO", bars=200, seed=3), horizon=3, warmup=100)
    s = backtest.summarize(t)
    assert len(t) > 50 and s.n.sum() == len(t)
