import glob
import os.path


def parse(line):
    line = line.split('=', 1)
    if len(line) <= 1:
        return None, None
    line = line[1]
    line = line.split('>-<')
    text = line[0]
    wav_file = line[-7]
    return text, wav_file


def process(file_name):
    sentences = []
    not_found = []
    speech_folder = file_name
    speech_folder = speech_folder[:-4] # Removes .spl
    speech_folder = speech_folder + "/"
    speech_folder = speech_folder.replace("data", "speech", 1)
    with open(file_name, encoding='latin-1') as f:
        should_parse = False
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
                sentences.append((text, wav_file_name))
    return sentences, not_found


if __name__ == "__main__":
    all_sentences = []
    all_not_found = []
    for file_name in glob.glob("./train/**/*/*.spl", recursive=True):
        sentences, not_found = process(file_name)
        all_sentences.extend(sentences)
        all_not_found.extend(not_found)
    with open('all-train.csv', 'wt') as f:
        f.write('wav_filename,transcript\n')
        for (text, wav_file) in all_sentences:
            f.write("{0}, {1}\n".format(wav_file, text))
    for (wav_file_name, file_name) in all_not_found:
        print("Speech file not found in:\n\t{0}\nas defined in:\n\t{1}\n==================================".format(wav_file_name, file_name))
    print("\nTotal found sentences: {0}\nTotal not found: {1}".format(len(all_sentences), len(all_not_found)))
