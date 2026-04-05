"""
Tema C - Robot Explorer (nivel avansat).
IA Lab #06 - Inteligență Artificială 2025-2026

Comportament:
- Wall-following pe peretele din dreapta (P-controller)
- Recuperare la obstacol frontal / blocaj:
	BACKWARD (1s) -> TURNING (stanga/dreapta random, ~90°) -> WALL_FOLLOW

Cerintele temei:
- Ruleaza cel putin 60s (se opreste automat dupa durata)
- Salveaza traiectoria XY si graficul la final

Ctrl+C pentru oprire manuala.
"""

import csv
import os
import random
import time
from enum import Enum

from coppeliasim_zmqremoteapi_client import RemoteAPIClient


# --- Parametri wall-following ---
V_BASE = 2.0  # rad/s
TARGET_DIST = 0.4  # m
K_P = 3.0
SENSOR_MAX = 1.0

RIGHT_SENSORS = [8, 9]
FRONT_SENSORS = [3, 4]

FRONT_RECOVERY = 0.35  # m (declanseaza recuperare)

# --- Parametri recuperare ---
V_BACK = 1.5
V_TURN = 2.0
T_BACK = 1.0
T_TURN = 1.57

CONTROL_DT = 0.05

RUN_DURATION = 60.0  # secunde

OUT_CSV = os.path.join(os.path.dirname(__file__), 'explorer_traj.csv')
OUT_PNG = os.path.join(os.path.dirname(__file__), 'explorer_traj.png')


class Mode(Enum):
	WALL_FOLLOW = 1
	BACKWARD = 2
	TURNING = 3


def clamp(x, lo, hi):
	return max(lo, min(hi, x))


def set_velocity(sim, left_motor, right_motor, v_left, v_right):
	sim.setJointTargetVelocity(left_motor, v_left)
	sim.setJointTargetVelocity(right_motor, v_right)


def read_min_dist(sim, sensors, indices):
	min_dist = SENSOR_MAX
	for idx in indices:
		result, dist, *_ = sim.readProximitySensor(sensors[idx])
		if result and dist < min_dist:
			min_dist = dist
	return min_dist


def compute_wall_follow(v_base, dist_right):
	"""Returneaza (v_left, v_right, state_str) pentru wall-follow."""
	if dist_right >= SENSOR_MAX * 0.95:
		# cauta perete: viraj usor dreapta
		return v_base, v_base * 0.5, 'CAUTA_PERETE'

	error = dist_right - TARGET_DIST
	v_left = v_base + K_P * error
	v_right = v_base - K_P * error

	cap = v_base * 1.5
	v_left = clamp(v_left, -cap, cap)
	v_right = clamp(v_right, -cap, cap)

	return v_left, v_right, f'URMARIRE dr={dist_right:.3f} err={error:+.3f}'


def safe_import_matplotlib():
	try:
		import matplotlib.pyplot as plt
		return plt
	except Exception:
		return None


def plot_trajectory(csv_path, out_png):
	plt = safe_import_matplotlib()
	if plt is None:
		print('[WARN] matplotlib nu este disponibil; nu pot salva graficul.')
		return

	x = []
	y = []
	with open(csv_path, 'r', newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for r in reader:
			x.append(float(r['pos_x']))
			y.append(float(r['pos_y']))

	if not x:
		print('[WARN] Traiectorie goala; nu salvez grafic.')
		return

	plt.figure(figsize=(6, 6))
	plt.plot(x, y, linewidth=1.5)
	plt.title('Explorer - Traiectorie XY')
	plt.xlabel('pos_x [m]')
	plt.ylabel('pos_y [m]')
	plt.axis('equal')
	plt.grid(True, alpha=0.3)
	plt.tight_layout()
	plt.savefig(out_png, dpi=150)
	plt.close()
	print(f'Grafic salvat: {out_png}')


def main():
	client = RemoteAPIClient()
	sim = client.require('sim')

	random.seed()

	robot = sim.getObject('/PioneerP3DX')
	left_motor = sim.getObject('/PioneerP3DX/leftMotor')
	right_motor = sim.getObject('/PioneerP3DX/rightMotor')
	sensors = [
		sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
		for i in range(16)
	]

	os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

	mode = Mode.WALL_FOLLOW
	mode_start_wall = time.time()
	turn_dir = +1

	sim.startSimulation()
	start_sim_t = float(sim.getSimulationTime())
	print('Tema C pornita (Explorer). Ruleaza 60s; Ctrl+C pentru oprire.\n')
	print(f'Log: {OUT_CSV}')

	f = open(OUT_CSV, 'w', newline='', encoding='utf-8')
	writer = csv.writer(f)
	writer.writerow(['timestamp', 'mode', 'pos_x', 'pos_y', 'dist_front', 'dist_right', 'v_left', 'v_right'])
	f.flush()

	iteration = 0

	try:
		while True:
			now_wall = time.time()
			mode_elapsed = now_wall - mode_start_wall

			sim_t = float(sim.getSimulationTime())
			if sim_t - start_sim_t >= RUN_DURATION:
				print('\n[OK] Durata de 60s atinsa. Oprire automata.')
				break

			dist_front = read_min_dist(sim, sensors, FRONT_SENSORS)
			dist_right = read_min_dist(sim, sensors, RIGHT_SENSORS)

			# Tranzitii
			if mode == Mode.WALL_FOLLOW and dist_front < FRONT_RECOVERY:
				mode = Mode.BACKWARD
				mode_start_wall = now_wall
				mode_elapsed = 0.0

			elif mode == Mode.BACKWARD and mode_elapsed >= T_BACK:
				mode = Mode.TURNING
				mode_start_wall = now_wall
				mode_elapsed = 0.0
				turn_dir = random.choice([+1, -1])

			elif mode == Mode.TURNING and mode_elapsed >= T_TURN:
				mode = Mode.WALL_FOLLOW
				mode_start_wall = now_wall
				mode_elapsed = 0.0

			# Actiuni
			if mode == Mode.WALL_FOLLOW:
				v_l, v_r, desc = compute_wall_follow(V_BASE, dist_right)
				state_str = desc

			elif mode == Mode.BACKWARD:
				v_l, v_r = -V_BACK, -V_BACK
				state_str = f'BACKWARD t={mode_elapsed:.2f}/{T_BACK:.2f}'

			else:  # TURNING
				if turn_dir > 0:
					v_l, v_r = -V_TURN, +V_TURN
					dir_str = 'LEFT'
				else:
					v_l, v_r = +V_TURN, -V_TURN
					dir_str = 'RIGHT'
				state_str = f'TURN {dir_str} t={mode_elapsed:.2f}/{T_TURN:.2f}'

			set_velocity(sim, left_motor, right_motor, v_l, v_r)

			pos = sim.getObjectPosition(robot, sim.handle_world)
			writer.writerow([sim_t, mode.name, pos[0], pos[1], dist_front, dist_right, v_l, v_r])

			if iteration % 20 == 0:
				f.flush()
				print(f"t={sim_t:6.2f}s  {state_str:<30}  front={dist_front:.3f}  right={dist_right:.3f}")

			iteration += 1
			time.sleep(CONTROL_DT)

	except KeyboardInterrupt:
		print('\nOprire manuala.')
	finally:
		try:
			f.flush()
			f.close()
		except Exception:
			pass

		set_velocity(sim, left_motor, right_motor, 0.0, 0.0)
		sim.stopSimulation()

		plot_trajectory(OUT_CSV, OUT_PNG)


if __name__ == '__main__':
	main()
