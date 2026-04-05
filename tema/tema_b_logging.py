"""
Tema B - Braitenberg cu inregistrare de date.
IA Lab #06 - Inteligență Artificială 2025-2026

Ruleaza vehiculul Braitenberg (tip "Frica") si salveaza in CSV:
	timestamp, v_left, v_right, s0..s7, pos_x, pos_y

Dupa Ctrl+C:
- inchide CSV
- genereaza 3 grafice PNG (traiectorie, viteze, heatmap senzori)

Nota: pentru grafice e nevoie de matplotlib.
"""

import csv
import os
import time

from coppeliasim_zmqremoteapi_client import RemoteAPIClient


# --- Parametri Braitenberg (identici cu cerinta 3.5) ---
V_BASE = 3.0
V_MAX = 6.0
K_SENSOR = 6.0
SENSOR_MAX = 1.0

WEIGHTS = [
	(+0.5, -0.5),
	(+1.0, -1.0),
	(+1.5, -1.5),
	(+2.0, -2.0),
	(-2.0, +2.0),
	(-1.5, +1.5),
	(-1.0, +1.0),
	(-0.5, +0.5),
]

CONTROL_DT = 0.05  # 20 Hz

CSV_PATH = os.path.join(os.path.dirname(__file__), 'log_braitenberg.csv')
PLOT_TRAJ = os.path.join(os.path.dirname(__file__), 'plot_traj.png')
PLOT_SPEED = os.path.join(os.path.dirname(__file__), 'plot_speeds.png')
PLOT_HEAT = os.path.join(os.path.dirname(__file__), 'plot_heatmap.png')


def clamp(x, lo, hi):
	return max(lo, min(hi, x))


def read_sensor_proximity(sim, sensor_handle):
	"""Returneaza (proximity, detected, distance).

	proximity in [0,1], unde 1 inseamna foarte aproape.
	"""
	result, distance, *_ = sim.readProximitySensor(sensor_handle)
	if result:
		proximity = 1.0 - (distance / SENSOR_MAX)
		proximity = clamp(proximity, 0.0, 1.0)
		return proximity, True, distance
	return 0.0, False, SENSOR_MAX


def braitenberg_step(sim, sensors):
	"""Calculeaza vitezele si valorile s0..s7 (proximity)."""
	v_left = V_BASE
	v_right = V_BASE

	s_values = []
	for i, (w_l, w_r) in enumerate(WEIGHTS):
		proximity, detected, _ = read_sensor_proximity(sim, sensors[i])
		s_values.append(proximity)
		if detected:
			v_left += K_SENSOR * w_l * proximity
			v_right += K_SENSOR * w_r * proximity

	v_left = clamp(v_left, -V_MAX, V_MAX)
	v_right = clamp(v_right, -V_MAX, V_MAX)
	return v_left, v_right, s_values


def safe_import_matplotlib():
	try:
		import matplotlib.pyplot as plt
		return plt
	except Exception:
		return None


def load_csv_rows(csv_path):
	rows = []
	with open(csv_path, 'r', newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for r in reader:
			rows.append(r)
	return rows


def generate_plots(csv_path):
	plt = safe_import_matplotlib()
	if plt is None:
		print("[WARN] matplotlib nu este disponibil; sar peste generarea graficelor.")
		print("       Instaleaza: pip install matplotlib")
		return

	rows = load_csv_rows(csv_path)
	if not rows:
		print("[WARN] CSV gol; nu generez grafice.")
		return

	t = [float(r['timestamp']) for r in rows]
	v_left = [float(r['v_left']) for r in rows]
	v_right = [float(r['v_right']) for r in rows]
	x = [float(r['pos_x']) for r in rows]
	y = [float(r['pos_y']) for r in rows]

	s = []
	for i in range(8):
		col = f's{i}'
		s.append([float(r[col]) for r in rows])
	# s = list of 8 lists; heatmap wants (8, N)

	# 1) Traiectorie XY
	plt.figure(figsize=(6, 6))
	plt.plot(x, y, linewidth=1.5)
	plt.title('Traiectorie robot (XY)')
	plt.xlabel('pos_x [m]')
	plt.ylabel('pos_y [m]')
	plt.axis('equal')
	plt.grid(True, alpha=0.3)
	plt.tight_layout()
	plt.savefig(PLOT_TRAJ, dpi=150)
	plt.close()

	# 2) Viteze in timp
	plt.figure(figsize=(8, 4))
	plt.plot(t, v_left, label='v_left')
	plt.plot(t, v_right, label='v_right')
	plt.title('Viteze motoare in timp')
	plt.xlabel('timestamp [s]')
	plt.ylabel('viteza [rad/s]')
	plt.grid(True, alpha=0.3)
	plt.legend()
	plt.tight_layout()
	plt.savefig(PLOT_SPEED, dpi=150)
	plt.close()

	# 3) Heatmap senzori
	import numpy as np

	data = np.array(s)  # (8, N)
	plt.figure(figsize=(10, 4))
	plt.imshow(data, aspect='auto', origin='lower', interpolation='nearest')
	plt.title('Heatmap activare senzori (s0..s7)')
	plt.xlabel('timestep')
	plt.ylabel('sensor index')
	plt.yticks(list(range(8)), [f's{i}' for i in range(8)])
	plt.colorbar(label='proximity [0..1]')
	plt.tight_layout()
	plt.savefig(PLOT_HEAT, dpi=150)
	plt.close()

	print("Grafice salvate:")
	print(f"- {PLOT_TRAJ}")
	print(f"- {PLOT_SPEED}")
	print(f"- {PLOT_HEAT}")


def main():
	client = RemoteAPIClient()
	sim = client.require('sim')

	robot = sim.getObject('/PioneerP3DX')
	left_motor = sim.getObject('/PioneerP3DX/leftMotor')
	right_motor = sim.getObject('/PioneerP3DX/rightMotor')
	sensors = [
		sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
		for i in range(16)
	]

	os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

	sim.startSimulation()
	print("Tema B pornita (Braitenberg + logging). Ctrl+C pentru oprire.\n")
	print(f"CSV: {CSV_PATH}")

	f = open(CSV_PATH, 'w', newline='', encoding='utf-8')
	writer = csv.writer(f)

	head = ['timestamp', 'v_left', 'v_right'] + [f's{i}' for i in range(8)] + ['pos_x', 'pos_y']
	writer.writerow(head)
	f.flush()

	iteration = 0

	try:
		while True:
			timestamp = float(sim.getSimulationTime())
			v_l, v_r, s_values = braitenberg_step(sim, sensors)

			sim.setJointTargetVelocity(left_motor, v_l)
			sim.setJointTargetVelocity(right_motor, v_r)

			pos = sim.getObjectPosition(robot, sim.handle_world)
			row = [timestamp, v_l, v_r] + s_values + [pos[0], pos[1]]
			writer.writerow(row)

			# flush rar ca sa nu incetineasca
			if iteration % 20 == 0:
				f.flush()
				print(f"t={timestamp:6.2f}s  vL={v_l:+.2f}  vR={v_r:+.2f}")

			iteration += 1
			time.sleep(CONTROL_DT)

	except KeyboardInterrupt:
		print("\nOprire manuala.")
	finally:
		try:
			f.flush()
			f.close()
		except Exception:
			pass

		sim.setJointTargetVelocity(left_motor, 0.0)
		sim.setJointTargetVelocity(right_motor, 0.0)
		sim.stopSimulation()

		# generare grafice din CSV
		generate_plots(CSV_PATH)


if __name__ == '__main__':
	main()
