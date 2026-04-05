"""
Tema B - Generare grafice din CSV (post-procesare).
IA Lab #06 - Inteligență Artificială 2025-2026

Folosire:
	python .\tema\tema_b_grafice.py

Citeste `tema/log_braitenberg.csv` si genereaza 3 PNG:
- tema/plot_traj.png
- tema/plot_speeds.png
- tema/plot_heatmap.png
"""

import os

from tema_b_logging import CSV_PATH, generate_plots


def main():
	if not os.path.exists(CSV_PATH):
		print(f"Nu exista CSV: {CSV_PATH}")
		print("Ruleaza mai intai: python .\\tema\\tema_b_logging.py")
		return

	generate_plots(CSV_PATH)


if __name__ == '__main__':
	main()
