"""
10958 Search

123456789 を順番通りに使い、
連結・四則演算・括弧によって 10958 を作れるか探索する。

現在の段階:
- 区間DP
- 整数による厳密計算
- 連結
- 四則演算
"""

DIGITS = "123456789"
TARGET = 10958


def solve():
    n = len(DIGITS)

    # dp[i][j]:
    # DIGITS[i:j] から作れる値を保存する辞書
    #
    # 例:
    # dp[0][2] は "12" から作れる値
    #
    # value -> expression
    dp = [[{} for _ in range(n + 1)] for _ in range(n)]

    # ----------------------------------------
    # STEP 1: 連結した数字を登録
    # ----------------------------------------
    for i in range(n):
        for j in range(i + 1, n + 1):
            value = int(DIGITS[i:j])
            expression = DIGITS[i:j]

            dp[i][j][value] = expression

    # ----------------------------------------
    # STEP 2: 区間を短い順に処理
    # ----------------------------------------
    for length in range(2, n + 1):

        for i in range(n - length + 1):
            j = i + length

            # 区間 [i, j) を
            # [i, k) と [k, j) に分割
            for k in range(i + 1, j):

                left = dp[i][k]
                right = dp[k][j]

                # 左右の値を組み合わせる
                for a, expr_a in left.items():
                    for b, expr_b in right.items():

                        # 加算
                        value = a + b
                        if value not in dp[i][j]:
                            dp[i][j][value] = f"({expr_a}+{expr_b})"

                        # 減算
                        value = a - b
                        if value not in dp[i][j]:
                            dp[i][j][value] = f"({expr_a}-{expr_b})"

                        # 乗算
                        value = a * b
                        if value not in dp[i][j]:
                            dp[i][j][value] = f"({expr_a}*{expr_b})"

                        # 除算
                        if b != 0 and a % b == 0:
                            value = a // b
                            if value not in dp[i][j]:
                                dp[i][j][value] = f"({expr_a}/{expr_b})"

    return dp


def main():
    print("=== 10958 Search ===")
    print(f"Digits : {DIGITS}")
    print(f"Target : {TARGET}")
    print()

    dp = solve()

    results = dp[0][len(DIGITS)]

    print(f"Number of distinct values: {len(results)}")

    if TARGET in results:
        print()
        print("FOUND!")
        print(results[TARGET])
    else:
        print()
        print("10958 was not found.")


if __name__ == "__main__":
    main()
