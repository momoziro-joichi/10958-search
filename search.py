from fractions import Fraction
from functools import lru_cache


# ============================================================
# Configuration
# ============================================================

MAX_ABS_EXPONENT = 100


def target_exponent_candidates(target, limit):
    """A necessary bound for rational bases; never a magnitude cutoff.

    For reduced a/b raised to nonzero e, every nonunit numerator or
    denominator component of the target is an integer |e|-th power.
    Such a component c is at least 2**|e|, so |e| <= c.bit_length()-1.
    Negative exponents swap components and obey the same bound.
    Targets 0, 1 and -1 need the original full exponent range.
    """
    if target not in (0, 1, -1):
        components = (abs(target.numerator), target.denominator)
        limit = min(limit, *(c.bit_length() - 1 for c in components if c > 1))
    return range(-limit, limit + 1)


def digit_power_exponents(base, target, limit):
    """All e in [-limit, limit] with base**e == target, for digits 0..9.

    For base >= 2 the positive powers are strictly increasing integers;
    negative powers are their reciprocals. Repeated exact division identifies
    the unique exponent without constructing each candidate power.
    """
    if base == 0:
        return range(1, limit + 1) if target == 0 else ()
    if base == 1:
        return range(-limit, limit + 1) if target == 1 else ()
    if target <= 0:
        return ()
    if target.denominator == 1:
        remaining, sign = target.numerator, 1
    elif target.numerator == 1:
        remaining, sign = target.denominator, -1
    else:
        return ()
    exponent = 0
    while remaining != 1:
        if exponent == limit:
            return ()
        remaining, remainder = divmod(remaining, base)
        if remainder:
            return ()
        exponent += 1
    return (sign * exponent,)


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

    if exponent == 1:
        return n

    if exponent >= n.bit_length():
        return None

    lo = 0
    hi = 1 << ((n.bit_length() + exponent - 1) // exponent)

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

def make_solver(digits, *, root_split=None, lookup_digits=4, edge_inversion=True,
                max_abs_exponent=MAX_ABS_EXPONENT, exponent_lookup_digits=4,
                right_inversion_digits=2):

    if type(max_abs_exponent) is not int or max_abs_exponent < 0:
        raise ValueError("max_abs_exponent must be a nonnegative integer")

    if not digits or any(c not in "0123456789" for c in digits):
        raise ValueError("digits must be a nonempty ASCII digit string")

    if root_split is not None and not 1 <= root_split < len(digits):
        raise ValueError("root_split must be inside the digit string")
    if not isinstance(lookup_digits, int) or lookup_digits < 0:
        raise ValueError("lookup_digits must be a nonnegative integer")

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
                    # Both search directions use max_abs_exponent.
                    # ----------------------------------------

                    if (
                        b.denominator == 1
                        and not (a == 0 and b <= 0)
                    ):

                        exponent = b.numerator

                        # This bound limits the searched expression space.
                        if abs(exponent) <= max_abs_exponent:

                            value = a ** exponent

                            result.setdefault(
                                value,
                                f"({expr_a}^{expr_b})"
                            )

        return result

    # ========================================================
    # TARGET-DIRECTED SEARCH
    # ========================================================

    def can_make(i, j, target):
        # Do not retain millions of distinct failed single-digit targets.
        if j - i == 1:
            return digits[i:j] if Fraction(int(digits[i:j])) == target else None
        restricted_root = root_split is not None and i == 0 and j == len(digits)
        if j - i <= lookup_digits and not restricted_root:
            return full_dp(i, j).get(target)
        return cached_can_make(i, j, target)

    @lru_cache(maxsize=50000)
    def cached_can_make(i, j, target):

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

        splits = (root_split,) if (
            root_split is not None and i == 0 and j == len(digits)
        ) else sorted(range(i + 1, j), key=lambda k: (abs(2 * k - i - j), k))
        for k in splits:

            # A single right digit fixes the operand/exponent. Invert it
            # directly instead of materializing a potentially huge left table.
            if edge_inversion and j - k == 1:
                b = Fraction(int(digits[k:j]))
                expr_b = digits[k:j]
                candidates = [(target - b, "+"), (target + b, "-")]
                if b:
                    candidates += [(target / b, "*"), (target * b, "/")]
                elif target == 0:
                    return f"({digits[i:k]}*{expr_b})"
                for base, operator in candidates:
                    expr_a = can_make(i, k, base)
                    if expr_a is not None:
                        return f"({expr_a}{operator}{expr_b})"
                if b == 0:
                    # A string containing a nonzero digit has a nonzero
                    # concatenation; an all-zero string cannot make nonzero.
                    if target == 1 and int(digits[i:k]) != 0:
                        return f"({digits[i:k]}^{expr_b})"
                elif b <= max_abs_exponent:
                    root = rational_nth_root_exact(target, b.numerator)
                    if root is not None:
                        roots = [root]
                        if b.numerator % 2 == 0 and root != 0:
                            roots.append(-root)
                        for base in roots:
                            expr_a = can_make(i, k, base)
                            if expr_a is not None:
                                return f"({expr_a}^{expr_b})"
                continue

            # Enumerate a small right operand instead of a large left table.
            # Each recursive query consumes fewer digits; all values stay exact.
            if j - k <= right_inversion_digits and k - i > j - k:
                for b, expr_b in full_dp(k, j).items():
                    candidates = [(target - b, "+"), (target + b, "-")]
                    if b:
                        candidates += [(target / b, "*"), (target * b, "/")]
                    elif target == 0:
                        return f"({digits[i:k]}*{expr_b})"
                    for base, operator in candidates:
                        expr_a = can_make(i, k, base)
                        if expr_a is not None:
                            return f"({expr_a}{operator}{expr_b})"
                    if b.denominator != 1 or abs(b) > max_abs_exponent:
                        continue
                    exponent = b.numerator
                    if exponent == 0:
                        # All-zero digits cannot produce a nonzero value.
                        if target == 1 and int(digits[i:k]) != 0:
                            return f"({digits[i:k]}^{expr_b})"
                        continue
                    if exponent < 0 and target == 0:
                        continue
                    root_target = Fraction(1) / target if exponent < 0 else target
                    root = rational_nth_root_exact(root_target, abs(exponent))
                    if root is None:
                        continue
                    bases = [root]
                    if exponent % 2 == 0 and root != 0:
                        bases.append(-root)
                    for base in bases:
                        expr_a = can_make(i, k, base)
                        if expr_a is not None:
                            return f"({expr_a}^{expr_b})"
                continue

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

                # Zero products/quotients cannot be inverted by division.
                if a == 0 and target == 0:
                    return f"({expr_a}*{digits[k:j]})"

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
            # Short right intervals use forward enumeration; long ones
            # query bounded integer exponents after checking exact roots.
            # =================================================

            # Invert powers of a digit exactly; retain all exponents for the
            # degenerate bases 0 and 1, which are not one-to-one.
            if edge_inversion and k - i == 1:
                base = int(digits[i:k])
                for exponent in digit_power_exponents(base, target, max_abs_exponent):
                    expr_b = can_make(k, j, Fraction(exponent))
                    if expr_b is not None:
                        return f"({digits[i:k]}^{expr_b})"
                continue

            # Long exponent operands are queried only after a feasible base
            # is known. Never truncate intermediate values in forward DP.
            directed = j - k > exponent_lookup_digits
            candidates = ((Fraction(e), None) for e in
                          target_exponent_candidates(target, max_abs_exponent)) if directed else full_dp(k, j).items()

            for exponent, expr_b in candidates:

                # Forward DP only permits integer exponents
                if exponent.denominator != 1:
                    continue

                exponent_int = exponent.numerator

                # Same practical safety boundary as full DP
                if abs(exponent_int) > max_abs_exponent:
                    continue

                # Every nonzero base satisfies A^0 = 1.
                if exponent_int == 0:
                    if target == 1:
                        for base, expr_a in left.items():
                            if base != 0:
                                witness = can_make(k, j, exponent) if directed else expr_b
                                if witness is not None:
                                    return f"({expr_a}^{witness})"
                                break
                    continue

                # Invert negative powers before taking the exact root.
                if exponent_int < 0:
                    if target == 0:
                        continue
                    root_target = Fraction(1) / target
                else:
                    root_target = target

                root = rational_nth_root_exact(
                    root_target, abs(exponent_int)
                )
                if root is None:
                    continue

                # Even powers have both positive and negative base candidates.
                bases = [root]
                if exponent_int % 2 == 0 and root != 0:
                    bases.append(-root)

                for base in bases:
                    expr_a = left.get(base)
                    if expr_a is not None:
                        witness = can_make(k, j, exponent) if directed else expr_b
                        if witness is not None:
                            return f"({expr_a}^{witness})"
                        break

        return None

    # Preserve the existing cache inspection/cleanup interface.
    can_make.cache_clear = cached_can_make.cache_clear
    can_make.cache_info = cached_can_make.cache_info
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
