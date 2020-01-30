import glob


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
                wav_file_name = glob.glob("./train/**/*/{0}".format(wav_file), recursive=True)
                if len(wav_file_name) == 0:
                    print("File not found ({0}), from {1}... SKIPPING".format(wav_file, file_name))
                    continue
                if len(wav_file_name) >= 2:
                    print("Ambiguous wav file name:\nText: {0}\nFile names:{1}".format(text, wav_file_name))
                    continue
                wav_file_name = wav_file_name[0]
                sentences.append((text, wav_file_name))
    return sentences



if __name__ == "__main__":
    all_sentences = []
    for file_name in glob.glob("./train/**/*/*.spl", recursive=True):
        sentences = process(file_name)
        all_sentences.extend(sentences)
    with open('all-train.csv', 'wt') as f:
        f.write('wav_filename,transcript\n')
        for (text, wav_file) in all_sentences:
            f.write("{0}, {1}\n".format(wav_file, text))
