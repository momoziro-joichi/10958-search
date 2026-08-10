"""
10958 Search

123456789 を順番通りに使い、
連結・四則演算・累乗・括弧によって
10958 を作れるか探索する。

STEP 3:
- 区間DP
- Fractionによる厳密な有理数計算
- 整数指数の累乗
"""

from fractions import Fraction


DIGITS = "123456789"
TARGET = Fraction(10958)

# 巨大整数の暴走を防ぐための暫定上限。
# この上限を超えた累乗は今回は登録しない。
# 後のターゲット逆算で、この制限を取り除く。
MAX_POWER_DIGITS = 100


def safe_integer_power(a, b):
    """
    整数 a の b 乗を厳密に計算する。

    条件:
    - b は整数
    - b >= 0
    - 0^0 は除外
    - 結果が MAX_POWER_DIGITS 桁以内

    条件を満たさなければ None を返す。
    """

    if b < 0:
        return None

    if a == 0 and b == 0:
        return None

    # 0^positive = 0
    if a == 0:
        return 0

    # 1^b, (-1)^b
    if abs(a) == 1:
        return a ** b

    # 桁数を事前に概算
    # Pythonで巨大整数を作る前に確認する。
    import math

    estimated_digits = int(
        abs(b) * math.log10(abs(a))
    ) + 1

    if estimated_digits > MAX_POWER_DIGITS:
        return None

    return a ** b


def solve():
    n = len(DIGITS)

    # value -> expression
    dp = [[{} for _ in range(n + 1)] for _ in range(n)]

    # ========================================
    # 連結
    # ========================================

    for i in range(n):
        for j in range(i + 1, n + 1):

            value = Fraction(int(DIGITS[i:j]))

            expression = DIGITS[i:j]

            dp[i][j][value] = expression

    # ========================================
    # 区間DP
    # ========================================

    for length in range(2, n + 1):

        print(f"Processing length {length}...")

        for i in range(n - length + 1):

            j = i + length

            for k in range(i + 1, j):

                left = dp[i][k]
                right = dp[k][j]

                for a, expr_a in left.items():

                    for b, expr_b in right.items():

                        # --------------------------------
                        # +
                        # --------------------------------

                        value = a + b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}+{expr_b})"
                            )

                        # --------------------------------
                        # -
                        # --------------------------------

                        value = a - b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}-{expr_b})"
                            )

                        # --------------------------------
                        # *
                        # --------------------------------

                        value = a * b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}*{expr_b})"
                            )

                        # --------------------------------
                        # /
                        # --------------------------------

                        if b != 0:

                            value = a / b

                            if value not in dp[i][j]:
                                dp[i][j][value] = (
                                    f"({expr_a}/{expr_b})"
                                )

                        # --------------------------------
                        # ^
                        #
                        # STEP 3:
                        # 整数 ^ 整数 のみ
                        # --------------------------------

                        if (
                            a.denominator == 1
                            and b.denominator == 1
                        ):

                            base = a.numerator
                            exponent = b.numerator

                            power = safe_integer_power(
                                base,
                                exponent
                            )

                            if power is not None:

                                value = Fraction(power)

                                if value not in dp[i][j]:

                                    dp[i][j][value] = (
                                        f"({expr_a}^{expr_b})"
                                    )

        # ========================================
        # 探索規模
        # ========================================

        counts = []

        for i in range(n - length + 1):

            j = i + length

            counts.append(len(dp[i][j]))

        print(
            f"  intervals: {len(counts)}"
        )

        print(
            f"  min values: {min(counts)}"
        )

        print(
            f"  max values: {max(counts)}"
        )

        print(
            f"  total values: {sum(counts)}"
        )

    return dp


def main():

    print("=== 10958 Search ===")
    print(f"Digits : {DIGITS}")
    print(f"Target : {TARGET}")
    print()

    dp = solve()

    results = dp[0][len(DIGITS)]

    print()
    print("========================================")
    print("FINAL RESULT")
    print("========================================")

    print(
        f"Distinct rational values: {len(results)}"
    )

    if TARGET in results:

        print()
        print("FOUND!")

        print(
            f"Expression: {results[TARGET]}"
        )

        print(
            f"Value: {TARGET}"
        )

    else:

        print()
        print("10958 was not found.")

    print()
    print("========================================")
    print("FRACTION TESTS")
    print("========================================")

    print(
        "1/2 exists:",
        Fraction(1, 2) in results
    )

    print(
        "1/3 exists:",
        Fraction(1, 3) in results
    )


if __name__ == "__main__":
    main()
