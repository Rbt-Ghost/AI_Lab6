# IA Lab #06 — Tema

Acest folder contine implementari pentru Temele A–D.

## Rulare (Windows / PowerShell)

Asigura-te ca:
- CoppeliaSim este deschis
- scena `pioneer_lab06.ttt` este incarcata

Activeaza venv si instaleaza dependintele:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Tema A — recuperare la obstacol

```powershell
python .\tema\tema_a_recuperare.py
```

Robotul merge inainte, iar la obstacol face automat: inapoi 1s -> viraj random ~90° -> inainte.

## Tema B — Braitenberg cu logging + grafice

Ruleaza (scrie CSV + la final genereaza PNG-uri):

```powershell
python .\tema\tema_b_logging.py
```

Regenerare grafice dintr-un CSV existent:

```powershell
python .\tema\tema_b_grafice.py
```

Fisiere generate:
- `tema/log_braitenberg.csv`
- `tema/plot_traj.png`, `tema/plot_speeds.png`, `tema/plot_heatmap.png`

## Tema C — Explorer (60s)

```powershell
python .\tema\tema_c_explorer.py
```

Fisiere generate:
- `tema/explorer_traj.csv`
- `tema/explorer_traj.png`

## Tema D (Bonus) — Braitenberg "Iubire"

```powershell
python .\tema\tema_d_bonus_iubire.py
```

## Note

- Scripturile pornesc/opresc simularea si opresc motoarele in `finally`.
- Fisierele `.venv/`, `*.csv` si `*.png` sunt ignorate de git prin `.gitignore`.
