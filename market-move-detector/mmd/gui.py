"""Tkinter desktop UI (tkinter ships with the python.org Windows installer)."""
import threading, tkinter as tk
from tkinter import ttk, messagebox
from . import scanner, data

COLORS = {"HIGH": "#ffb3b3", "WATCH": "#fff2b3", "QUIET": "#ffffff"}


def launch(symbols, source="yahoo", threshold=65.0, log="alerts_log.csv"):
    root = tk.Tk()
    root.title("Market Move Detector")
    root.geometry("1100x650")
    top = ttk.Frame(root, padding=8); top.pack(fill="x")
    ttk.Label(top, text="Symbols:").pack(side="left")
    sym_var = tk.StringVar(value=" ".join(symbols)); ttk.Entry(top, textvariable=sym_var, width=48).pack(side="left", padx=4)
    src_var = tk.StringVar(value=source); ttk.Combobox(top, textvariable=src_var, values=["yahoo", "demo"], width=7, state="readonly").pack(side="left")
    ttk.Label(top, text="Alert ≥").pack(side="left", padx=(10, 2))
    thr_var = tk.DoubleVar(value=threshold); ttk.Spinbox(top, from_=10, to=100, textvariable=thr_var, width=5).pack(side="left")
    ttk.Label(top, text="Auto (min):").pack(side="left", padx=(10, 2))
    auto_var = tk.IntVar(value=0); ttk.Spinbox(top, from_=0, to=240, textvariable=auto_var, width=4).pack(side="left")
    status = tk.StringVar(value="Ready"); ttk.Label(root, textvariable=status, padding=(8, 0)).pack(fill="x")

    cols = ("symbol", "score", "level", "bias", "close", "why")
    tree = ttk.Treeview(root, columns=cols, show="headings")
    for c, w in zip(cols, (90, 70, 70, 80, 100, 650)):
        tree.heading(c, text=c.upper()); tree.column(c, width=w, anchor="w")
    for lvl, col in COLORS.items():
        tree.tag_configure(lvl, background=col)
    tree.pack(fill="both", expand=True, padx=8, pady=8)
    state = {"results": {}, "busy": False}

    def finish(results, errors):
        state["busy"] = False
        tree.delete(*tree.get_children())
        state["results"] = {r.symbol: r for r in results}
        for r in results:
            tree.insert("", "end", iid=r.symbol, tags=(r.level,),
                        values=(r.symbol, r.score, r.level, r.bias, f"{r.last_close:.2f}", "; ".join(r.reasons())))
        new = scanner.log_alerts(results, log, thr_var.get())
        status.set(f"{len(results)} scanned, {len(new)} alert(s), {len(errors)} error(s)" + (f": {errors}" if errors else ""))
        if new:
            scanner.beep()

    def do_scan():
        if state["busy"]:
            return
        state["busy"] = True; status.set("Scanning…")
        syms = sym_var.get().replace(",", " ").split()
        src = src_var.get()
        threading.Thread(target=lambda: (lambda out: root.after(0, finish, *out))(scanner.scan(syms, src)), daemon=True).start()

    def show_chart(_=None):
        sel = tree.selection()
        if not sel:
            return
        try:
            import matplotlib; matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            df = data.get(sel[0], src_var.get()).tail(120)
            fig, (a1, a2) = plt.subplots(2, 1, sharex=True, figsize=(9, 6), gridspec_kw={"height_ratios": [3, 1]})
            a1.plot(df.index, df["close"]); a1.set_title(f"{sel[0]}  score {state['results'][sel[0]].score}")
            a2.bar(df.index, df["volume"]); plt.show()
        except Exception as e:
            messagebox.showerror("Chart", str(e))

    def tick():
        if auto_var.get() > 0:
            do_scan()
        root.after(max(1, auto_var.get() or 1) * 60000, tick)

    ttk.Button(top, text="Scan now", command=do_scan).pack(side="left", padx=10)
    tree.bind("<Double-1>", show_chart)
    root.after(200, do_scan); root.after(60000, tick)
    root.mainloop()
