"""Independent exact evaluator for the solver's fully parenthesized grammar.

No solver, DP, root inversion, Python eval, or floating-point arithmetic.
Call under a process time/memory budget: exact powers can be expensive.
"""
from fractions import Fraction


def verify_expression(expression, digits, target, max_abs_exponent, root_split=None):
    if not digits or any(c not in '0123456789' for c in digits):
        raise ValueError('Invalid digits')
    if type(max_abs_exponent) is not int or max_abs_exponent < 0:
        raise ValueError('Invalid exponent cap')
    if not isinstance(expression, str) or len(expression) > 4 * len(digits) - 3:
        raise ValueError('Invalid expression length')
    if ''.join(c for c in expression if c in '0123456789') != digits:
        raise ValueError('Expression digit order/count mismatch')
    position = 0

    def parse():
        nonlocal position
        start = position
        while position < len(expression) and expression[position] in '0123456789':
            position += 1
        if position > start:
            return Fraction(int(expression[start:position])), position - start, None
        if position >= len(expression) or expression[position] != '(':
            raise ValueError('Expected digits or opening parenthesis')
        position += 1
        left, left_count, _ = parse()
        if position >= len(expression) or expression[position] not in '+-*/^':
            raise ValueError('Invalid operator')
        operator = expression[position]
        position += 1
        right, right_count, _ = parse()
        if position >= len(expression) or expression[position] != ')':
            raise ValueError('Expected closing parenthesis')
        position += 1
        if operator == '+':
            value = left + right
        elif operator == '-':
            value = left - right
        elif operator == '*':
            value = left * right
        elif operator == '/':
            if right == 0:
                raise ValueError('Division by zero')
            value = left / right
        else:
            if right.denominator != 1 or abs(right) > max_abs_exponent:
                raise ValueError('Exponent outside integer cap')
            if left == 0 and right <= 0:
                raise ValueError('Undefined zero power')
            value = left ** right.numerator
        return value, left_count + right_count, left_count

    value, _, split = parse()
    if position != len(expression):
        raise ValueError('Trailing expression content')
    # A concatenated literal is accepted in any solver partition.
    if root_split is not None and split is not None and split != root_split:
        raise ValueError('Expression belongs to a different root split')
    if value != Fraction(target):
        raise ValueError('Expression value does not equal target')
    return value
