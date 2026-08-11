from fractions import Fraction
from functools import lru_cache


# ============================================================
# Exact rational arithmetic
# ============================================================

def integer_nth_root_exact(n, exponent):
    """
    Return x if x^exponent == n.
    Otherwise return None.
    """

    if exponent <= 0:
        return None

    if n < 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

    lo = 0
    hi = n

    while lo <= hi:
        mid = (lo + hi) // 2
        value = mid ** exponent

        if value == n:
            return mid

        if value < n:
            lo = mid + 1
        else:
            hi = mid - 1

    return None


def rational_nth_root_exact(value, exponent):
    """
    Return x if x is rational and x^exponent == value.
    Otherwise return None.
    """

    if exponent <= 0:
        return None

    numerator = value.numerator
    denominator = value.denominator

    # Positive / zero
    if numerator >= 0:

        root_num = integer_nth_root_exact(
            numerator,
            exponent
        )

        root_den = integer_nth_root_exact(
            denominator,
            exponent
        )

        if root_num is None or root_den is None:
            return None

        return Fraction(root_num, root_den)

    # Negative value
    if exponent % 2 == 0:
        return None

    root_num = integer_nth_root_exact(
        -numerator,
        exponent
    )

    root_den = integer_nth_root_exact(
        denominator,
        exponent
    )

    if root_num is None or root_den is None:
        return None

    return Fraction(-root_num, root_den)


# ============================================================
# Full DP
# ============================================================

def make_solver(digits):
    """
    Create a solver for one fixed digit string.
    """

    n = len(digits)

    @lru_cache(maxsize=None)
    def full_dp(i, j):
        """
        All exact rational values obtainable from digits[i:j].
        """

        result = {}

        # Concatenation
        value = Fraction(int(digits[i:j]))
        result[value] = digits[i:j]

        # Every binary split
        for k in range(i + 1, j):

            left = full_dp(i, k)
            right = full_dp(k, j)

            for a, expr_a in left.items():
                for b, expr_b in right.items():

                    # Addition
                    value = a + b

                    if value not in result:
                        result[value] = (
                            f"({expr_a}+{expr_b})"
                        )

                    # Subtraction
                    value = a - b

                    if value not in result:
                        result[value] = (
                            f"({expr_a}-{expr_b})"
                        )

                    # Multiplication
                    value = a * b

                    if value not in result:
                        result[value] = (
                            f"({expr_a}*{expr_b})"
                        )

                    # Division
                    if b != 0:

                        value = a / b

                        if value not in result:
                            result[value] = (
                                f"({expr_a}/{expr_b})"
                            )

                    # Integer exponentiation
                    if (
                        b.denominator == 1
                        and 0 <= b.numerator <= 20
                        and not (a == 0 and b == 0)
                    ):

                        exponent = b.numerator
                        value = a ** exponent

                        if value not in result:
                            result[value] = (
                                f"({expr_a}^{expr_b})"
                            )

        return result

    # ========================================================
    # Target-directed search
    # ========================================================

    @lru_cache(maxsize=None)
    def can_make(i, j, target):
        """
        Can digits[i:j] produce target?

        Returns an expression or None.
        """

        # Concatenation
        if Fraction(int(digits[i:j])) == target:
            return digits[i:j]

        # One digit
        if j - i == 1:
            return None

        # Every possible top-level split
        for k in range(i + 1, j):

            left = full_dp(i, k)

            for a, expr_a in left.items():

                # ------------------------------------------------
                # A + B = T
                # B = T - A
                # ------------------------------------------------

                b = target - a

                expr_b = can_make(
                    k,
                    j,
                    b
                )

                if expr_b is not None:
                    return f"({expr_a}+{expr_b})"

                # ------------------------------------------------
                # A - B = T
                # B = A - T
                # ------------------------------------------------

                b = a - target

                expr_b = can_make(
                    k,
                    j,
                    b
                )

                if expr_b is not None:
                    return f"({expr_a}-{expr_b})"

                # ------------------------------------------------
                # A * B = T
                # B = T / A
                # ------------------------------------------------

                if a != 0:

                    b = target / a

                    expr_b = can_make(
                        k,
                        j,
                        b
                    )

                    if expr_b is not None:
                        return f"({expr_a}*{expr_b})"

                # ------------------------------------------------
                # A / B = T
                # B = A / T
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
                            return f"({expr_a}/{expr_b})"

                # ------------------------------------------------
                # A ^ B = T
                #
                # At this stage B is an integer because the
                # forward DP only permits integer exponents.
                #
                # Find exact rational roots instead of guessing
                # possible bases.
                # ------------------------------------------------

                for exponent in range(0, 21):

                    # A^0 = 1
                    if exponent == 0:

                        if target != 1:
                            continue

                        base = Fraction(1)

                    else:

                        base = rational_nth_root_exact(
                            target,
                            exponent
                        )

                        if base is None:
                            continue

                    expr_base = can_make(
                        i,
                        k,
                        base
                    )

                    if expr_base is None:
                        continue

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

    return full_dp, can_make


# ============================================================
# Validation
# ============================================================

def validate(digits):
    print()
    print("========================================")
    print("VALIDATION")
    print("Digits:", digits)
    print("========================================")

    full_dp, can_make = make_solver(digits)

    all_values = full_dp(
        0,
        len(digits)
    )

    print(
        "Full DP values:",
        len(all_values)
    )

    failures = []

    print("Checking reverse search...")

    for value in all_values:

        expression = can_make(
            0,
            len(digits),
            value
        )

        if expression is None:
            failures.append(value)

    print()

    if failures:

        print("VALIDATION FAILED")
        print("Failures:", len(failures))

        for value in failures[:20]:
            print("FAILED:", value)

        return False

    print("VALIDATION SUCCESS")
    print(
        "Full DP and target search agree for",
        digits
    )

    return True


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print("10958 SEARCH PROJECT")
    print("STAGE 9A - ALGORITHM VALIDATION")
    print("========================================")

    # Small → larger
    test_cases = [
        "123",
        "1234",
        "12345",
    ]

    for digits in test_cases:

        success = validate(digits)

        if not success:

            print()
            print("STOP.")
            print(
                "The algorithm must be fixed before "
                "moving to larger digit strings."
            )

            return

    print()
    print("========================================")
    print("ALL VALIDATION TESTS PASSED")
    print("========================================")

    print()
    print("10958 search: NOT RUN YET")
    print()
    print(
        "Next stage will optimize the target-directed "
        "search before attempting 123456789."
    )


if __name__ == "__main__":
    main()
