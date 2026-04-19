"""
Controls
--------
w / s : forward / backward
a / d : strafe left / right
q / e : rotate left / right
space : stop
r     : stand up
f     : stand down
z / x : decrease / increase speed
ESC   : quit
"""

import sys
import time
import select
import termios
import tty

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def get_key(timeout):
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
        return sys.stdin.read(1)
    return None


def Teleoperation():

    if len(sys.argv) < 2:
        print("Usage: python3 Teleoperation.py <network_interface>")
        print("Example: python3 Teleoperation.py wlan0")
        return

    net_iface = sys.argv[1]

    print("Initializing connection to Go2...")
    ChannelFactoryInitialize(0, net_iface)

    sport = SportClient()
    sport.SetTimeout(10.0)
    sport.Init()

    print("Connected to robot")

    vx = 0
    vy = 0
    yaw = 0

    max_vx = 0.6
    max_vy = 0.4
    max_yaw = 1.0

    speed_scale = 0.5

    step_vx = 0.1
    step_vy = 0.1
    step_yaw = 0.2

    hz = 50
    dt = 1.0 / hz

    last_key_time = time.time()
    deadman = 0.35

    print("\nKeyboard Controls:")
    print("w/s forward/back")
    print("a/d strafe")
    print("q/e rotate")
    print("space stop")
    print("z/x speed down/up")
    print("r stand up")
    print("f stand down")
    print("ESC quit\n")

    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())

        while True:

            start = time.time()

            key = get_key(0)

            if key is not None:

                last_key_time = start

                if ord(key) == 27:
                    break

                if key == " ":
                    vx = vy = yaw = 0

                elif key == "w":
                    vx += step_vx

                elif key == "s":
                    vx -= step_vx

                elif key == "a":
                    vy += step_vy

                elif key == "d":
                    vy -= step_vy

                elif key == "q":
                    yaw += step_yaw

                elif key == "e":
                    yaw -= step_yaw

                elif key == "z":
                    speed_scale = clamp(speed_scale - 0.05, 0.05, 1)

                elif key == "x":
                    speed_scale = clamp(speed_scale + 0.05, 0.05, 1)

                elif key == "r":
                    sport.StandUp()

                elif key == "f":
                    sport.StandDown()

            if (start - last_key_time) > deadman:
                vx = vy = yaw = 0
            else:
                vx *= 0.9
                vy *= 0.9
                yaw *= 0.9

            vx_cmd = clamp(vx, -max_vx * speed_scale, max_vx * speed_scale)
            vy_cmd = clamp(vy, -max_vy * speed_scale, max_vy * speed_scale)
            yaw_cmd = clamp(yaw, -max_yaw * speed_scale, max_yaw * speed_scale)

            sport.Move(vx_cmd, vy_cmd, yaw_cmd)

            print(
                f"\rvx {vx_cmd:.2f}  vy {vy_cmd:.2f}  yaw {yaw_cmd:.2f}  speed {speed_scale:.2f}",
                end="",
                flush=True,
            )

            elapsed = time.time() - start
            time.sleep(max(0, dt - elapsed))

    finally:

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        print("\nStopping robot")

        try:
            sport.StopMove()
        except:
            sport.Move(0, 0, 0)


if __name__ == "__main__":
    Teleoperation()