# La quête de l'anneau

[Lien vers le challenge](https://hackropole.fr/fr/challenges/crypto/fcsc2025-crypto-la-quete-de-l-anneau/)

Ici le mécanisme pour chiffrer le message est une "multiplication modulaire" selon l'équation $c \equiv m \cdot iv \pmod s$ avec $c$ le message chiffré, $m$ le message à chiffrer, $iv$ un nombre aléatoire premier avec $s$ et $s$ le 'module' de chiffrement.

Le déchiffrement s'obtient donc avec l'équation $m \equiv c \cdot iv^{-1} \pmod s$ avec $iv^{-1}$ l'inverse de $iv$ dans l'anneau $\mathbb Z / s\mathbb Z$, en gros $iv^{-1} \cdot iv \equiv 1\pmod s $.

Démonstration:

$$
c \cdot iv^{-1} \equiv  (m \cdot iv) \cdot iv^{-1} \pmod s \\
\equiv m \cdot iv^{-1} \cdot iv \pmod s \\
\equiv m \pmod s
$$

On peut réécrire la relation de chiffrement comme :

$$ m \cdot iv - c \equiv 0 \pmod s $$

pour tout triplet chiffré $(m, iv, c)$ chiffré avec $s$. Notamment avec nos deux triplets.

Donc il ne reste plus qu'à chercher le PGCD des deux relations $m_1 \cdot iv_1 - c_1$ et $m_2 \cdot iv_2 - c_2$ pour obtenir un multiple de $s$. Mais au vu des tailles des entiers je pense qu'on devrait tomber sur $s$ (et si quand on essaie de déchiffrer on tombe pas sur FCSC{xxx} alors on se penchera sur ce problème)

Une fois qu'on a $s$ "yapuka" déchiffrer le message et le décoder pour voir s'afficher le flag.

Voici le code qui fait cela

```python
import json
from functools import reduce
from math import gcd

with open('output.txt', 'r') as f:
    data = json.loads(f.read())

triplets = data['data']

differences = [t['c'] - t['m'] * t['iv'] for t in triplets]

differences = [abs(d) for d in differences]
s = reduce(gcd, differences)


def decrypt(c: dict, s: int, bs: int = 64) -> bytes:
    r = b''
    for d in c:
        m = d['c'] * pow(d['iv'], -1, s) % s
        r += int.to_bytes(m, bs, 'big')
    return r


flag = decrypt(data['C'], s, bs=64)
print(f'Flag: {flag.decode()}')
```
