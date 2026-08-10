"""
10958 Search - Stage 7

Target-directed search without a giant global DP table.

Digits:
    123456789

Allowed:
    concatenation
    +
    -
    *
    /
    ^

All arithmetic is exact using Fraction.

This version deliberately avoids storing millions
of interval/value states in memory.

The search is target-directed:
    1. Choose the top-level split.
    2. Generate one side.
    3. Derive the exact value required from the other side.
    4. Recursively test only that required value.

Exponentiation is handled using exact integer/rational roots.
"""

from fractions import Fraction
import math


DIGITS = "123456789"
TARGET = Fraction(10958)

# For the first exponentiation stage.
# This is NOT the final completeness bound.
MAX_EXPONENT = 20

# Progress reporting.
NODE_REPORT_INTERVAL = 10000

nodes = 0


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
    Otherwise return None.

    n >= 0
    k >= 1
    """

    if k <= 0 or n < 0:
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
    Determine whether value has an exact rational
    exponent-th root.

    Returns Fraction if it exists.
    Otherwise None.
    """

    if exponent <= 0:
        return None

    p = value.numerator
    q = value.denominator

    # Positive or zero.
    if p >= 0:

        rp = integer_nth_root(p, exponent)
        rq = integer_nth_root(q, exponent)

        if rp is None or rq is None:
            return None

        return Fraction(rp, rq)

    # Negative result requires odd exponent.
    if exponent % 2 == 0:
        return None

    rp = integer_nth_root(-p, exponent)
    rq = integer_nth_root(q, exponent)

    if rp is None or rq is None:
        return None

    return Fraction(-rp, rq)


# ============================================================
# Expression generation for a SMALL side
# ============================================================

def generate_values(i, j):
    """
    Generate all distinct exact values for DIGITS[i:j].

    This is intentionally used only on the selected
    smaller side of a split.

    Returns:
        dict[Fraction, expression]
    """

    result = {}

    # Concatenation.
    value = concat_value(i, j)
    result[value] = DIGITS[i:j]

    # Single digit.
    if j - i == 1:
        return result

    # Split recursively.
    for k in range(i + 1, j):

        left = generate_values(i, k)
        right = generate_values(k, j)

        for a, expr_a in left.items():

            for b, expr_b in right.items():

                # +
                value = a + b

                if value not in result:
                    result[value] = (
                        f"({expr_a}+{expr_b})"
                    )

                # -
                value = a - b

                if value not in result:
                    result[value] = (
                        f"({expr_a}-{expr_b})"
                    )

                # *
                value = a * b

                if value not in result:
                    result[value] = (
                        f"({expr_a}*{expr_b})"
                    )

                # /
                if b != 0:

                    value = a / b

                    if value not in result:
                        result[value] = (
                            f"({expr_a}/{expr_b})"
                        )

                # Integer exponentiation.
                if (
                    is_integer(a)
                    and is_integer(b)
                    and b.numerator >= 0
                ):

                    exponent = b.numerator

                    # Avoid absurd powers during this stage.
                    if exponent <= MAX_EXPONENT:

                        if not (
                            a == 0
                            and exponent == 0
                        ):

                            value = Fraction(
                                a.numerator ** exponent,
                                1
                            )

                            if value not in result:
                                result[value] = (
                                    f"({expr_a}^{expr_b})"
                                )

    return result


# ============================================================
# Target-directed search
# ============================================================

