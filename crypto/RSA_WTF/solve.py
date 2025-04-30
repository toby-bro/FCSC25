import json

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.number import inverse
from Crypto.Util.Padding import unpad
from sympy import gcd
from sympy.ntheory.modular import crt

with open('output.txt', 'r') as f:
    data = json.load(f)

flag_bytes = b''

for block_data in data:
    iv_hex, c_hex, p, q, dp, dq = block_data

    iv = bytes.fromhex(iv_hex)
    c = bytes.fromhex(c_hex)

    mod1 = p - 1
    mod2 = q - 1

    try:
        inv_dp = inverse(dp, mod1)
        inv_dq = inverse(dq, mod2)
    except ValueError as e:
        print(f'Error calculating inverse for block: {e}')
        print(f'p={p}, q={q}, dp={dp}, dq={dq}')
        raise ValueError('We should definitely never arrived on this line.') from e

    k_tuple = crt([mod1, mod2], [inv_dp, inv_dq])

    if k_tuple is None:
        print('CRT failed for a block.')
        g = gcd(mod1, mod2)
        print(f'Checking consistency: {inv_dp % g} vs {inv_dq % g}')
        raise ValueError('CRT failed for a block : report the bug to sympy if p-1 and q-1 are coprime.')

    k = k_tuple[0]

    aes_key = SHA256.new(str(k).encode()).digest()

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    try:
        decrypted_block = unpad(cipher.decrypt(c), AES.block_size)
        flag_bytes += decrypted_block
    except ValueError as e:
        print(f'Error unpadding block: {e}, which is also completely abnormal.')

print(flag_bytes.decode())
