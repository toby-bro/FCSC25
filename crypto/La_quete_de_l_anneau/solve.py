import json
from functools import reduce
from math import gcd

with open('output.txt', 'r') as f:
    data = json.loads(f.read())

triplets = data['data']

differences = [t['c'] - t['m'] * t['iv'] for t in triplets]

differences = [abs(d) for d in differences]
s = reduce(gcd, differences)

# print(f'Found modulus s: {s}')


def decrypt(c: dict, s: int, bs: int = 64) -> bytes:
    r = b''
    for d in c:
        m = d['c'] * pow(d['iv'], -1, s) % s
        r += int.to_bytes(m, bs, 'big')
    return r


flag = decrypt(data['C'], s, bs=64)
print(f'Flag: {flag.decode()}')
