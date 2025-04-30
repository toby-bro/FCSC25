#!/usr/bin/env python3
import re

import pexpect
from minimum_distance import minimumDistanceOnCube, point


def main() -> None:
    print('Connecting to chall.fcsc.fr:2054...')
    child = pexpect.spawn('nc chall.fcsc.fr 2054')
    child.timeout = 30

    child.logfile = open('/dev/stdout', 'wb')

    alice_pattern = re.compile(r'Alice = \[(\d+), (\d+), (\d+)\]')
    bob_pattern = re.compile(r'Bob\s+= \[(\d+), (\d+), (\d+)\]')
    distance_pattern = re.compile(r'Distance: $')
    flag_pattern = re.compile(r'FCSC{[^}]+}')

    try:
        round_count = 0
        while True:
            child.expect(alice_pattern)

            alice_coords = [
                int(child.match.group(1)),
                int(child.match.group(2)),
                int(child.match.group(3)),
            ]

            child.expect(bob_pattern)

            bob_coords = [
                int(child.match.group(1)),
                int(child.match.group(2)),
                int(child.match.group(3)),
            ]

            alice_point = point(alice_coords)
            bob_point = point(bob_coords)

            distance = minimumDistanceOnCube(32, alice_point, bob_point)

            child.expect(distance_pattern)

            print(f'Sending answer: {distance}')

            child.sendline(str(distance))

            round_count += 1
            print(f'Completed round {round_count}\n')

    except pexpect.EOF:
        print('Connection closed by server')

    except pexpect.TIMEOUT:
        print('Server timeout - no response received')

    except Exception as e:
        print(f'Error: {e!s}')

    finally:
        if child.logfile:
            child.logfile.close()


if __name__ == '__main__':
    main()
