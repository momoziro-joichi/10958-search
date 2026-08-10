"""
10958 Search - Stage 8

Digits:
    123456789

Allowed:
    concatenation
    +
    -
    *
    /
    ^

Stage 8 improvements:
    - Cache generated values for every interval.
    - Cache failed (interval, target) searches.
    - Use exact Fraction arithmetic.
    - Prune impossible integer powers of 10958.
    - Avoid repeatedly generating the same interval.
    - Print progress.

This is NOT yet a complete proof of impossibility.
"""

from fractions import Fraction
from functools import lru_cache
import math


# ============================================================
# Configuration
# ============================================================

STAGE = 8

DIGITS = "123456789"
TARGET = Fraction(10958)

MAX_INTEGER_EXPONENT = 20

REPORT_INTERVAL = 10000


# ============================================================
# Counters
# ============================================================

search_calls = 0
generated_intervals = 0
cached_failures = 0


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
    """

    if k <= 0:
        return None

    if n < 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

    # For large numbers, binary search.
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
    Determine whether a rational value has an exact
    rational exponent-th root.

    Example:
        16^(1/2) is handled indirectly through
        exact_root(16, 2) -> 4

    Returns Fraction or None.
    """

    if exponent <= 0:
        return None

    p = value.numerator
    q = value.denominator

    # Positive / zero.
    if p >= 0:

        rp = integer_nth_root(p, exponent)
        rq = integer_nth_root(q, exponent)

        if rp is None or rq is None:
            return None

        return Fraction(rp, rq)

    # Negative values require odd roots.
    if exponent % 2 == 0:
        return None

    rp = integer_nth_root(-p, exponent)
    rq = integer_nth_root(q, exponent)

    if rp is None or rq is None:
        return None

    return Fraction(-rp, rq)


# ============================================================
# Exact power
# ============================================================

def exact_power(base, exponent):
    """
    Exact rational integer power.

    base is Fraction.
    exponent is non-negative integer.
    """

    if exponent < 0:
        return None

    if base == 0 and exponent == 0:
        return None

    if exponent == 0:
        return Fraction(1)

    return Fraction(
        base.numerator ** exponent,
        base.denominator ** exponent
    )


# ============================================================
# Generate all values for ONE interval
# ============================================================

@lru_cache(maxsize=None)
def generate_values(i, j):
    """
    Return:

        {
            Fraction value: expression
        }

    for DIGITS[i:j].

    IMPORTANT:
    This function is cached, so each interval is generated
    only once.
    """

    global generated_intervals

    generated_intervals += 1

    result = {}

    # --------------------------------------------------------
    # Concatenation
    # --------------------------------------------------------

    result[concat_value(i, j)] = DIGITS[i:j]

    # One digit.
    if j - i == 1:
        return result

    # --------------------------------------------------------
    # Split interval
    # --------------------------------------------------------

    for k in range(i + 1, j):

        left = generate_values(i, k)
        right = generate_values(k, j)

        for a, expr_a in left.items():

            for b, expr_b in right.items():

                # + ------------------------------------------------

                value = a + b

                if value not in result:
                    result[value] = (
                        f"({expr_a}+{expr_b})"
                    )

                # - ------------------------------------------------

                value = a - b

                if value not in result:
                    result[value] = (
                        f"({expr_a}-{expr_b})"
                    )

                # * ------------------------------------------------

                value = a * b

                if value not in result:
                    result[value] = (
                        f"({expr_a}*{expr_b})"
                    )

                # / ------------------------------------------------

                if b != 0:

                    value = a / b

                    if value not in result:
                        result[value] = (
                            f"({expr_a}/{expr_b})"
                        )

                # ^ ------------------------------------------------
                #
                # Only integer exponents in Stage 8.
                #

                if (
                    is_integer(b)
                    and b >= 0
                    and b <= MAX_INTEGER_EXPONENT
                ):

                    exponent = b.numerator

                    value = exact_power(
                        a,
                        exponent
                    )

                    if value is not None:

                        if value not in result:
                            result[value] = (
                                f"({expr_a}^{expr_b})"
                            )

    return result


# ============================================================
# Mathematical pruning for TARGET
# ============================================================

def impossible_integer_power(target):
    """
    Return True if target cannot be A^B where
    A and B are integers and B >= 1.

    This is especially useful for 10958.
    """

    if not is_integer(target):
        return False

    n = target.numerator

    if n == 0:
        return False

    if n == 1:
        return False

    # Negative target:
    # an odd exponent could potentially work.
    if n < 0:
        return False

    # If n is not a perfect power, no non-trivial
    # integer exponentiation can produce it.
    for exponent in range(2, MAX_INTEGER_EXPONENT + 1):

        root = integer_nth_root(
            n,
            exponent
        )

        if root is not None:
            return False

    return True


# ============================================================
# Target-directed search
# ============================================================

failed_targets = set()


