"""
10958 Search - Stage 6

Target-directed structural search.

Digits:
    123456789

Allowed:
    concatenation
    +
    -
    *
    /
    ^
    parentheses

Important:
This version avoids constructing the full value set
for the complete 9-digit expression.

It recursively asks:

    Can interval [i:j] produce target?

Arithmetic is exact using Fraction.
"""

from fractions import Fraction
from functools import lru_cache
import math


DIGITS = "123456789"
TARGET = Fraction(10958)

# Maximum number of exponent candidates to inspect.
MAX_EXPONENT = 20


# ============================================================
# Basic utilities
# ============================================================

def concat_value(i, j):
    return Fraction(int(DIGITS[i:j]))


def is_integer(x):
    return x.denominator == 1


# ============================================================
# Exact integer root
# ============================================================

def integer_nth_root(n, k):
    """
    Return x if x^k == n.
    Otherwise None.
    """

    if k <= 0:
        return None

    if n < 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

    # Binary search.
    lo = 1
    hi = n

    while lo <= hi:

        mid = (lo + hi) // 2
        value = mid ** k

        if value == n:
            return mid

        if value < n:
            lo = mid + 1
        else:
            hi = mid - 1

    return None


def exact_root(value, exponent):
    """
    Check whether value has a rational
    exponent-th root.
    """

    if exponent <= 0:
        return None

    p = value.numerator
    q = value.denominator

    # Positive
    if p >= 0:

        rp = integer_nth_root(p, exponent)
        rq = integer_nth_root(q, exponent)

        if rp is None or rq is None:
            return None

        return Fraction(rp, rq)

    # Negative values require odd exponent.
    if exponent % 2 == 0:
        return None

    rp = integer_nth_root(-p, exponent)
    rq = integer_nth_root(q, exponent)

    if rp is None or rq is None:
        return None

    return Fraction(-rp, rq)


# ============================================================
# Factor candidates
# ============================================================

def integer_divisors(n):
    """
    Return positive divisors of |n|.
    """

    n = abs(n)

    if n == 0:
        return []

    divisors = set()

    limit = math.isqrt(n)

    for d in range(1, limit + 1):

        if n % d == 0:

            divisors.add(d)
            divisors.add(n // d)

    return sorted(divisors)


# ============================================================
# Search
# ============================================================

visited = set()
nodes = 0


@lru_cache(maxsize=None)
def can_make(i, j, target):

    global nodes

    nodes += 1

    # Progress indicator.
    if nodes % 10000 == 0:

        print(
            f"Visited states: {nodes:,}"
        )

    state = (i, j, target)

    if state in visited:
        return None

    visited.add(state)

    # --------------------------------------------------------
    # Direct concatenation
    # --------------------------------------------------------

    if concat_value(i, j) == target:

        return DIGITS[i:j]

    # A single digit has no further split.
    if j - i == 1:

        return None

    # --------------------------------------------------------
    # Every possible top-level split
    # --------------------------------------------------------

    for k in range(i + 1, j):

        print(
            f"Checking interval "
            f"{i}:{k} | {k}:{j}"
            if nodes < 100
            else "",
            end=""
        )

        # ====================================================
        # Addition
        #
        # A + B = target
        #
        # We need one side and derive the other.
        # ====================================================

        # The smaller side can be concatenated directly,
        # which gives useful candidate values without
        # generating the complete universe.

        left_direct = concat_value(i, k)

        right_needed = target - left_direct

        expr_right = can_make(
            k,
            j,
            right_needed
        )

        if expr_right is not None:

            return (
                f"({DIGITS[i:k]}+"
                f"{expr_right})"
            )

        right_direct = concat_value(k, j)

        left_needed = target - right_direct

        expr_left = can_make(
            i,
            k,
            left_needed
        )

        if expr_left is not None:

            return (
                f"({expr_left}+"
                f"{DIGITS[k:j]})"
            )

        # ====================================================
        # Subtraction
        # ====================================================

        right_direct = concat_value(k, j)

        left_needed = target + right_direct

        expr_left = can_make(
            i,
            k,
            left_needed
        )

        if expr_left is not None:

            return (
                f"({expr_left}-"
                f"{DIGITS[k:j]})"
            )

        left_direct = concat_value(i, k)

        right_needed = left_direct - target

        expr_right = can_make(
            k,
            j,
            right_needed
        )

        if expr_right is not None:

            return (
                f"({DIGITS[i:k]}-"
                f"{expr_right})"
            )

        # ====================================================
        # Multiplication
        # ====================================================

        # Try direct concatenation on the left.
        if left_direct != 0:

            right_needed = target / left_direct

            expr_right = can_make(
                k,
                j,
                right_needed
            )

            if expr_right is not None:

                return (
                    f"({DIGITS[i:k]}*"
                    f"{expr_right})"
                )

        # Try direct concatenation on the right.
        if right_direct != 0:

            left_needed = target / right_direct

            expr_left = can_make(
                i,
                k,
                left_needed
            )

            if expr_left is not None:

                return (
                    f"({expr_left}*"
                    f"{DIGITS[k:j]})"
                )

        # ====================================================
        # Division
        # ====================================================

        # A / B = target
        #
        # A = target * B

        left_needed = target * right_direct

        expr_left = can_make(
            i,
            k,
            left_needed
        )

        if expr_left is not None and right_direct != 0:

            return (
                f"({expr_left}/"
                f"{DIGITS[k:j]})"
            )

        # B = A / target
        if target != 0:

            right_needed = left_direct / target

            if right_needed != 0:

                expr_right = can_make(
                    k,
                    j,
                    right_needed
                )

                if expr_right is not None:

                    return (
                        f"({DIGITS[i:k]}/"
                        f"{expr_right})"
                    )

        # ====================================================
        # Exponentiation
        # ====================================================

        # A^B = target
        #
        # Instead of generating arbitrary A and B,
        # try mathematically possible small integer exponents.
        # ====================================================

        for exponent in range(
            1,
            MAX_EXPONENT + 1
        ):

            base = exact_root(
                target,
                exponent
            )

            if base is None:
                continue

            expr_left = can_make(
                i,
                k,
                base
            )

            if expr_left is None:
                continue

            expr_right = can_make(
                k,
                j,
                Fraction(exponent)
            )

            if expr_right is not None:

                return (
                    f"({expr_left}^"
                    f"{expr_right})"
                )

    return None


# ============================================================
# Main
# ============================================================

def main():

    global nodes

    print("========================================")
    print("10958 STRUCTURAL TARGET SEARCH")
    print("========================================")

    print(
        f"Digits : {DIGITS}"
    )

    print(
        f"Target : {TARGET}"
    )

    print()

    print(
        "Starting structural search..."
    )

    print()

    result = can_make(
        0,
        len(DIGITS),
        TARGET
    )

    print()

    print("========================================")
    print("RESULT")
    print("========================================")

    if result is not None:

        print("FOUND!")
        print()
        print(
            f"Expression: {result}"
        )

        print(
            f"Value: {TARGET}"
        )

    else:

        print(
            "10958 was not found."
        )

    print()
    print(
        f"Visited states: {nodes:,}"
    )

    print()
    print(
        "Search class:"
    )

    print(
        "  Concatenation"
    )

    print(
        "  + - * /"
    )

    print(
        "  Integer exponentiation"
    )

    print(
        "  Exact Fraction arithmetic"
    )

    print()
    print(
        "This is not yet an impossibility proof."
    )


if __name__ == "__main__":
    main()
