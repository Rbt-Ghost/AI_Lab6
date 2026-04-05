"""
Tema A - Evitare cu recuperare (extindere Cerinta 3.4).
IA Lab #06 - Inteligență Artificială 2025-2026

Comportament:
- FORWARD: merge inainte
- BACKWARD: da inapoi T_BACK secunde cand vede obstacol
- TURNING: vireaza stanga/dreapta ~90° si revine la FORWARD

Ctrl+C pentru oprire.
"""

import random
import time
from enum import Enum

from coppeliasim_zmqremoteapi_client import RemoteAPIClient


# --- Parametri ---
V_FORWARD = 2.0  # rad/s
V_BACK = 1.5  # rad/s
V_TURN = 2.0  # rad/s

STOP_DISTANCE = 0.5  # m
FRONT_SENSORS = [2, 3, 4, 5]
SENSOR_MAX = 1.0

T_BACK = 1.0  # s
T_TURN = 1.57  # s (~90°)

CONTROL_DT = 0.05  # s (20 Hz)


class RobotState(Enum):
	FORWARD = 1
	BACKWARD = 2
	TURNING = 3


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


def next_state(current_state, dist_front, state_elapsed, state_duration):
	"""Decide tranzitia intre stari.

	Args:
		current_state: RobotState curent.
		dist_front: distanta minima frontala (m).
		state_elapsed: secunde petrecute in starea curenta.
		state_duration: durata tinta a starii curente (secunde) sau None.
	"""
	if current_state == RobotState.FORWARD:
		if dist_front < STOP_DISTANCE:
			return RobotState.BACKWARD
		return RobotState.FORWARD

	if current_state == RobotState.BACKWARD:
		if state_elapsed >= state_duration:
			return RobotState.TURNING
		return RobotState.BACKWARD

	if current_state == RobotState.TURNING:
		if state_elapsed >= state_duration:
			return RobotState.FORWARD
		return RobotState.TURNING

	return RobotState.FORWARD


def main():
	client = RemoteAPIClient()
	sim = client.require('sim')

	left_motor = sim.getObject('/PioneerP3DX/leftMotor')
	right_motor = sim.getObject('/PioneerP3DX/rightMotor')
	sensors = [
		sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
		for i in range(16)
	]

	# Seed random for reproducible-ish behavior per run
	random.seed()

	state = RobotState.FORWARD
	state_start_wall = time.time()
	turn_dir = +1  # +1 = stanga, -1 = dreapta

	sim.startSimulation()
	print("Tema A pornita (recuperare la obstacol). Ctrl+C pentru oprire.\n")

	try:
		while True:
			dist_front = read_min_dist(sim, sensors, FRONT_SENSORS)
			now = time.time()
			elapsed = now - state_start_wall

			if state == RobotState.FORWARD:
				duration = None
			elif state == RobotState.BACKWARD:
				duration = T_BACK
			else:
				duration = T_TURN

			new_state = next_state(state, dist_front, elapsed, duration)

			if new_state != state:
				state = new_state
				state_start_wall = now
				elapsed = 0.0

				if state == RobotState.TURNING:
					turn_dir = random.choice([+1, -1])

			if state == RobotState.FORWARD:
				set_velocity(sim, left_motor, right_motor, V_FORWARD, V_FORWARD)
				print(f"[FORWARD ] front={dist_front:.3f} m")

			elif state == RobotState.BACKWARD:
				set_velocity(sim, left_motor, right_motor, -V_BACK, -V_BACK)
				print(f"[BACKWARD] front={dist_front:.3f} m  t={elapsed:.2f}/{T_BACK:.2f}s")

			else:  # TURNING
				if turn_dir > 0:
					# vireaza stanga: stanga inapoi, dreapta inainte
					set_velocity(sim, left_motor, right_motor, -V_TURN, +V_TURN)
					dir_str = "LEFT"
				else:
					# vireaza dreapta
					set_velocity(sim, left_motor, right_motor, +V_TURN, -V_TURN)
					dir_str = "RIGHT"
				print(f"[TURNING ] dir={dir_str:<5}  t={elapsed:.2f}/{T_TURN:.2f}s")

			time.sleep(CONTROL_DT)

	except KeyboardInterrupt:
		print("\nOprire manuala.")
	finally:
		set_velocity(sim, left_motor, right_motor, 0.0, 0.0)
		sim.stopSimulation()


if __name__ == '__main__':
	main()
