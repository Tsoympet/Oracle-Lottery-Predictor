
# Oracle Lottery Predictor (All-in)

Ensemble of Bayesian/Dirichlet/shrinkage/MRF scorers + Monte-Carlo EV, Luck/Unluck
adaptive policy, BMA combiner, and CP-SAT portfolio optimization. Windows installer
via PyInstaller + Inno Setup (with optional code signing).

## Quickstart
```bash
pip install -r requirements.txt
pytest -q

# fetch history (live OPAP scrape)
olp-fetch-opap --game joker
olp-features    --game joker

# predict
olp-predict --game joker --candidates 400 --select 40

# desktop
python -m oracle_lottery.ui.main_window
```


## Strength Panel & Reports
- EV(MC) summary (mean/median/p95) from last predictions
- Luck/Unluck curve (EWMA)
- Heatmaps: co-occurrence & Pearson correlation (PNG exports in `reports_out/`)

## CI/Release (Windows)
Tag `v1.0.0` → PyInstaller build → (optional) Code-sign → Inno Setup installer → GitHub Release.



## History directory (Excel import)
You can drop OPAP historical Excel files under `history/<game>/history.xlsx`. Then run:
```bash
olp-import-history --game joker
```
This will write a normalized `history.csv` in `history/<game>/` and also to `data/<game>/history.csv` used by the app.
