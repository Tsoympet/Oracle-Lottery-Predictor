
from PySide6 import QtWidgets
from ..util.config import get_sentry_dsn
from ..util.sentry_init import try_init_sentry
from ..core.orchestrator import predict_final_portfolio, PredictOptions, learn_from_outcome
from ..reports.dashboard import compute_series
from ..data.games_registry import get_game
from ..reports.outcomes import record_outcome, best_match_against_draw, evaluation_report, evaluation_report_ev, _next_draw_id_from_history, validate_numbers_for_game
from ..reports.evaluator import evaluate_tickets_vs_draw
from ..reports.heatmaps import export_cooccurrence_all, export_correlation_all
from ..reports.analytics import export_luck_curve_all
from ..reports.exporters import export_json, export_hits_csv
from ..reports.importers import import_history_csv, import_outcomes_csv, import_history_html
from ..data.store import predictions_path
import csv, statistics as st, os, math
from pathlib import Path
from ..reports.analytics import ev_mc_summary, luck_curve_from_hits
from ..reports.heatmaps import export_cooccurrence_heatmap, export_correlation_heatmap
from ..reports.dashboard import compute_series
from ..data.games_registry import get_game
from ..reports.outcomes import record_outcome, best_match_against_draw, evaluation_report, evaluation_report_ev, _next_draw_id_from_history, validate_numbers_for_game
from ..reports.evaluator import evaluate_tickets_vs_draw
from ..reports.heatmaps import export_cooccurrence_all, export_correlation_all
from ..reports.analytics import export_luck_curve_all
from ..reports.exporters import export_json, export_hits_csv
from ..reports.importers import import_history_csv, import_outcomes_csv, import_history_html

