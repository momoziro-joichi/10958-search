"""
10958 Search
123456789 を順番通りに使って 10958 を作れるか探索する。

STEP 1:
まずは数字列と連結数を正しく扱うための土台を作る。
"""

DIGITS = "123456789"
TARGET = 10958


def concatenated_numbers(s):
    """文字列 s の全ての連続部分文字列を整数として返す。"""
    numbers = []

    for i in range(len(s)):
        for j in range(i + 1, len(s) + 1):
            numbers.append(int(s[i:j]))

    return numbers


def main():
    print("=== 10958 Search ===")
    print(f"Digits : {DIGITS}")
    print(f"Target : {TARGET}")
    print()

    numbers = concatenated_numbers(DIGITS)

    print("Concatenated numbers:")
    print(numbers)


if __name__ == "__main__":
    main()
