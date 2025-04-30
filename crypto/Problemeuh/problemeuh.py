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
