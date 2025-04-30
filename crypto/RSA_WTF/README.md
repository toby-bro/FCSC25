# RSA WTF

## Analysis

This challenge has the amusing property of providing us with $p, q, dp, dq$ in a RSA-related challenge.

In this challenge AES CBC is used to encrypt the flag with a key that is a random number that we understand we will have to derive from the $p, q, dp, dq$ aforementioned.

The flag is split into 8-byte blocks that are successively encrypted with this weird key generation method.

What we have is that $dp \cdot k \equiv 1 \pmod {p-1}$ and $dq \cdot k \equiv 1 \pmod {q-1}$.

We guess at that point that we will be using the Chinese remainder theorem (CRT) to solve this problem. So our objective is to transform this into an equivalent problem.

We shall call $X^{-1}$ the inverse of $X$ in the ring $\mathbb Z / n\mathbb Z$, such that $X X^{-1} \equiv 1 \pmod n$
We can transform this into

$$
k \equiv dp ^{-1} \pmod {p-1} \\
k \equiv dq ^{-1} \pmod {q-1}
$$

Which is exactly what we were looking for and now we know that we can determine the remainder of the division of $k$ by the least common multiple of these integers. So we can determine the remainder of the division of $k$ by $lcm(p-1,q-1)$ which will most certainly be $k$ itself given the size of each number.

## Resolution

We used the implementation of the CRT from sympy to save some time. Once we recovered $k$ then there is nothing stopping us from decrypting the flag as we know $iv$. The final script that solved the problem is the following.

```python
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

```