def search_target(i, j, target, depth=0):
    """
    Can DIGITS[i:j] produce target?

    No giant global memoization is used.
    """

    global nodes

    nodes += 1

    if nodes % NODE_REPORT_INTERVAL == 0:

        print(
            f"Visited states: {nodes:,}"
        )

    # --------------------------------------------------------
    # Direct concatenation
    # --------------------------------------------------------

    if concat_value(i, j) == target:
        return DIGITS[i:j]

    # One digit cannot be split.
    if j - i == 1:
        return None

    # --------------------------------------------------------
    # Try every top-level split.
    # --------------------------------------------------------

    for k in range(i + 1, j):

        left_len = k - i
        right_len = j - k

        # ----------------------------------------------------
        # Generate the smaller side.
        #
        # We do not build both complete sides.
        # ----------------------------------------------------

        if left_len <= right_len:

            generated = generate_values(i, k)

            # =================================================
            # +
            # A + B = target
            # B = target - A
            # =================================================

            for a, expr_a in generated.items():

                b = target - a

                expr_b = search_target(
                    k,
                    j,
                    b,
                    depth + 1
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}+{expr_b})"
                    )

            # =================================================
            # -
            # A - B = target
            # B = A - target
            # =================================================

            for a, expr_a in generated.items():

                b = a - target

                expr_b = search_target(
                    k,
                    j,
                    b,
                    depth + 1
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}-{expr_b})"
                    )

            # =================================================
            # *
            # A * B = target
            # B = target / A
            # =================================================

            for a, expr_a in generated.items():

                if a == 0:
                    continue

                b = target / a

                expr_b = search_target(
                    k,
                    j,
                    b,
                    depth + 1
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}*{expr_b})"
                    )

            # =================================================
            # /
            # A / B = target
            # B = A / target
            # =================================================

            if target != 0:

                for a, expr_a in generated.items():

                    b = a / target

                    if b == 0:
                        continue

                    expr_b = search_target(
                        k,
                        j,
                        b,
                        depth + 1
                    )

                    if expr_b is not None:

                        return (
                            f"({expr_a}/{expr_b})"
                        )

            # =================================================
            # ^
            # A^B = target
            # =================================================

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

                expr_a = search_target(
                    i,
                    k,
                    base,
                    depth + 1
                )

                if expr_a is None:
                    continue

                expr_b = search_target(
                    k,
                    j,
                    Fraction(exponent),
                    depth + 1
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}^{expr_b})"
                    )

        # ----------------------------------------------------
        # Generate RIGHT side instead.
        # ----------------------------------------------------

        else:

            generated = generate_values(k, j)

            # =================================================
            # +
            # A + B = target
            # A = target - B
            # =================================================

            for b, expr_b in generated.items():

                a = target - b

                expr_a = search_target(
                    i,
                    k,
                    a,
                    depth + 1
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}+{expr_b})"
                    )

            # =================================================
            # -
            # A - B = target
            # A = target + B
            # =================================================

            for b, expr_b in generated.items():

                a = target + b

                expr_a = search_target(
                    i,
                    k,
                    a,
                    depth + 1
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}-{expr_b})"
                    )

            # =================================================
            # *
            # A * B = target
            # A = target / B
            # =================================================

            for b, expr_b in generated.items():

                if b == 0:
                    continue

                a = target / b

                expr_a = search_target(
                    i,
                    k,
                    a,
                    depth + 1
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}*{expr_b})"
                    )

            # =================================================
            # /
            # A / B = target
            # A = target * B
            # =================================================

            for b, expr_b in generated.items():

                if b == 0:
                    continue

                a = target * b

                expr_a = search_target(
                    i,
                    k,
                    a,
                    depth + 1
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}/{expr_b})"
                    )

            # =================================================
            # ^
            # A^B = target
            # =================================================

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

                expr_a = search_target(
                    i,
                    k,
                    base,
                    depth + 1
                )

                if expr_a is None:
                    continue

                expr_b = search_target(
                    k,
                    j,
                    Fraction(exponent),
                    depth + 1
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}^{expr_b})"
                    )

    return None


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print("10958 SEARCH - STAGE 7")
    print("========================================")

    print(
        f"Digits : {DIGITS}"
    )

    print(
        f"Target : {TARGET}"
    )

    print()

    print(
        "Generating smaller sides only..."
    )

    print(
        "Starting search..."
    )

    print()

    result = search_target(
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
        "  123456789 in fixed order"
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
        "NOTE:"
    )

    print(
        "Exponent search is currently limited "
        f"to 1..{MAX_EXPONENT}."
    )

    print(
        "This is not yet an impossibility proof."
    )


if __name__ == "__main__":
    main()
