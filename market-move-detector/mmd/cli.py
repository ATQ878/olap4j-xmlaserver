"""Command line: python -m mmd --symbols SPY QQQ AAPL [--source demo] [--watch 300]"""
import argparse, time
from . import scanner

DEFAULT = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "TSLA", "BTC-USD"]


def run_once(args):
    results, errors = scanner.scan(args.symbols, args.source)
    print(f"{'SYMBOL':<10}{'SCORE':>6}  {'LEVEL':<6}{'BIAS':<8}{'CLOSE':>12}  WHY")
    for r in results:
        print(f"{r.symbol:<10}{r.score:>6.1f}  {r.level:<6}{r.bias:<8}{r.last_close:>12.2f}  {'; '.join(r.reasons())}")
    for s, e in errors.items():
        print(f"{s:<10} ERROR {e}")
    if scanner.log_alerts(results, args.log, args.threshold):
        scanner.beep()


def main(argv=None):
    p = argparse.ArgumentParser(prog="mmd", description="Detect early signs of market moves")
    p.add_argument("--symbols", nargs="+", default=DEFAULT)
    p.add_argument("--source", choices=["yahoo", "demo", "csv"], default="yahoo")
    p.add_argument("--threshold", type=float, default=65.0, help="log + beep at/above this score")
    p.add_argument("--log", default="alerts_log.csv")
    p.add_argument("--watch", type=int, default=0, help="rescan every N seconds")
    p.add_argument("--backtest", action="store_true", help="walk-forward test of score vs. forward moves")
    p.add_argument("--horizon", type=int, default=5, help="backtest forward bars")
    p.add_argument("--gui", action="store_true", help="launch the desktop window")
    a = p.parse_args(argv)
    if a.gui:
        from .gui import launch
        return launch(a.symbols, a.source, a.threshold, a.log)
    if a.backtest:
        from . import backtest
        t = backtest.run(a.symbols, a.source, a.horizon, **({"period": "5y"} if a.source == "yahoo" else {}))
        if t.empty:
            print("No data loaded; check your connection or symbols.")
            return
        print(f"{len(t)} observations, baseline big-move rate {(t.move_x > 1.5).mean():.1%}")
        print(backtest.summarize(t).to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        return
    while True:
        run_once(a)
        if not a.watch:
            break
        time.sleep(a.watch)
