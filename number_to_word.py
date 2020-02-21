import math
import sys

TEN = 10
ONE_HUNDRED = 100
ONE_THOUSAND = 1000
ONE_MILLION = 1000000
ONE_BILLION = 1000000000            # 1.000.000.000 (9)
ONE_TRILLION = 1000000000000        # 1.000.000.000.000 (12)
ONE_QUADRILLION = 1000000000000000  # 1.000.000.000.000.000 (15)
MAX = 999999999999999              # 9.007.199.254.740.992 (15)

LESS_THAN_TWENTY = [
    'noll', 'ett', 'två', 'tre', 'fyra', 'fem',
    'sex', 'sju', 'åtta', 'nio', 'tio',
    'elva', 'tolv', 'tretton', 'fjorton',
    'femton', 'sexton', 'sjutton', 'arton', 'nitton'
]

TENTHS_LESS_THAN_HUNDRED = [
    'noll', 'tio', 'tjugo', 'trettio', 'fyrtio',
    'femtio', 'sextio', 'sjuttio', 'åttio', 'nittio'
]


# Converts an integer into words.
# If number is decimal, the decimals will be removed.
# @example to_words(12) => 'twelve'
# @param {number|string} number
# @returns {string}
def to_words(number):
    try:
        num = int(number)
    except ValueError:
        raise ValueError('Input is not a number')

    if (num == 0):
        return "noll"
    if (abs(num) > MAX):
        raise ValueError('Value is too large (>999999999999)')
    words = generate_words(num)
    return words

def recurse(number, prefix, suffix, divisor):
    remainder = number % divisor
    num = math.floor(number / divisor)
    if (num == 1):
        return prefix + 'en ' + suffix + " " + generate_words(remainder)
    else:
        return prefix + generate_words(num) + suffix + 'er ' + generate_words(remainder)

def generate_words(number):
    remainder = 0
    word = ''

    # We’re done
    if (number == 0):
        return ''

    # If negative, prepend “minus”
    if (number < 0):
        word = 'minus '
        number = abs(number)

    if (number < 20):
        remainder = 0
        return LESS_THAN_TWENTY[number]
    elif (number < ONE_HUNDRED):
        remainder = number % 10
        return word + TENTHS_LESS_THAN_HUNDRED[math.floor(number / TEN)] \
            + generate_words(remainder)
    elif (number < ONE_THOUSAND):
        remainder = number % ONE_HUNDRED
        return word + LESS_THAN_TWENTY[math.floor(number / ONE_HUNDRED)] \
            + 'hundra' + generate_words(remainder)
    elif (number < ONE_MILLION):
        remainder = number % ONE_THOUSAND
        return word + generate_words(math.floor(number/ONE_THOUSAND)) \
            + ' tusen ' + generate_words(remainder)
    elif (number < ONE_BILLION):
        return recurse(number, word, ' miljon', ONE_MILLION)
    elif (number < ONE_TRILLION):
        return recurse(number, word, ' miljard', ONE_BILLION)
    elif (number < ONE_QUADRILLION):
        return recurse(number, word, ' biljon', ONE_TRILLION)


if __name__ == "__main__":
    print(to_words(sys.argv[1]))
