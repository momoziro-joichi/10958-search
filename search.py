"""
10958 Target-Directed Search

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

This version uses target-directed recursive search.

Stage 4:
    Instead of generating every possible final value,
    start from 10958 and work backwards.

Arithmetic is exact using Fraction.

Exponentiation:
    integer base
    integer exponent
    exponent >= 0
    0^0 is excluded

Important:
    This is an optimization/search stage.
    It is NOT yet a mathematical impossibility proof.
"""

from fractions import Fraction
from functools import lru_cache
import math


DIGITS = "123456789"
TARGET = Fraction(10958)

# Prevent enormous integer powers.
MAX_POWER_DIGITS = 100


# ============================================================
# Utilities
# ============================================================

def is_integer(x):
    return x.denominator == 1


def integer_root_exact(n, k):
    """
    Return x such that x^k = n, if an integer x exists.
    Otherwise return None.

    Handles n >= 0 and k >= 1.
    """

    if k <= 0:
        return None

    if n < 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

    # Initial approximation
    lo = 0
    hi = 1

    while hi ** k < n:
        hi *= 2

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


def exact_rational_root(value, exponent):
    """
    Find integer x such that:

        x^exponent = value

    where value is a Fraction and exponent > 0.

    Return x as Fraction if it exists.
    Otherwise return None.
    """

    if exponent <= 0:
        return None

    numerator = value.numerator
    denominator = value.denominator

    # Positive numerator
    if numerator >= 0:

        root_num = integer_root_exact(
            numerator,
            exponent
        )

        root_den = integer_root_exact(
            denominator,
            exponent
        )

        if root_num is None or root_den is None:
            return None

        return Fraction(root_num, root_den)

    # Negative numerator
    #
    # An even power cannot produce a negative value.
    if exponent % 2 == 0:
        return None

    root_num = integer_root_exact(
        -numerator,
        exponent
    )

    root_den = integer_root_exact(
        denominator,
        exponent
    )

    if root_num is None or root_den is None:
        return None

    return Fraction(-root_num, root_den)


def safe_power(a, b):
    """
    Exact integer-base / integer-exponent power.

    Returns Fraction or None.
    """

    if not is_integer(a):
        return None

    if not is_integer(b):
        return None

    base = a.numerator
    exponent = b.numerator

    if exponent < 0:
        return None

    if base == 0 and exponent == 0:
        return None

    if base == 0:
        return Fraction(0)

    if abs(base) == 1:
        return Fraction(base ** exponent)

    # Estimate number of decimal digits before computing.
    estimated_digits = (
        int(exponent * math.log10(abs(base))) + 1
    )

    if estimated_digits > MAX_POWER_DIGITS:
        return None

    return Fraction(base ** exponent)


# ============================================================
# Directly constructible values
# ============================================================

@lru_cache(maxsize=None)
def concatenated_value(i, j):
    """
    DIGITS[i:j] as one integer.
    """

    return Fraction(int(DIGITS[i:j]))


# ============================================================
# Main target-directed search
# ============================================================

