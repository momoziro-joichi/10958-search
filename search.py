"""
10958 Search

123456789 を順番通りに使い、
連結・四則演算・括弧によって 10958 を作れるか探索する。

STEP 2.5:
- 区間DP
- Fractionによる厳密な有理数計算
- 探索規模の計測
"""

from fractions import Fraction


DIGITS = "123456789"
TARGET = Fraction(10958)


def solve():
    n = len(DIGITS)

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

                        # ----------------------------
                        # +
                        # ----------------------------

                        value = a + b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}+{expr_b})"
                            )

                        # ----------------------------
                        # -
                        # ----------------------------

                        value = a - b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}-{expr_b})"
                            )

                        # ----------------------------
                        # *
                        # ----------------------------

                        value = a * b

                        if value not in dp[i][j]:
                            dp[i][j][value] = (
                                f"({expr_a}*{expr_b})"
                            )

                        # ----------------------------
                        # /
                        # ----------------------------

                        if b != 0:

                            value = a / b

                            if value not in dp[i][j]:
                                dp[i][j][value] = (
                                    f"({expr_a}/{expr_b})"
                                )

        # ========================================
        # この長さでの探索規模
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
