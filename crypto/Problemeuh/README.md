# Problèmeuh

Ce challenge très intéressant est en gros surtout un problème d'arithmétique des nombres entiers. Ça m'a amusé de pouvoir en refaire. Allons-y pour la résolution.

Les contraintes sont que

$$(a,b,c,x,y) \in \mathbb Z ^5$$

et que

$$
\left \{ \begin{align*}
a &> 0 \\
a &= 487 c \\
159 a &= 485 b \\
x^2 &= a + b \\
y ( 3y &- 1 ) = 2b \\
\end{align*} \right .
$$

D'où

$$
\left \{ \begin{align*}
a &> 0 \\
a &= 487 c \\
159 a &= 485 b \\
x^2 &= a + \frac {159} {485} a \\
y ( 3y &- 1 ) = 2b \\
\end{align*} \right .
$$

$$
\left \{ \begin{align*}
a &> 0 \\
a &= 487 c \\
159 a &= 485 b \\
x^2 &= a (1 + \frac{159}{485}) \\
y ( 3y &- 1 ) = 2b \\
\end{align*} \right .
$$

$$
\left \{ \begin{align*}
a &> 0 \\
a &= 487 c \\
159 a &= 485 b \\
x^2 &=  487 c \left(1 + \frac{159}{485}\right) \\
y ( 3y &- 1 ) = 2b \\
\end{align*} \right .
$$

On va maintenant s'intéresser particulièrement à la 4ème équation. On peut supposer sans nuire à la généralité que $x \in \mathbb N$.
Puisqu'on est dans les nombres entiers on a que la décomposition en facteurs premiers de $x$ est unique, selon le théorème fondamental de l'arithmétique. Il s'en suit que tout facteur premier de $x$ se retrouve également dans la décomposition de $x^2$ mais sa puissance est doublée.

Donc $487 c \left(\frac{485 + 159}{485}\right) $ est un nombre entier qui divise $x^2$.

On notera $\perp$ le symbole est premier avec

Or $485 \perp 644$ et $487 \perp 485$ et $644 = 2^2 \cdot 7 \cdot 23$.
On peut réécrire notre équation comme

$$
x^2 = 2^2 \cdot 7 \cdot 23 \cdot \frac{487}{485} c
$$

Pour que $x^2$ soit entier on a donc $ c \equiv 0 \pmod {485} $.

Ensuite pour que tous les facteurs premiers de $x$ soit présents au double de leur puissance dans la décomposition de $x^2$ alors on a

$$
\left \{ \begin{align*}
c & \equiv 0 \pmod{487} \\
c & \equiv 0 \pmod{7} \\
c & \equiv 0 \pmod{23} \\
\end{align*} \right .
$$

Puisque $485$ est premier avec tous les autres facteurs premiers ci-dessus pour simplifier les notations on va le conserver tel quel sans le factoriser.

D'où il existe $n \in \mathbb N^*$ tel que

$$ c = 487 \cdot 7 \cdot 23 \cdot 485 \cdot n^2 $$

On obtient donc immédiatement que

$$
\left \{ \begin{align*}
a &= 487^2 \cdot 7 \cdot 23 \cdot 485 \cdot n^2 \\
b &= 159 \cdot 487^2 \cdot 7 \cdot 23 \cdot n^2 \\
\end{align*}\right .
$$

On a par ailleurs immédiatement qu'un tel $a$ est strictement positif.

Étudions à présent l'équation donnée par $y$, à savoir $y(3y - 1) = 2b \Leftrightarrow 3y^2 - y - 2b = 0$

Notons $\Delta = d^2$ le discriminant de cette équation et $d$ sa racine qui doit être entière puisque le système cherche une solution entière.

On a

$$
\Delta = d^2 = (-1)^2 - 4 (-2b) (3) = 1 + 24 b \\
\Leftrightarrow d^2 = 1 + 24 \cdot 159 \cdot 487^2 \cdot 7 \cdot 23 \cdot n^2 \\
\Leftrightarrow  \left \{ \begin{align*}
1  &= d^2 - K n^2 \\ \mathrm{avec} \; K&=24 \cdot 159 \cdot 487^2 \cdot 7 \cdot 23 \end{align*} \right .
$$

Et après quelques recherches sur internet on reconnaît bien sûr une équation de Pell.

Sans plus d'ambages nous l'avons résolue avec la méthode des [fractions continues](https://fr.wikipedia.org/wiki/%C3%89quation_de_Pell-Fermat#Fraction_continue).

Puisque ce problème revient à trouver une solution, pas forcément toutes les solutions, si on trouve une telle solution $(d, n)$ à ce problème alors nous obtenons directement un 5-uplet $(a, b, c, x, y)$ d'entiers valides, et je suppose que les organisateurs de ce challenge ont choisi comme flag la solution la plus petite.

Par ailleurs pour que $y$ soit un entier naturel vous me ferez remarquer que je n'ai pas utilisé le fait qu'il fallait que $y = \frac{1 \pm d}{6}$ soit un entier. Mais figurez vous que cette condition est vérifiée puisqu'on avait $d^2 - 1 = 24b$ donc $(d+1)(d-1) = 6 \cdot 2 ^2 \cdot b$.
Comme $d^2 = 1+Kn^2$, avec $K$ pair et divisible par 3 (car facteur de 24), alors $d$ est impair et non divisible par 3. Donc $d \equiv 1$ ou $5 \pmod 6$. Si $d \equiv 1 \pmod 6$, alors $1-d$ est divisible par 6. Si $d \equiv 5 \pmod 6$, alors $1+d$ est divisible par 6. Donc l'une des deux valeurs $\frac{1+d}{6}$ ou $\frac{1-d}{6}$ est entière.
Donc nécessairement si on trouve une solution à l'équation de Pell alors on trouve au moins un $y$ entier naturel.

Voici donc le programme qui trouve une solution à cette équation de Pell et donc au problèmeuh amusant quoique je pense un peu bovinant à créer pour l'orga. Merci encore.

```python
import math
import sys
from hashlib import sha256

sys.set_int_max_str_digits(31337)


def flag(a: int, b: int, c: int, x: int, y: int) -> None:

    try:
        ## Ce que le programme faisait initialement
        # a, b, c, x, y = [int(input(f'{x} = ')) for x in 'abcxy']
        assert a > 0
        assert a == 487 * c
        assert 159 * a == 485 * b
        assert x**2 == a + b
        assert y * (3 * y - 1) == 2 * b
        h = sha256(str(a).encode()).hexdigest()
        print(f'FCSC{{{h}}}')
    except:
        print('Nope!')


def get_c(n: int) -> int:
    return n**2 * 485 * 487 * 7 * 23


def get_b(a: int) -> int:
    return 159 * a // 485


def get_a(c: int) -> int:
    return 487 * c


def pell(n: int) -> tuple[int, int]:
    if n <= 0:
        raise ValueError('n must be a positive integer')
    sqrt_n_int = int(n**0.5)
    if sqrt_n_int * sqrt_n_int == n:
        raise ValueError("n cannot be a perfect square for Pell's equation x^2 - n*y^2 = 1")

    a0 = sqrt_n_int
    m = 0
    d = 1
    a = a0

    p_prev, q_prev = 1, 0
    p_curr, q_curr = a0, 1

    while True:
        m = d * a - m
        d = (n - m**2) // d
        if d == 0:
            raise ValueError('Division by zero encountered in Pell solver.')
        a = (a0 + m) // d

        p_next = a * p_curr + p_prev
        q_next = a * q_curr + q_prev

        if p_next**2 - n * q_next**2 == 1:
            return p_next, q_next

        p_prev, p_curr = p_curr, p_next
        q_prev, q_curr = q_curr, q_next


def main() -> None:
    d, n = pell(24 * 159 * 487**2 * 7 * 23)
    print(f'd = {d}, n = {n}')
    c = get_c(n)
    a = get_a(c)
    b = get_b(a)
    x = math.isqrt(a + b)
    if ((1 + d) % 6) == 0:
        y = (1 + d) // 6
    else:
        y = (1 - d) // 6
    print(f'a = {a}, b = {b}, c = {c}, x = {x}, y = {y}')
    flag(a, b, c, x, y)


if __name__ == '__main__':
    main()
```
