from fractions import Fraction
from functools import lru_cache

DIGITS = "123"


# ============================================================
# ① 従来方式：区間から「作れる全ての値」を求める
# ============================================================

@lru_cache(maxsize=None)
def generate_values(i, j):
    result = {}

    # 連結
    result[Fraction(int(DIGITS[i:j]))] = DIGITS[i:j]

    # 区間を分割
    for k in range(i + 1, j):

        left = generate_values(i, k)
        right = generate_values(k, j)

        for a, expr_a in left.items():
            for b, expr_b in right.items():

                # +
                value = a + b
                if value not in result:
                    result[value] = f"({expr_a}+{expr_b})"

                # -
                value = a - b
                if value not in result:
                    result[value] = f"({expr_a}-{expr_b})"

                # *
                value = a * b
                if value not in result:
                    result[value] = f"({expr_a}*{expr_b})"

                # /
                if b != 0:
                    value = a / b
                    if value not in result:
                        result[value] = f"({expr_a}/{expr_b})"

                # ^（今回は整数指数のみ）
                if (
                    b.denominator == 1
                    and 0 <= b.numerator <= 10
                    and not (a == 0 and b == 0)
                ):
                    value = a ** b.numerator

                    if value not in result:
                        result[value] = f"({expr_a}^{expr_b})"

    return result


# ============================================================
# ② 新方式：target を指定して逆向きに探索
# ============================================================

@lru_cache(maxsize=None)
def can_make(i, j, target):
    """
    DIGITS[i:j] から target を作れるか？

    作れる → 式
    作れない → None
    """

    # 連結そのもの
    if Fraction(int(DIGITS[i:j])) == target:
        return DIGITS[i:j]

    # 1桁なら終了
    if j - i == 1:
        return None

    # 全ての分割
    for k in range(i + 1, j):

        # ----------------------------------------------------
        # A + B = target
        # B = target - A
        # ----------------------------------------------------

        left_values = generate_values(i, k)

        for a, expr_a in left_values.items():

            b = target - a

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}+{expr_b})"

        # ----------------------------------------------------
        # A - B = target
        # B = A - target
        # ----------------------------------------------------

        for a, expr_a in left_values.items():

            b = a - target

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}-{expr_b})"

        # ----------------------------------------------------
        # A * B = target
        # B = target / A
        # ----------------------------------------------------

        for a, expr_a in left_values.items():

            if a == 0:
                continue

            b = target / a

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}*{expr_b})"

        # ----------------------------------------------------
        # A / B = target
        # B = A / target
        # ----------------------------------------------------

        if target != 0:

            for a, expr_a in left_values.items():

                b = a / target

                if b == 0:
                    continue

                expr_b = can_make(k, j, b)

                if expr_b is not None:
                    return f"({expr_a}/{expr_b})"

        # ----------------------------------------------------
        # A ^ B = target
        #
        # 今回は簡単化のため、
        # 整数指数だけを扱う。
        # ----------------------------------------------------

        if target != 0:

            for exponent in range(0, 11):

                # target = A^exponent
                if exponent == 0:

                    if target != 1:
                        continue

                    base = Fraction(1)

                else:

                    # target の整数指数根を探す
                    base = None

                    for candidate in range(-100, 101):

                        if Fraction(candidate) ** exponent == target:
                            base = Fraction(candidate)
                            break

                    if base is None:
                        continue

                expr_a = can_make(i, k, base)

                if expr_a is None:
                    continue

                expr_b = can_make(
                    k,
                    j,
                    Fraction(exponent)
                )

                if expr_b is not None:
                    return f"({expr_a}^{expr_b})"

    return None


# ============================================================
# ③ 比較テスト
# ============================================================

def main():

    print("========================================")
    print("STAGE 9 - SMALL VALIDATION")
    print("========================================")

    print()
    print("Digits:", DIGITS)
    print()

    # 全値DP
    all_values = generate_values(0, len(DIGITS))

    print(
        "Number of values from full DP:",
        len(all_values)
    )

    print()

    # --------------------------------------------------------
    # 全値DPで得られた「全ての値」が、
    # 逆向き探索でも作れるか確認する
    # --------------------------------------------------------

    print("Checking reverse search...")
    print()

    failures = []

    for index, value in enumerate(all_values):

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

            # 最初の数個だけ表示
            if len(failures) >= 10:
                break

    print()
    print("========================================")
    print("VALIDATION RESULT")
    print("========================================")

    if not failures:

        print()
        print("SUCCESS!")
        print()
        print(
            "Every value generated by the full DP "
            "was also found by reverse search."
        )

        print()
        print(
            "The two methods agree for DIGITS = 123."
        )

    else:

        print()
        print(
            "VALIDATION FAILED."
        )

        print(
            "Number of failures:",
            len(failures)
        )

    print()

    # --------------------------------------------------------
    # 10958はまだ探索しない
    # --------------------------------------------------------

    print("10958 search:")
    print("NOT RUN YET")

    print()
    print(
        "Stage 9 first validates the algorithm "
        "on a tiny search space."
    )


if __name__ == "__main__":
    main()