@lru_cache(maxsize=None)
def search(i, j, target):
    """
    Can DIGITS[i:j] produce target?

    Returns an expression if found.
    Otherwise None.
    """

    # --------------------------------------------------------
    # Direct concatenation
    # --------------------------------------------------------

    if target == concatenated_value(i, j):
        return DIGITS[i:j]

    # --------------------------------------------------------
    # Split interval
    # --------------------------------------------------------

    for k in range(i + 1, j):

        # ----------------------------------------------------
        # LEFT + RIGHT
        #
        # A + B = target
        #
        # B = target - A
        # ----------------------------------------------------

        # Enumerate possible left expressions.
        left_values = generate_values(i, k)

        for a, expr_a in left_values.items():

            b = target - a

            expr_b = search(k, j, b)

            if expr_b is not None:
                return f"({expr_a}+{expr_b})"

        # ----------------------------------------------------
        # LEFT - RIGHT
        #
        # A - B = target
        #
        # B = A - target
        # ----------------------------------------------------

        for a, expr_a in left_values.items():

            b = a - target

            expr_b = search(k, j, b)

            if expr_b is not None:
                return f"({expr_a}-{expr_b})"

        # ----------------------------------------------------
        # LEFT * RIGHT
        #
        # A * B = target
        #
        # B = target / A
        # ----------------------------------------------------

        for a, expr_a in left_values.items():

            if a == 0:
                continue

            b = target / a

            expr_b = search(k, j, b)

            if expr_b is not None:
                return f"({expr_a}*{expr_b})"

        # ----------------------------------------------------
        # LEFT / RIGHT
        #
        # A / B = target
        #
        # B = A / target
        # ----------------------------------------------------

        if target != 0:

            for a, expr_a in left_values.items():

                b = a / target

                if b == 0:
                    continue

                expr_b = search(k, j, b)

                if expr_b is not None:
                    return f"({expr_a}/{expr_b})"

        # ----------------------------------------------------
        # POWER
        #
        # A^B = target
        #
        # We enumerate possible integer exponents B
        # from the right interval.
        #
        # Then derive A exactly using integer roots.
        # ----------------------------------------------------

        right_values = generate_values(k, j)

        for b, expr_b in right_values.items():

            if not is_integer(b):
                continue

            exponent = b.numerator

            if exponent <= 0:
                continue

            a = exact_rational_root(
                target,
                exponent
            )

            if a is None:
                continue

            expr_a = search(i, k, a)

            if expr_a is not None:
                return f"({expr_a}^{expr_b})"

    return None


# ============================================================
# Forward generation for a SMALL interval
# ============================================================

@lru_cache(maxsize=None)
def generate_values(i, j):
    """
    Generate all exact rational values for a subinterval.

    This is intentionally used only for the smaller
    subproblems encountered by the target-directed search.

    Returns:
        Fraction -> expression
    """

    values = {}

    # Concatenation
    values[concatenated_value(i, j)] = DIGITS[i:j]

    # Split
    for k in range(i + 1, j):

        left = generate_values(i, k)
        right = generate_values(k, j)

        for a, expr_a in left.items():

            for b, expr_b in right.items():

                # +
                value = a + b

                if value not in values:
                    values[value] = (
                        f"({expr_a}+{expr_b})"
                    )

                # -
                value = a - b

                if value not in values:
                    values[value] = (
                        f"({expr_a}-{expr_b})"
                    )

                # *
                value = a * b

                if value not in values:
                    values[value] = (
                        f"({expr_a}*{expr_b})"
                    )

                # /
                if b != 0:

                    value = a / b

                    if value not in values:
                        values[value] = (
                            f"({expr_a}/{expr_b})"
                        )

                # ^
                power = safe_power(a, b)

                if power is not None:

                    if power not in values:
                        values[power] = (
                            f"({expr_a}^{expr_b})"
                        )

    return values


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print("10958 TARGET-DIRECTED SEARCH")
    print("========================================")

    print(f"Digits : {DIGITS}")
    print(f"Target : {TARGET}")
    print()

    print("Starting reverse search...")
    print()

    expression = search(
        0,
        len(DIGITS),
        TARGET
    )

    print()
    print("========================================")
    print("RESULT")
    print("========================================")

    if expression is not None:

        print("FOUND!")
        print()
        print(f"Expression: {expression}")
        print(f"Target    : {TARGET}")

    else:

        print("10958 was not found.")

    print()
    print("Search type:")
    print("  Target-directed recursive search")
    print("  Exact Fraction arithmetic")
    print("  Concatenation")
    print("  + - * /")
    print("  Integer exponentiation")

    print()
    print("IMPORTANT:")
    print("This result is not yet an impossibility proof.")


if __name__ == "__main__":
    main()
