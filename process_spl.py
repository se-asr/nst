import glob
import os.path
import subprocess


BAD_FILES = [
    './train/Stasjon3/280799/adb_0467/speech/scr0467/03/04670303/r4670265/u0265070.wav',
    './train/Stasjon6/060799/adb_0467/speech/scr0467/06/04670605/r4670479/u0479151.wav'
]

DEV_NULL = open(os.devnull, 'w')


def parse(line):
    line = line.split('=', 1)
    if len(line) <= 1:
        return None, None
    line = line[1]
    line = line.split('>-<')
    text = line[0]
    wav_file = line[-7]
    return text, wav_file


# [Info states]
# 1=Speaker ID>-<567>-<
# 2=Name>-<Erik Gustavsson>-<
# 3=Age>-<36>-<
# 4=Sex>-<Male>-<
# 5=Region of Birth>-<Stockholm med omnejd>-<
# 6=Region of Youth>-<Stockholm med omnejd>-<
# 7=Remarks>-<>-<
def parse_metadata(line):
    key = None
    value = None
    line = line.split('=', 1)
    if len(line) <= 1:
        return None, None
    line = line[1]
    if line.startswith('Speaker ID'):
        key = 'speaker_id'
    elif line.startswith('Age'):
        key = 'age'
    elif line.startswith('Sex'):
        key = 'sex'
    elif line.startswith('Region of Birth'):
        key = 'region_of_birth'
    elif line.startswith('Region of Youth'):
        key = 'region_of_youth'
    elif line.startswith('Remarks') or line.startswith('Name'):
        return 'ignored', None
    else:
        # Key not recognized
        print('Unknown key:', line)
        return None, None

    line = line.split('>-<')
    if len(line) <= 1:
        print("Value not found", line)
        return None, None
    value = line[1]
    return key, value


def process(file_name):
    sentences = []
    not_found = []
    speech_folder = file_name
    speech_folder = speech_folder[:-4] # Removes .spl
    speech_folder = speech_folder + "/"
    speech_folder = speech_folder.replace("data", "speech", 1)
    metadata = {
        'speaker_id': None,
        'age': None,
        'sex': None,
        'region_of_birth': None,
        'region_of_youth': None
    }
    with open(file_name, encoding='latin-1') as f:
        should_parse = False
        should_parse_metadata = False
        for line in f:
            line = line.strip()
            if line == '':
                continue
            if line.startswith('[End]') or line.startswith('[Operators]'):
                should_parse = False
                continue

            if line.startswith('[Validation states]'):
                should_parse = True
                continue
            if line.startswith('[Info states]'):
                should_parse_metadata = True
                continue
            if line.startswith('[Session]'):
                should_parse_metadata = False
                continue

            if should_parse:
                text, wav_file = parse(line)
                if not wav_file or not wav_file.endswith(".wav"):
                    print("Incorrect file: {0}".format(file_name))
                    print(line)
                    continue
                wav_file_name = speech_folder + wav_file
                if not os.path.isfile(wav_file_name):
                    not_found.append((wav_file_name, file_name))
                    continue
                if wav_file_name in BAD_FILES:
                    # We only want good (non broken) sound files
                    continue
                duration_in_seconds = float(subprocess.check_output(['soxi', '-D', wav_file_name], stderr=DEV_NULL))
                file_size = os.path.getsize(wav_file_name)
                sentences.append((text, wav_file_name, duration_in_seconds, file_size))
            if should_parse_metadata:
                key, value = parse_metadata(line)
                if not key:
                    print("Malformed metadata in {}".format(file_name))
                    continue
                metadata[key] = value
    return sentences, not_found, metadata


if __name__ == "__main__":
    sentence_count = 0
    not_found_count = 0
    with open('all-train.csv', 'wt') as f:
        f.write('wav_filename, duration_in_seconds, file_size, speaker_id, age, sex, region_of_birth, region_of_youth, transcript\n')
        for file_name in glob.glob("./train/**/*/*.spl", recursive=True):
            sentences, not_found, metadata = process(file_name)
            sentence_count += len(sentences)
            not_found_count += len(not_found)
            for (text, wav_file, duration_in_seconds, file_size) in sentences:
                if wav_file not in BAD_FILES:
                    # We only want good (non broken) sound files
                    f.write("{}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(wav_file, duration_in_seconds, file_size, metadata['speaker_id'], metadata['age'], metadata['sex'], metadata['region_of_birth'], metadata['region_of_youth'], text))
            for (wav_file_name, file_name) in not_found:
                print("Speech file not found in:\n\t{0}\nas defined in:\n\t{1}\n==================================".format(wav_file_name, file_name))
    print("\nTotal found sentences: {0}\nTotal not found: {1}".format(sentence_count, not_found_count))
