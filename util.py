import re
import tempfile
from number_to_word import to_words

units = {
    'mm': 'millimeter',
    'cm': 'centimeter',
    'dm': 'decmieter',
    'km': 'kilometer',
    'm': 'meter',
    'ml': 'milliliter',
    'cl': 'centiliter',
    'dl': 'deciliter',
    'l': 'liter',
}

re_units = {}
for key, _ in units.items():
    re_units[key] = re.compile(r"\b{0}(²|³)?\b".format(re.escape(key)))

re_square = re.compile(r"([\w]+)²")
re_cubic  = re.compile(r"([\w]+)³")

re_combine_digits = re.compile(r"(\d)(\u00A0| )(\d)")
re_sep_decimals = re.compile(r"(\d),(\d)")
re_digit_range = re.compile(r"(\d)-(\d)")

re_remove_silent_date = re.compile(r"\(\d{1,2}/\d{1,2} \d+\)")

re_numbers = re.compile(r"\d+")
re_spaces = re.compile(r"\s\s+")                    # matches 2 or more consecutive spaces
re_replace_all = re.compile(r"[^a-z|å|ä|ö|\s]")

TMP_DIR = tempfile.mkdtemp()


def normalize(text):
    text = text.lower()
    text = re_remove_silent_date.sub('', text)
    text = text.replace('"', '')
    text = text.replace('.', '')
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace("_", " ")
    text = text.replace("\\", " ")
    text = text.replace("é", "e")
    text = text.replace("&", "och")
    for key, pattern in re_units.items():
        replacement = r"{0}\1".format(re.escape(units[key]))
        text = pattern.sub(replacement, text)
    text = re_square.sub(r"kvadrat\1", text)
    text = re_cubic.sub(r"kubik\1", text)
    text = re_combine_digits.sub(r"\1\3", text)
    text = re_sep_decimals.sub(r"\1 komma \2", text)
    text = re_digit_range.sub(r"\1 till \2", text)
    text = text.replace('-', ' ')
    text = text.replace('%', 'procent')
    def number_to_word(match):
        match = match.group()
        word = match
        try:
            word = to_words(match)
        except ValueError as ex:
            print('Failed to convert "{}": {}'.format(match, ex))
        return word
    text = re_numbers.sub(number_to_word, text)
    text = re_replace_all.sub('', text)
    text = re_spaces.sub(' ', text)
    return text.strip()