class Main(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oracle Lottery Predictor")
        self.tabs = QtWidgets.QTabWidget(self)

        # Predict tab
        t1 = QtWidgets.QWidget(); l = QtWidgets.QVBoxLayout(t1)
        self.game = QtWidgets.QComboBox(); self.game.addItems(["lotto","joker","eurojackpot"])
        self.sc = QtWidgets.QSpinBox(); self.sc.setRange(5,2000); self.sc.setValue(400)
        self.sel = QtWidgets.QSpinBox(); self.sel.setRange(1,400); self.sel.setValue(40)
        self.btn = QtWidgets.QPushButton("Predict")
        self.out = QtWidgets.QPlainTextEdit(); self.out.setReadOnly(True)
        form = QtWidgets.QFormLayout()
        form.addRow("Game:", self.game); form.addRow("Candidates:", self.sc); form.addRow("Select:", self.sel)
        l.addLayout(form); l.addWidget(self.btn); l.addWidget(self.out)
        self.btn.clicked.connect(self.do_predict)
        self.tabs.addTab(t1, "Predict")

        # Strength tab
        t2 = QtWidgets.QWidget(); s = QtWidgets.QVBoxLayout(t2)
        self.str_progress = QtWidgets.QProgressBar(); self.str_progress.setValue(0)
        self.lbl_hit = QtWidgets.QLabel("Rolling hit%: –")
        self.lbl_ev  = QtWidgets.QLabel("Mean EV(MC): –")
        self.lbl_info= QtWidgets.QLabel("Status: idle")
        s.addWidget(self.str_progress); s.addWidget(self.lbl_hit); s.addWidget(self.lbl_ev); s.addWidget(self.lbl_info); s.addStretch()
        self.btn_heatmaps.clicked.connect(self.export_heatmaps)
        self.btn_luck.clicked.connect(self.export_luck)
        self.btn_heatmaps.clicked.connect(self.export_heatmaps)
        self.btn_luck.clicked.connect(self.export_luck)
        self.btn_plotly.clicked.connect(self.export_plotly)
        self.btn_backtest.clicked.connect(self.run_backtest)
        self.tabs.addTab(t2, "Strength")

        # Analysis tab
        t4 = QtWidgets.QWidget(); a = QtWidgets.QFormLayout(t4)
        self.an_last = QtWidgets.QSpinBox(); self.an_last.setRange(5, 1000); self.an_last.setValue(50)
        self.an_scen = QtWidgets.QLineEdit(); self.an_scen.setText("baseline:300:30,wide:600:40,deep:400:60")
        self.btn_an = QtWidgets.QPushButton("Run Scenarios & Curves")
        self.btn_tune = QtWidgets.QPushButton("Run Tuner (Optuna)")
        self.btn_repred = QtWidgets.QPushButton("Run Re-Predict (WF)")
        a.addRow("Last draws:", self.an_last)
        a.addRow("Scenarios (name:candidates:select, ...):", self.an_scen)
        a.addRow(self.btn_an)
        a.addRow(self.btn_tune)
        a.addRow(self.btn_repred)
        self.btn_an.clicked.connect(self.run_scenarios_curves)
        self.btn_tune.clicked.connect(self.run_tuner)
        self.btn_repred.clicked.connect(self.run_repredict)
        self.tabs.addTab(t4, "Analysis")

        # Record Outcome tab
        t3 = QtWidgets.QWidget(); r3 = QtWidgets.QFormLayout(t3)
        self.rd_draw = QtWidgets.QLineEdit(); self.rd_draw.setPlaceholderText("e.g., 20250101")
        self.rd_n1 = QtWidgets.QSpinBox(); self.rd_n1.setRange(1,90)
        self.rd_n2 = QtWidgets.QSpinBox(); self.rd_n2.setRange(1,90)
        self.rd_n3 = QtWidgets.QSpinBox(); self.rd_n3.setRange(1,90)
        self.rd_n4 = QtWidgets.QSpinBox(); self.rd_n4.setRange(1,90)
        self.rd_n5 = QtWidgets.QSpinBox(); self.rd_n5.setRange(1,90)
        self.rd_n6 = QtWidgets.QSpinBox(); self.rd_n6.setRange(0,90); self.rd_n6.setValue(0)  # optional 6th
        self.rd_bonus1 = QtWidgets.QSpinBox(); self.rd_bonus1.setRange(0,90); self.rd_bonus1.setValue(0)
        self.rd_bonus2 = QtWidgets.QSpinBox(); self.rd_bonus2.setRange(0,90); self.rd_bonus2.setValue(0)
        self.btn_rec = QtWidgets.QPushButton("Record & Learn")
        self.btn_imp_hist_csv = QtWidgets.QPushButton("Import History CSV")
        self.btn_imp_hist_html = QtWidgets.QPushButton("Import History HTML")
        self.btn_imp_out_csv = QtWidgets.QPushButton("Import Outcomes CSV")
        self.btn_exp_eval = QtWidgets.QPushButton("Export Eval Report")
        r3.addRow("Draw ID:", self.rd_draw)
        nums_row = QtWidgets.QHBoxLayout()
        for w in [self.rd_n1,self.rd_n2,self.rd_n3,self.rd_n4,self.rd_n5,self.rd_n6,self.rd_bonus1,self.rd_bonus2]: nums_row.addWidget(w)
        r3.addRow("Numbers:", QtWidgets.QWidget())
        # embed numbers row under a dummy widget
        nums_container = QtWidgets.QWidget(); nums_container.setLayout(nums_row)
        r3.removeRow(1); r3.addRow("Numbers:", nums_container)
        r3.addRow(self.btn_rec)
        r3.addRow(self.btn_imp_hist_csv)
        r3.addRow(self.btn_imp_hist_html)
        r3.addRow(self.btn_imp_out_csv)
        r3.addRow(self.btn_exp_eval)
        self.tabs.addTab(t3, "Record Outcome")
        self.btn_rec.clicked.connect(self.do_record_outcome)
        self.btn_imp_hist_csv.clicked.connect(self.do_import_history_csv)
        self.btn_imp_hist_html.clicked.connect(self.do_import_history_html)
        self.btn_imp_out_csv.clicked.connect(self.do_import_outcomes_csv)
        self.btn_exp_eval.clicked.connect(self.do_export_eval)
        self.game.currentIndexChanged.connect(self._auto_draw_id)
        self._auto_draw_id()
    

        r = QtWidgets.QVBoxLayout(self); r.addWidget(self.tabs); try_init_sentry(get_sentry_dsn())
        self.resize(820, 560)

    def current_game_id(self): return self.game.currentText()

    def do_predict(self):
        gid = self.current_game_id()
        opts = PredictOptions(candidates=self.sc.value(), select=self.sel.value())
        final = predict_final_portfolio(gid, opts)
        self.out.setPlainText("\n".join(", ".join(map(str,t)) for t in final))
        self._recompute_strength(gid)
        self.lbl_info.setText(f"Predicted {len(final)} tickets for {gid}")

    def _recompute_strength(self, gid: str):
        # Try to compute EV(MC) summary from last predictions
        pp = predictions_path(gid)
        try:
            ev = ev_mc_summary(gid, Path(pp), n_draws=1500)
            ev_mean = float(ev.get("mean", 0.0))
        except Exception:
            ev_mean = 0.0
        series = compute_series(gid, window=50)
        hits = [v for v in series.get("hit_rate", []) if v is not None]
        hit_pct = (100.0 * st.mean(hits)) if hits else 0.0
        self.lbl_hit.setText(f"Rolling hit%: {hit_pct:.2f}%")
        self.lbl_ev.setText(f"Mean EV(MC): {ev_mean:.2f}")
        score = min(100, max(0, int(0.6*hit_pct + 40.0*(1.0/(1.0+math.exp(-ev_mean/10.0)))))) if ev_mean is not None else int(hit_pct)
        self.str_progress.setValue(score)
        series = compute_series(gid, window=50)
        hits = [v for v in series.get("hit_rate", []) if v is not None]
        hit_pct = (100.0 * st.mean(hits)) if hits else 0.0
        self.lbl_hit.setText(f"Rolling hit%: {hit_pct:.2f}%")

        ev_mc = self._estimate_ev_proxy(gid)
        self.lbl_ev.setText(f"Mean EV(MC) proxy: {ev_mc:.2f}")
        score = min(100, max(0, int(0.6*hit_pct + 40.0*(1.0/(1.0+math.exp(-ev_mc/10.0)))))) if ev_mc is not None else int(hit_pct)
        self.str_progress.setValue(score)

    def _estimate_ev_proxy(self, gid: str):
        pp = predictions_path(gid)
        if not os.path.exists(pp): return 0.0
        rows=[]; 
        with open(pp, "r", encoding="utf-8") as f:
            r = csv.reader(f); next(r,None)
            for rr in r:
                nums=[int(x) for x in rr[1:] if x and x.isdigit()]
                if nums: rows.append(nums)
        if not rows: return 0.0
        vals=[]
        for t in rows[:60]:
            gaps = [b-a for a,b in zip(t,t[1:])]
            vals.append(sum(gaps)/len(gaps))
        return float(st.mean(vals)) if vals else 0.0

if __name__ == "__main__":
    app = QtWidgets.QApplication([]); w = Main(); w.show(); app.exec()


    def export_heatmaps(self):
        gid = self.current_game_id()
        out_dir = Path("reports_out"); out_dir.mkdir(parents=True, exist_ok=True)
        co = export_cooccurrence_all(gid, out_dir)
        cr = export_correlation_all(gid, out_dir)
        self.lbl_info.setText(f"Exported heatmaps (PNG/SVG/CSV) → {out_dir}")

    def export_luck(self):
        gid = self.current_game_id()
        # Dummy hit series from dashboard (user can replace with real record outcomes)
        series = compute_series(gid, window=150)
        hit_bin = [1 if (v is not None and v>0.0) else 0 for v in series.get("hit_rate",[])]
        curve = luck_curve_from_hits(hit_bin, half_life=50)
        vals = [v for v in curve.get("luck_curve", []) if v is not None]
        from pathlib import Path
        out_dir = Path("reports_out")
        export_luck_curve_all(hit_bin, out_dir, gid)
        self.lbl_info.setText(f"Exported luck curve (PNG/SVG/CSV) → {out_dir}")


    def export_plotly(self):
        # demo histogram using Strength proxy values to showcase HTML/SVG export
        from pathlib import Path
        from ..reports.plotly_exports import export_histogram
        import random
        vals = [random.random() for _ in range(500)]
        out_dir = Path("reports_out"); out_dir.mkdir(parents=True, exist_ok=True)
        html = export_histogram(vals, "Strength Proxy Histogram", out_dir/"strength_hist.html", out_svg=out_dir/"strength_hist.svg")
        self.lbl_info.setText(f"Exported Plotly → {html}")


    def do_record_outcome(self):
        gid = self.current_game_id()
        try:
            draw_id = int(self.rd_draw.text()) if self.rd_draw.text().strip() else 0
        except Exception:
            draw_id = 0
        nums = [self.rd_n1.value(), self.rd_n2.value(), self.rd_n3.value(), self.rd_n4.value(), self.rd_n5.value()]
        if self.rd_n6.value() > 0: nums.append(self.rd_n6.value())
        if self.rd_bonus1.value() > 0: nums.append(self.rd_bonus1.value())
        if self.rd_bonus2.value() > 0: nums.append(self.rd_bonus2.value())
        check = validate_numbers_for_game(gid, nums)
        if not check.get("ok"):
            self.lbl_info.setText(f"Validation error: {check.get('err')}"); return
        main = check.get("main", []); bonus = check.get("bonus", [])
        # Auto draw id if empty
        if draw_id == 0:
            try: draw_id = _next_draw_id_from_history(gid)
            except Exception: draw_id = 0
        record_outcome(gid, draw_id=draw_id, numbers=main + bonus)
        try: learn_from_outcome(gid, drawn_numbers=main, learning_rate=0.05)
        except Exception: pass
        stats = best_match_against_draw(gid, main)
        report = evaluation_report(gid, main)
        top = evaluate_tickets_vs_draw(gid, main)
        msg = f"Recorded. Best hit: {stats.get('best_match',0)} / tickets={stats.get('tickets',0)}; mean matched={report.get('mean_matched',0):.2f}.\nTop tickets:"\
            + "\n".join([f"#{t['idx']}: m{t['m']} b{t['b']} tier={t['tier']} prize={t['prize']:.2f} -> {t['ticket']}" for t in top[:5]])
        QtWidgets.QMessageBox.information(self, "Outcome Summary", msg)
        self.lbl_info.setText("Outcome recorded & learned. See summary.")
        self._recompute_strength(gid)


    def _auto_draw_id(self):
        gid = self.current_game_id()
        try:
            draw_id = _next_draw_id_from_history(gid)
            self.rd_draw.setText(str(draw_id))
        except Exception:
            pass
        gs = get_game(gid)
        has_bonus = bool(gs and gs.bonus_picks > 0)
        self.rd_bonus1.setVisible(has_bonus)
        self.rd_bonus2.setVisible(has_bonus and gs.bonus_picks >= 2)


    def do_import_history_csv(self):
        gid = self.current_game_id()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select History CSV", "", "CSV Files (*.csv)")
        if not path: return
        try:
            added = import_history_csv(gid, Path(path))
            self.lbl_info.setText(f"Imported {added} history rows from CSV.")
            self._auto_draw_id()
        except Exception as e:
            self.lbl_info.setText(f"Import failed: {e}")

    def do_import_history_html(self):
        gid = self.current_game_id()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select History HTML", "", "HTML Files (*.html *.htm)")
        if not path: return
        try:
            added = import_history_html(gid, Path(path))
            self.lbl_info.setText(f"Imported {added} history rows from HTML.")
            self._auto_draw_id()
        except Exception as e:
            self.lbl_info.setText(f"Import failed: {e}")

    def do_import_outcomes_csv(self):
        gid = self.current_game_id()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Outcomes CSV", "", "CSV Files (*.csv)")
        if not path: return
        try:
            added = import_outcomes_csv(gid, Path(path))
            self.lbl_info.setText(f"Imported {added} outcomes rows from CSV.")
            self._recompute_strength(gid)
        except Exception as e:
            self.lbl_info.setText(f"Import failed: {e}")

    def do_export_eval(self):
        gid = self.current_game_id()
        # Use the latest draw id from history for the report; if record tab has id use that
        try:
            draw_id = int(self.rd_draw.text()) if self.rd_draw.text().strip() else 0
        except Exception:
            draw_id = 0
        # Take last row from history as draw numbers
        from pathlib import Path
        hist = Path("data")/gid/"history.csv"
        nums = []
        if hist.exists():
            import csv
            with hist.open("r", encoding="utf-8") as f:
                r = list(csv.reader(f))
                if len(r) >= 2:
                    last = r[-1]
                    nums = [int(x) for x in last[1:] if x and x.isdigit()]
        if not nums:
            self.lbl_info.setText("No history found to build evaluation report."); return
        rep = evaluation_report_ev(gid, nums)
        out_dir = Path("reports_out"); out_dir.mkdir(parents=True, exist_ok=True)
        export_json(rep, out_dir/f"{gid}_eval_{draw_id or 'latest'}.json")
        export_hits_csv(rep, out_dir/f"{gid}_eval_{draw_id or 'latest'}.csv")
        self.lbl_info.setText(f"Exported evaluation report to reports_out/.")


    def run_backtest(self):
        gid = self.current_game_id()
        N = int(self.spn_backtest.value())
        from pathlib import Path
        from ..reports.backtest import backtest
        from ..reports.exporters import export_backtest_csv
        res = backtest(gid, last=N, per_ticket=False)
        out_dir = Path("reports_out"); out_dir.mkdir(parents=True, exist_ok=True)
        paths = export_backtest_csv(res, out_dir/f"{gid}_backtest_summary_last{N}.csv")
        self.lbl_info.setText(f"Backtest exported → {paths['summary']}")


    def run_scenarios_curves(self):
        gid = self.current_game_id()
        last = int(self.an_last.value())
        scs = self.an_scen.text().strip()
        from pathlib import Path
        from ..reports.scenarios import Scenario, run_scenarios
        from ..reports.exporters import export_scenarios_json
        from ..reports.curves import export_learning_curves, export_hit_threshold_curve
        # parse scenarios
        parsed=[]; 
        for tok in scs.split(","):
            try:
                name,cand,sel = tok.split(":")
                parsed.append(Scenario(name=name, candidates=int(cand), select=int(sel)))
            except Exception:
                pass
        res = run_scenarios(gid, parsed, last=last)
        out_dir = Path("reports_out"); out_dir.mkdir(parents=True, exist_ok=True)
        export_scenarios_json(res, out_dir/f"{gid}_scenarios_last{last}.json")
        export_learning_curves(gid, last, out_dir)
        export_hit_threshold_curve(gid, last, out_dir)
        self.lbl_info.setText(f"Scenarios & curves exported to {out_dir}")


    def run_tuner(self):
        gid = self.current_game_id()
        from pathlib import Path
        from ..cli.tune import main as tune_main
        # Execute tuner in-process (keeps it simple); output goes to reports_out JSON
        try:
            import sys
            argv = sys.argv
            sys.argv = ["olp-tune","--game",gid,"--last",str(self.an_last.value()),"--trials","30","--outdir","reports_out"]
            tune_main()
            sys.argv = argv
            self.lbl_info.setText("Tuner finished → reports_out/*_tuning_results.json")
        except Exception as e:
            self.lbl_info.setText(f"Tuner failed: {e}")

    def run_repredict(self):
        gid = self.current_game_id()
        from ..cli.repredict import main as rep_main
        try:
            import sys
            argv = sys.argv
            sys.argv = ["olp-repredict","--game",gid,"--last",str(self.an_last.value()),"--outdir","reports_out"]
            rep_main()
            sys.argv = argv
            self.lbl_info.setText("Re-predict finished → reports_out/*_repredict_last*.json")
        except Exception as e:
            self.lbl_info.setText(f"Re-predict failed: {e}")
