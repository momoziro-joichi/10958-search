from fractions import Fraction
from functools import lru_cache


# ============================================================
# Configuration
# ============================================================

DIGITS = "12345"


# ============================================================
# Exact integer nth root
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


# ============================================================
# Exact rational nth root
# ============================================================

def rational_nth_root_exact(value, exponent):
    """
    Find rational x satisfying

        x^exponent = value

    exactly.

    Return None if no rational solution exists.
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

    # Negative target
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

    return Fraction(
        -root_num,
        root_den
    )


# ============================================================
# Solver factory
# ============================================================

def make_solver(digits):

    n = len(digits)

    # ========================================================
    # FULL DP
    # ========================================================

    @lru_cache(maxsize=None)
    def full_dp(i, j):

        result = {}

        # Concatenation
        value = Fraction(int(digits[i:j]))

        result[value] = digits[i:j]

        # Every possible split
        for k in range(i + 1, j):

            left = full_dp(i, k)
            right = full_dp(k, j)

            for a, expr_a in left.items():

                for b, expr_b in right.items():

                    # ----------------------------------------
                    # +
                    # ----------------------------------------

                    value = a + b

                    result.setdefault(
                        value,
                        f"({expr_a}+{expr_b})"
                    )

                    # ----------------------------------------
                    # -
                    # ----------------------------------------

                    value = a - b

                    result.setdefault(
                        value,
                        f"({expr_a}-{expr_b})"
                    )

                    # ----------------------------------------
                    # *
                    # ----------------------------------------

                    value = a * b

                    result.setdefault(
                        value,
                        f"({expr_a}*{expr_b})"
                    )

                    # ----------------------------------------
                    # /
                    # ----------------------------------------

                    if b != 0:

                        value = a / b

                        result.setdefault(
                            value,
                            f"({expr_a}/{expr_b})"
                        )

                    # ----------------------------------------
                    # ^
                    #
                    # Forward rule:
                    # exponent must be an integer.
                    #
                    # No artificial upper limit here.
                    # ----------------------------------------

                    if (
                        b.denominator == 1
                        and not (a == 0 and b == 0)
                    ):

                        exponent = b.numerator

                        # Avoid enormous useless powers
                        # during validation.
                        #
                        # This is NOT a mathematical restriction
                        # of the target search; it only prevents
                        # pathological Python integer explosions.
                        if abs(exponent) <= 100:

                            value = a ** exponent

                            result.setdefault(
                                value,
                                f"({expr_a}^{expr_b})"
                            )

        return result

    # ========================================================
    # TARGET-DIRECTED SEARCH
    # ========================================================

    @lru_cache(maxsize=None)
    def can_make(i, j, target):

        # ----------------------------------------------------
        # Concatenation
        # ----------------------------------------------------

        if Fraction(int(digits[i:j])) == target:
            return digits[i:j]

        # Single digit
        if j - i == 1:
            return None

        # ----------------------------------------------------
        # Every possible split
        # ----------------------------------------------------

        for k in range(i + 1, j):

            left = full_dp(i, k)

            # =================================================
            # +, -, *, /
            # =================================================

            for a, expr_a in left.items():

                # A + B = T
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

                # A - B = T
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

                # A * B = T
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

                # A / B = T
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

            # =================================================
            # EXPONENTIATION
            #
            # A^B = target
            #
            # Instead of guessing B=0..20,
            # enumerate the actual possible exponents
            # from the right interval.
            # =================================================

            right = full_dp(k, j)

            for exponent, expr_b in right.items():

                # Forward DP only permits integer exponents
                if exponent.denominator != 1:
                    continue

                exponent_int = exponent.numerator

                # Same practical safety boundary as full DP
                if abs(exponent_int) > 100:
                    continue

                # A^0 = 1
                if exponent_int == 0:

                    if target != 1:
                        continue

                    base = Fraction(1)

                else:

                    base = rational_nth_root_exact(
                        target,
                        abs(exponent_int)
                    )

                    if base is None:
                        continue

                    # Negative exponent:
                    #
                    # A^(-n) = target
                    # A^n = 1/target
                    #
                    if exponent_int < 0:

                        if target == 0:
                            continue

                        base = rational_nth_root_exact(
                            Fraction(1, 1) / target,
                            -exponent_int
                        )

                        if base is None:
                            continue

                expr_a = can_make(
                    i,
                    k,
                    base
                )

                if expr_a is not None:

                    return (
                        f"({expr_a}^{expr_b})"
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

    print()
    print("Building full DP...")

    all_values = full_dp(
        0,
        len(digits)
    )

    print(
        "Number of values:",
        len(all_values)
    )

    print()
    print("Checking reverse search...")

    failures = []

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

        print("VALIDATION FAILED.")
        print(
            "Number of failures:",
            len(failures)
        )

        print()
        print("Failed values:")

        for value in failures:
            print(
                "FAILED:",
                value
            )

        return False

    print("VALIDATION SUCCESS.")

    print()
    print(
        "Full DP and target search agree for:",
        digits
    )

    return True


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print("10958 SEARCH PROJECT")
    print("STAGE 9A - VALIDATION")
    print("========================================")

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


if __name__ == "__main__":
    main()
