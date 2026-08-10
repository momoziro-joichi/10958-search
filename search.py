"""
10958 Target Search - Stage 5

123456789 を順番通りに使い、
連結・四則演算・累乗・括弧で
10958を作れるか探索する。

特徴:
- Exact Fraction
- Interval recursion
- Target-directed search
- 巨大な値集合を作らない
- 整数指数の累乗を逆算
"""

from fractions import Fraction
from functools import lru_cache
import math


DIGITS = "123456789"
TARGET = Fraction(10958)

MAX_EXPONENT = 20


# ============================================================
# 基本
# ============================================================

def concat_value(i, j):
    return Fraction(int(DIGITS[i:j]))


def is_integer(x):
    return x.denominator == 1


# ============================================================
# 整数累乗
# ============================================================

def exact_power(base, exponent):
    """
    base^exponent を厳密に計算。

    今回は整数base・非負整数exponentのみ。
    """

    if not is_integer(base):
        return None

    if not is_integer(exponent):
        return None

    b = base.numerator
    e = exponent.numerator

    if e < 0:
        return None

    if b == 0 and e == 0:
        return None

    return Fraction(b ** e)


# ============================================================
# target-directed search
# ============================================================

@lru_cache(maxsize=None)
def can_make(i, j, target):
    """
    DIGITS[i:j] を使って target を作れるか。

    見つかった場合:
        expression
    見つからなければ:
        None
    """

    # --------------------------------------------------------
    # 連結
    # --------------------------------------------------------

    if concat_value(i, j) == target:
        return DIGITS[i:j]

    # --------------------------------------------------------
    # 区間を分割
    # --------------------------------------------------------

    for k in range(i + 1, j):

        # ====================================================
        # A + B = target
        # ====================================================

        left_candidates = candidate_values(i, k)

        for a, expr_a in left_candidates:

            b = target - a

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}+{expr_b})"

        # ====================================================
        # A - B = target
        # ====================================================

        for a, expr_a in left_candidates:

            b = a - target

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}-{expr_b})"

        # ====================================================
        # A * B = target
        # ====================================================

        for a, expr_a in left_candidates:

            if a == 0:
                continue

            b = target / a

            expr_b = can_make(k, j, b)

            if expr_b is not None:
                return f"({expr_a}*{expr_b})"

        # ====================================================
        # A / B = target
        # ====================================================

        if target != 0:

            for a, expr_a in left_candidates:

                b = a / target

                if b == 0:
                    continue

                expr_b = can_make(k, j, b)

                if expr_b is not None:
                    return f"({expr_a}/{expr_b})"

        # ====================================================
        # A ^ B = target
        # ====================================================

        # 右側の指数候補を「生成」するのではなく、
        # 小さな整数指数だけを候補として試す。
        #
        # 10958 = 2 × 5479 なので、
        # 大きな整数べきになる可能性は非常に限定される。
        # ====================================================

        for exponent in range(1, MAX_EXPONENT + 1):

            exponent_f = Fraction(exponent)

            base = exact_root(target, exponent)

            if base is None:
                continue

            expr_a = can_make(i, k, base)

            if expr_a is None:
                continue

            expr_b = can_make(k, j, exponent_f)

            if expr_b is None:
                continue

            return f"({expr_a}^{expr_b})"

    return None


# ============================================================
# 左側候補
# ============================================================

@lru_cache(maxsize=None)
def candidate_values(i, j):
    """
    小さな区間について、
    その区間から作れる値を取得する。

    重要:
    大きな区間には原則として使わない。
    """

    result = {}

    # 連結
    value = concat_value(i, j)

    result[value] = DIGITS[i:j]

    # 1桁なら終了
    if j - i == 1:
        return result

    # 小区間についてのみDP
    for k in range(i + 1, j):

        left = candidate_values(i, k)
        right = candidate_values(k, j)

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

    return result


# ============================================================
# Exact root
# ============================================================

def integer_nth_root(n, k):
    """
    nの整数k乗根。
    完全なk乗ならその根を返す。
    """

    if n < 0:
        return None

    if n == 0:
        return 0

    if n == 1:
        return 1

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
    value^(1/exponent) が有理数なら返す。
    """

    if exponent <= 0:
        return None

    numerator = value.numerator
    denominator = value.denominator

    # 正
    if numerator >= 0:

        a = integer_nth_root(
            numerator,
            exponent
        )

        b = integer_nth_root(
            denominator,
            exponent
        )

        if a is None or b is None:
            return None

        return Fraction(a, b)

    # 負数は奇数指数のみ
    if exponent % 2 == 0:
        return None

    a = integer_nth_root(
        -numerator,
        exponent
    )

    b = integer_nth_root(
        denominator,
        exponent
    )

    if a is None or b is None:
        return None

    return Fraction(-a, b)


# ============================================================
# Main
# ============================================================

def main():

    print("========================================")
    print("10958 TARGET SEARCH")
    print("========================================")

    print(f"Digits : {DIGITS}")
    print(f"Target : {TARGET}")
    print()

    print("Searching...")
    print()

    result = can_make(
        0,
        len(DIGITS),
        TARGET
    )

    print()
    print("========================================")
    print("RESULT")
    print("========================================")

    if result:

        print("FOUND!")
        print()
        print(f"Expression: {result}")
        print(f"Value: {TARGET}")

    else:

        print("10958 was not found.")

    print()
    print("Search features:")
    print("  Exact Fraction arithmetic")
    print("  Concatenation")
    print("  + - * /")
    print("  Integer exponentiation")
    print("  Target-directed recursion")

    print()
    print("This is NOT yet an impossibility proof.")


if __name__ == "__main__":
    main()
