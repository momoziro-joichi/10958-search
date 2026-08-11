from fractions import Fraction
from functools import lru_cache

DIGITS = "12345"


# ============================================================
# Exact integer nth root
# ============================================================

def integer_nth_root(n, exponent):
    """
    Return x if x^exponent == n.
    Otherwise return None.

    n must be a non-negative integer.
    """

    if n < 0:
        return None

    if exponent <= 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

    # Binary search
    low = 0
    high = n

    while low <= high:

        mid = (low + high) // 2
        value = mid ** exponent

        if value == n:
            return mid

        if value < n:
            low = mid + 1

        else:
            high = mid - 1

    return None


# ============================================================
# Exact rational nth root
# ============================================================

def rational_nth_root(value, exponent):
    """
    Return the exact rational x satisfying

        x^exponent = value

    if such a rational x exists.

    Otherwise return None.

    Examples:

        rational_nth_root(Fraction(243, 1024), 5)
        -> Fraction(3, 4)

        rational_nth_root(Fraction(2), 2)
        -> None
    """

    if exponent <= 0:
        return None

    numerator = value.numerator
    denominator = value.denominator

    # --------------------------------------------------------
    # Positive / zero
    # --------------------------------------------------------

    if numerator >= 0:

        root_num = integer_nth_root(
            numerator,
            exponent
        )

        root_den = integer_nth_root(
            denominator,
            exponent
        )

        if root_num is None or root_den is None:
            return None

        return Fraction(root_num, root_den)

    # --------------------------------------------------------
    # Negative value
    #
    # Even root of a negative number is not rational.
    # Odd root can be negative.
    # --------------------------------------------------------

    if exponent % 2 == 0:
        return None

    root_num = integer_nth_root(
        -numerator,
        exponent
    )

    root_den = integer_nth_root(
        denominator,
        exponent
    )

    if root_num is None or root_den is None:
        return None

    return Fraction(
        -root_num,
        root_den
    )


# ============================================================
# ① Full DP
# ============================================================

@lru_cache(maxsize=None)
def generate_values(i, j):

    result = {}

    # Concatenation
    result[Fraction(int(DIGITS[i:j]))] = DIGITS[i:j]

    # Split
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

                # ^
                if (
                    b.denominator == 1
                    and 0 <= b.numerator <= 10
                    and not (a == 0 and b == 0)
                ):

                    exponent = b.numerator

                    value = a ** exponent

                    if value not in result:
                        result[value] = (
                            f"({expr_a}^{expr_b})"
                        )

    return result


# ============================================================
# ② Reverse search
# ============================================================

@lru_cache(maxsize=None)
def can_make(i, j, target):
    """
    Can DIGITS[i:j] make target?

    Returns an expression or None.
    """

    # --------------------------------------------------------
    # Concatenation
    # --------------------------------------------------------

    if Fraction(int(DIGITS[i:j])) == target:
        return DIGITS[i:j]

    # Single digit
    if j - i == 1:
        return None

    # --------------------------------------------------------
    # Every possible top-level split
    # --------------------------------------------------------

    for k in range(i + 1, j):

        # ====================================================
        # LEFT SIDE VALUES
        # ====================================================

        left_values = generate_values(i, k)

        for a, expr_a in left_values.items():

            # ------------------------------------------------
            # Addition
            #
            # A + B = target
            # B = target - A
            # ------------------------------------------------

            b = target - a

            expr_b = can_make(
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

            b = a - target

            expr_b = can_make(
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
            #
            # A * B = target
            # B = target / A
            # ------------------------------------------------

            if a != 0:

                b = target / a

                expr_b = can_make(
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

                b = a / target

                if b != 0:

                    expr_b = can_make(
                        k,
                        j,
                        b
                    )

                    if expr_b is not None:

                        return (
                            f"({expr_a}/{expr_b})"
                        )

            # ------------------------------------------------
            # Exponentiation
            #
            # A^B = target
            #
            # We know B must be an integer in this stage.
            #
            # Instead of guessing A from -100..100,
            # calculate the exact rational root.
            # ------------------------------------------------

            for exponent in range(0, 11):

                # A^0 = 1
                if exponent == 0:

                    if target != 1:
                        continue

                    base = Fraction(1)

                else:

                    base = rational_nth_root(
                        target,
                        exponent
                    )

                    if base is None:
                        continue

                # Can the LEFT interval make the base?
                expr_base = can_make(
                    i,
                    k,
                    base
                )

                if expr_base is None:
                    continue

                # Can the RIGHT interval make the exponent?
                expr_exponent = can_make(
                    k,
                    j,
                    Fraction(exponent)
                )

                if expr_exponent is not None:

                    return (
                        f"({expr_base}^{expr_exponent})"
                    )

    return None


# ============================================================
# ③ Validation
# ============================================================

def main():

    print("# STAGE 9 - SMALL VALIDATION")
    print()

    print("Digits:", DIGITS)
    print()

    # Full DP
    all_values = generate_values(
        0,
        len(DIGITS)
    )

    print(
        "Number of values from full DP:",
        len(all_values)
    )

    print()
    print("Checking reverse search...")
    print()

    failures = []

    for value in all_values:

        expression = can_make(
            0,
            len(DIGITS),
            value
        )

        if expression is None:

            failures.append(value)

            print(
                "FAILED:",
                value
            )

            if len(failures) >= 20:
                break

    print()
    print("========================================")

    if not failures:

        print("VALIDATION SUCCESS!")
        print()
        print(
            "The full DP and reverse search "
            "agree for DIGITS =",
            DIGITS
        )

    else:

        print("VALIDATION FAILED.")
        print(
            "Number of failures:",
            len(failures)
        )

    print()
    print("10958 search:")
    print("NOT RUN YET")


if __name__ == "__main__":
    main()
