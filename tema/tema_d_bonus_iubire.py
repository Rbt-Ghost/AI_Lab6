"""
Tema D (Bonus) - Braitenberg "Iubire".
IA Lab #06 - Inteligență Artificială 2025-2026

Descriere (conform cerintei):
- conexiuni ipsilaterale inhibitorii:
	* senzorii din fata-stanga reduc viteza motorului stang
	* senzorii din fata-dreapta reduc viteza motorului drept
- efect emergent: robotul tinde sa se "apropie" de stimul, dar incetineste si se opreste aproape

Ctrl+C pentru oprire.
"""

import time

from coppeliasim_zmqremoteapi_client import RemoteAPIClient


V_BASE = 3.0
V_MAX = 6.0
K_SENSOR = 5.0
SENSOR_MAX = 1.0

# Folosim 8 senzori frontali (0..7). Pentru "iubire":
# - partea stanga (0..3) inhiba motorul stang
# - partea dreapta (4..7) inhiba motorul drept
# Ponderile sunt negative pe motorul ipsilateral; celalalt motor ramane (aproape) neafectat.
WEIGHTS = [
	(-1.0, 0.0),  # S0
	(-1.5, 0.0),  # S1
	(-2.0, 0.0),  # S2
	(-2.5, 0.0),  # S3
	(0.0, -2.5),  # S4
	(0.0, -2.0),  # S5
	(0.0, -1.5),  # S6
	(0.0, -1.0),  # S7
]

CONTROL_DT = 0.05


def clamp(x, lo, hi):
	return max(lo, min(hi, x))


def iubire_velocities(sim, sensors):
	v_left = V_BASE
	v_right = V_BASE

	for i, (w_l, w_r) in enumerate(WEIGHTS):
		result, distance, *_ = sim.readProximitySensor(sensors[i])
		if result:
			proximity = 1.0 - (distance / SENSOR_MAX)
			proximity = clamp(proximity, 0.0, 1.0)
			v_left += K_SENSOR * w_l * proximity
			v_right += K_SENSOR * w_r * proximity

	v_left = clamp(v_left, -V_MAX, V_MAX)
	v_right = clamp(v_right, -V_MAX, V_MAX)
	return v_left, v_right


def main():
	client = RemoteAPIClient()
	sim = client.require('sim')

	left_motor = sim.getObject('/PioneerP3DX/leftMotor')
	right_motor = sim.getObject('/PioneerP3DX/rightMotor')
	sensors = [
		sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]')
		for i in range(16)
	]

	sim.startSimulation()
	print('Tema D pornita (Braitenberg "Iubire"). Ctrl+C pentru oprire.\n')

	try:
		iteration = 0
		while True:
			v_left, v_right = iubire_velocities(sim, sensors)

			sim.setJointTargetVelocity(left_motor, v_left)
			sim.setJointTargetVelocity(right_motor, v_right)

			if iteration % 20 == 0:
				print(f"v_stang={v_left:+.2f} rad/s  |  v_drept={v_right:+.2f} rad/s")

			iteration += 1
			time.sleep(CONTROL_DT)

	except KeyboardInterrupt:
		print('\nOprire manuala.')
	finally:
		sim.setJointTargetVelocity(left_motor, 0.0)
		sim.setJointTargetVelocity(right_motor, 0.0)
		sim.stopSimulation()


if __name__ == '__main__':
	main()