def search_target(i, j, target):
    """
    Determine whether DIGITS[i:j] can produce target.

    Returns an expression or None.
    """

    global search_calls
    global cached_failures

    search_calls += 1

    if search_calls % REPORT_INTERVAL == 0:

        print(
            f"Search calls: {search_calls:,} | "
            f"Failed cache: {len(failed_targets):,} | "
            f"Generated intervals: {generated_intervals:,}"
        )

    # --------------------------------------------------------
    # Failed-state cache
    # --------------------------------------------------------

    key = (i, j, target)

    if key in failed_targets:

        cached_failures += 1
        return None

    # --------------------------------------------------------
    # Direct concatenation
    # --------------------------------------------------------

    if concat_value(i, j) == target:

        return DIGITS[i:j]

    # Single digit.
    if j - i == 1:

        failed_targets.add(key)
        return None

    # --------------------------------------------------------
    # Mathematical pruning:
    # If target itself is not an integer perfect power,
    # top-level integer exponentiation is impossible.
    # This does NOT rule out exponentiation occurring
    # deeper inside the expression.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Try every top-level split.
    # --------------------------------------------------------

    for k in range(i + 1, j):

        left_len = k - i
        right_len = j - k

        # ====================================================
        # Case A:
        # Generate LEFT, solve RIGHT.
        # ====================================================

        if left_len <= right_len:

            left_values = generate_values(i, k)

            # ------------------------------------------------
            # Addition
            # ------------------------------------------------

            for a, expr_a in left_values.items():

                b = target - a

                expr_b = search_target(
                    k,
                    j,
                    b
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}+{expr_b})"
                    )

            # ------------------------------------------------
            # Subtraction
            #
            # A - B = target
            # B = A - target
            # ------------------------------------------------

            for a, expr_a in left_values.items():

                b = a - target

                expr_b = search_target(
                    k,
                    j,
                    b
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}-{expr_b})"
                    )

            # ------------------------------------------------
            # Multiplication
            # ------------------------------------------------

            for a, expr_a in left_values.items():

                if a == 0:
                    continue

                b = target / a

                expr_b = search_target(
                    k,
                    j,
                    b
                )

                if expr_b is not None:

                    return (
                        f"({expr_a}*{expr_b})"
                    )

            # ------------------------------------------------
            # Division
            #
            # A / B = target
            # B = A / target
            # ------------------------------------------------

            if target != 0:

                for a, expr_a in left_values.items():

                    b = a / target

                    if b == 0:
                        continue

                    expr_b = search_target(
                        k,
                        j,
                        b
                    )

                    if expr_b is not None:

                        return (
                            f"({expr_a}/{expr_b})"
                        )

        # ====================================================
        # Case B:
        # Generate RIGHT, solve LEFT.
        # ====================================================

        else:

            right_values = generate_values(k, j)

            # ------------------------------------------------
            # Addition
            # ------------------------------------------------

            for b, expr_b in right_values.items():

                a = target - b

                expr_a = search_target(
                    i,
                    k,
                    a
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}+{expr_b})"
                    )

            # ------------------------------------------------
            # Subtraction
            #
            # A - B = target
            # A = target + B
            # ------------------------------------------------

            for b, expr_b in right_values.items():

                a = target + b

                expr_a = search_target(
                    i,
                    k,
                    a
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}-{expr_b})"
                    )

            # ------------------------------------------------
            # Multiplication
            # ------------------------------------------------

            for b, expr_b in right_values.items():

                if b == 0:
                    continue

                a = target / b

                expr_a = search_target(
                    i,
                    k,
                    a
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}*{expr_b})"
                    )

            # ------------------------------------------------
            # Division
            #
            # A / B = target
            # A = target * B
            # ------------------------------------------------

            for b, expr_b in right_values.items():

                if b == 0:
                    continue

                a = target * b

                expr_a = search_target(
                    i,
                    k,
                    a
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}/{expr_b})"
                    )

        # ====================================================
        # Exponentiation
        # ====================================================
        #
        # Stage 8:
        # only INTEGER exponents.
        #
        # Instead of blindly generating A^B,
        # ask:
        #
        #     A^B = target
        #
        # Can target have an exact B-th root?
        #
        # ====================================================

        if not impossible_integer_power(target):

            for exponent in range(
                1,
                MAX_INTEGER_EXPONENT + 1
            ):

                base = exact_root(
                    target,
                    exponent
                )

                if base is None:
                    continue

                expr_left = search_target(
                    i,
                    k,
                    base
                )

                if expr_left is None:
                    continue

                expr_right = search_target(
                    k,
                    j,
                    Fraction(exponent)
                )

                if expr_right is not None:

                    return (
                        f"({expr_left}^{expr_right})"
                    )

    # --------------------------------------------------------
    # Nothing worked.
    # --------------------------------------------------------

    failed_targets.add(key)

    return None


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print(f"10958 SEARCH - STAGE {STAGE}")
    print("========================================")

    print(
        f"Digits : {DIGITS}"
    )

    print(
        f"Target : {TARGET}"
    )

    print()

    print(
        "Method:"
    )

    print(
        "  Cached interval generation"
    )

    print(
        "  Target-directed search"
    )

    print(
        "  Failed-state cache"
    )

    print(
        "  Exact Fraction arithmetic"
    )

    print(
        "  Integer exponentiation"
    )

    print()

    print(
        "Starting Stage 8..."
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

        print()
        print("FOUND!")
        print()
        print(
            f"Expression: {result}"
        )
        print(
            f"Target: {TARGET}"
        )

    else:

        print()
        print(
            "10958 was not found."
        )

    print()

    print("STATISTICS")
    print("----------------------------------------")

    print(
        f"Search calls      : {search_calls:,}"
    )

    print(
        f"Failed states     : {len(failed_targets):,}"
    )

    print(
        f"Cached hits       : {cached_failures:,}"
    )

    print(
        f"Generated intervals: {generated_intervals:,}"
    )

    print()

    print("SEARCH CLASS")
    print("----------------------------------------")

    print(
        "123456789 fixed order"
    )

    print(
        "Concatenation"
    )

    print(
        "+ - * /"
    )

    print(
        "Integer exponentiation"
    )

    print(
        "Exact rational arithmetic"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "This is NOT yet a complete impossibility proof."
    )

    print(
        "Rational/irrational algebraic-number cancellation"
        " is not yet included."
    )


if __name__ == "__main__":
    main()
