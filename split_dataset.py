import sys
import random
import argparse
import os
from collections import Counter
from util import normalize

DEFAULT_SEED = int(os.environ.get('DEFAULT_SEED', 1337))
TH_GENDER = float(os.environ.get('TH_GENDER', 0.001))
TH_DURATION = float(os.environ.get('TH_DURATION', 0.001))
TH_REGION = float(os.environ.get('TH_REGION', 0.1))

BAD_SOUND_FILES = [
    './train/Stasjon3/280799/adb_0467/speech/scr0467/03/04670303/r4670265/u0265070.wav',
    './train/Stasjon6/060799/adb_0467/speech/scr0467/06/04670605/r4670479/u0479151.wav',
    './train/Stasjon5/220799/adb_0467/speech/scr0467/05/04670505/r4670441/u0441079.wav',
    './train/Stasjon7/100799/adb_0467/speech/scr0467/07/04670706/r4670580/u0580189.wav',
    './train/Stasjon7/210799/adb_0467/speech/scr0467/07/04670707/r4670619/u0619087.wav',
    './train/Stasjon20/191099/adb_0467_2/speech/scr0467/20/04672001/r4670086/u0086079.wav',
    './train/Stasjon7/160799/adb_0467/speech/scr0467/07/04670706/r4670598/u0598102.wav',
    './train/Stasjon7/100899/adb_0467/speech/scr0467/07/04670707/r4670672/u0672205.wav',
    './train/Stasjon2/120799/adb_0467/speech/scr0467/02/04670202/r4670123/u0123069.wav',
    './train/Stasjon6/270799/adb_0467/speech/scr0467/06/04670606/r4670536/u0536161.wav'
]


def load_arg_parser():
    parser = argparse.ArgumentParser(description='Split input data file in \
                                                  three sets')
    parser.add_argument('--seed', dest='seed', type=int, help='applies seed to random split, use to achieve same results as earlier run')
    parser.add_argument('--split', dest='split', nargs='+', type=float, help='split sizes to use [train, dev, test] (default: 0.6 0.2 0.2)', default=[0.6, 0.2, 0.2])
    parser.add_argument('--file', type=str, help='path of input file (default: all-train.csv)', default='all-train.csv')
    parser.add_argument('--out-prefix', type=str, help='prefix for out files (default: <empty string>, produces train.csv dev.csv test.csv)', default='')
    parser.add_argument('--no-test', help='merge dev and test sets to one file, useful if you have already set aside a test set', action='store_true')
    parser.add_argument('--replace-umlauts', help='replace umlauts in Swedish with double letter combinations (å->aa, ä->ae, ö->oe)', action='store_true')
    parser.add_argument('--stats-only', help='don\'t save splits into files, just display statistics', action='store_true')
    parser.add_argument('--any-split', help='set all thresholds to 1', action='store_true')
    return parser

def load_train():
    return _load_data('all-train.csv')


def load_test():
    return _load_data('all-test.csv')


def _load_data(file_name):
    all_data = []
    with open(file_name, "r") as f:
        f.readline() # Skip header row
        for line in f:
            row = line.split(",")
            data = {
                'wav_file_name': row[0].strip(),
                'duration': float(row[1].strip()),
                'file_size': int(row[2].strip()),
                'speaker_id': row[3].strip(),
                'age': row[4].strip(),
                'sex': row[5].strip(),
                'region_of_birth': row[6].strip(),
                'region_of_youth': row[7].strip(),
                'text': ', '.join(row[8:]).strip()
            }
            all_data.append(data)
    return all_data


# Filters every item according to some filter functions defined
def filter_text(text):
    filter_functions = [
        lambda x: x == '( ... tyst under denna inspelning ...)',
        lambda x: "è" in x,
        lambda x: "ü" in x,
        lambda x: "î" in x,
        lambda x: "ÿ" in x
    ]
    for func in filter_functions:
        if (func(text)):
            return True
    return False


def fix_data(data_list, replace_umlauts):
    new_data = []

    for data in data_list:
        if data['duration'] >= 10.0:
            continue
        if data['speaker_id'].strip() == '':
            continue
        if filter_text(data['text']):
            continue
        if data['wav_file_name'] in BAD_SOUND_FILES:
            continue

        data['speaker_id'] =  data['speaker_id'].strip().replace('#', '')
        data['speaker_id'] =  data['speaker_id'].strip().replace('§', '')
        data['speaker_id'] =  data['speaker_id'].strip().replace('¨', '')

        data['text'] = normalize(data['text'], replace_umlauts)
        new_data.append(data)

    return new_data


def build_speaker_stats(data_list):
    stats = {}
    for data in data_list:
        speaker = data['speaker_id']
        speaker_stats = stats[speaker] if speaker in stats else {'duration': 0.0, 'file_size': 0, 'rows': 0}
        speaker_stats['age']                = data['age']
        speaker_stats['sex']                = data['sex']
        speaker_stats['region_of_youth']    = data['region_of_youth']
        speaker_stats['duration']          += data['duration']
        speaker_stats['file_size']         += data['file_size']
        speaker_stats['rows']              += 1
        stats[speaker] = speaker_stats
    return stats


def distribute_speakers(speaker_stats, split, seed):
    random.seed(seed)

    speakers_by_region = {}
    for speaker, stats in speaker_stats.items():
        region = stats['region_of_youth']
        if region not in speakers_by_region:
            speakers_by_region[region] = []
        speakers_by_region[region].append(speaker)

    train = []
    dev = []
    test = None
    if len(split) == 3:
        test = []

    for region, speakers in speakers_by_region.items():
        total_count = len(speakers)
        train_count = int(total_count * split['train'])
        dev_count = int(total_count * split['dev']) if test != None else total_count - train_count

        random.shuffle(speakers)

        train.extend(speakers[:train_count])
        dev.extend(speakers[train_count:train_count+dev_count])
        if test != None:
            test.extend(speakers[train_count+dev_count:])

    return train, dev, test

# Returns the largest difference between the items provided
def maxdiff(*stats):
    stats = [stat for stat in stats if stat]
    return max(stats) - min(stats)


# Like max(), but ignores None
def max_v2(data):
    return max([ val for val in data if val ])


def check_balance(speaker_stats, train, dev, test, split, verbose=False, early_exit=False):
    balanced = True
    def get_stats(data):
        ages = {}
        sexes = {}
        regions = {}
        duration = 0.0
        file_size = 0
        # Scale stats with how many rows/transcripts each speaker represent
        for d in data:
            duration += d['duration']
            file_size += d['file_size']
            rows = d['rows']
            age = d['age']
            ages[age] = ages[age] + rows if age in ages else rows
            sex = d['sex']
            sexes[sex] = sexes[sex] + rows if sex in sexes else rows
            region = d['region_of_youth']
            regions[region] = regions[region] + rows if region in regions else rows
        return {
            'age':              ages,
            'sex':              sexes,
            'region_of_youth':  regions,
            'duration':         duration,
            'file_size':        file_size
        }

    if verbose:
        print("Calcluating stats...")
    all_stats = get_stats([ stat for _, stat in speaker_stats.items() ])
    train_stats = get_stats([ stat for speaker, stat in speaker_stats.items() if speaker in train ])
    dev_stats = get_stats([ stat for speaker, stat in speaker_stats.items() if speaker in dev ])
    test_stats = None
    if test:
        test_stats = get_stats([ stat for speaker, stat in speaker_stats.items() if speaker in test ])

    if verbose:
        print("Checking gender balance, threshold: {}".format(TH_GENDER))

    def gender_difference(stats):
        male = stats['Male'] / (stats['Male'] + stats['Female'])
        female = stats['Female'] / (stats['Male'] + stats['Female'])
        return abs(male - female)

    total_gender_diff = gender_difference(all_stats['sex'])
    train_gender_diff = abs(gender_difference(train_stats['sex']) - total_gender_diff)
    dev_gender_diff = abs(gender_difference(dev_stats['sex']) - total_gender_diff)
    test_gender_diff = abs(gender_difference(test_stats['sex']) - total_gender_diff) if test else None

    if max_v2([train_gender_diff, dev_gender_diff, test_gender_diff]) >= TH_GENDER:
        if verbose:
            print("Failed gender check\ntrain: {}\ndev:   {}\ntest:  {}\n".format(train_gender_diff, dev_gender_diff, test_gender_diff))
        balanced = False
        if early_exit:
            return balanced
    elif verbose:
        print("Gender SUCCESS\ntrain: {}\ndev:   {}\ntest:  {}\n".format(train_gender_diff, dev_gender_diff, test_gender_diff))

    if verbose:
        print("Checking duration balance, threshold: {}".format(TH_DURATION))

    train_duration = train_stats['duration']
    dev_duration = dev_stats['duration']
    test_duration = test_stats['duration'] if test else 0.0
    total_duration = train_duration + dev_duration + test_duration

    train_duration_diff = abs(train_duration/total_duration - split['train'])
    dev_duration_diff = abs(dev_duration/total_duration - split['dev'])
    test_duration_diff = abs(test_duration/total_duration - split['test']) if test else None
    if max_v2([train_duration_diff, dev_duration_diff, test_duration_diff]) >= TH_DURATION:
        if verbose:
            print("Failed duration check\ntrain: {} ({:.2f}h)\ndev:   {} ({:.2f}h)\ntest:  {} ({:.2f}h)\n".format(train_duration_diff, train_duration/60.0/60.0, dev_duration_diff, dev_duration/60.0/60.0, test_duration_diff, test_duration/60.0/60.0))
        balanced = False
        if early_exit:
            return balanced
    elif verbose:
        print("Duration SUCCESS\ntrain: {} ({:.2f}h)\ndev:   {} ({:.2f}h)\ntest:  {} ({:.2f}h)\n".format(train_duration_diff, train_duration/60.0/60.0, dev_duration_diff, dev_duration/60.0/60.0, test_duration_diff, test_duration/60.0/60.0))

    if verbose:
        print("Checking region of youth balance, threshold: {}".format(TH_REGION))


    train_region_count = sum([ count for _, count in train_stats['region_of_youth'].items() ])
    dev_region_count = sum([ count for _, count in dev_stats['region_of_youth'].items() ])
    test_region_count = None
    if test:
        test_region_count = sum([ count for _, count in test_stats['region_of_youth'].items() ])
    total_region_count = train_region_count + dev_region_count
    if test:
        total_region_count += test_region_count

    for location, count in all_stats['region_of_youth'].items():
        train_part = train_stats['region_of_youth'][location]/train_region_count
        dev_part = dev_stats['region_of_youth'][location]/dev_region_count
        test_part = test_stats['region_of_youth'][location]/test_region_count if test else None
        train_diff = train_part / (all_stats['region_of_youth'][location]/total_region_count)
        dev_diff = dev_part / (all_stats['region_of_youth'][location]/total_region_count)
        test_diff = test_part / (all_stats['region_of_youth'][location]/total_region_count) if test else None
        if maxdiff(train_diff, dev_diff, test_diff) >= TH_REGION:
            if verbose:
                print("{} is unbalanced: ({}, {}, {})".format(location, train_diff, dev_diff, test_diff))
            balanced = False
    if not balanced:
        if verbose:
            print("Failed region of youth check\n")
        if early_exit:
            return balanced
    elif verbose:
        print("Region SUCCESS\n")

    return balanced


def do_split(speaker_stats, split, seed, verbose=False):
    print("*" * 80)
    print("Doing split using seed: {}".format(seed))
    if verbose:
        print("Distributing speakers in train, dev, and test sets")
    train, dev, test = distribute_speakers(speaker_stats, split, seed)

    if verbose:
        print("Checking if speaker stats are balanced")

    balanced = check_balance(speaker_stats, train, dev, test, split, verbose=verbose)

    return balanced, (train, dev, test)


def collect_data(data_list, partition):
    train, dev, test = partition
    d_train = []
    d_dev = []
    d_test = [] if test else None

    for item in data_list:
        speaker_id = item['speaker_id']
        if speaker_id in train:
            d_train.append(item)
        elif speaker_id in dev:
            d_dev.append(item)
        elif speaker_id in test and test:
            d_test.append(item)

    count_train = len(d_train)
    count_dev = len(d_dev)
    count_test = len(d_test) if test else 0
    if count_train + count_dev + count_test != len(data_list):
        print("Counts don't add up...")
        sys.exit(1)
    print(count_train, count_dev, count_test)
    return d_train, d_dev, d_test


def format_data_for_csv(data):
    file_name = data['wav_file_name']
    file_size = int(data['file_size'])
    text = data['text']
    return "{},{},{}\n".format(file_name, file_size, text)


def save_splits(train, dev, test, prefix=''):
    HEADER = 'wav_filename,wav_filesize,transcript\n'
    def write_csv(file_name, data):
        with open(file_name, 'w') as f:
            f.write(HEADER)
            for d in data:
                f.write(format_data_for_csv(d))
    write_csv("{}train.csv".format(prefix), train)
    write_csv("{}dev.csv".format(prefix), dev)
    if test:
        write_csv("{}test.csv".format(prefix), test)


def main(args):
    if args.any_split:
        print('Allowing any split')
        global TH_GENDER
        TH_GENDER = 1.0
        global TH_DURATION
        TH_DURATION = 1.0
        global TH_REGION
        TH_REGION = 1.0

    if abs(sum(args.split) - 1.0) > 0.000001: # Floating point error check
        print("Sum of split percentages must be 1 (100%)")
        sys.exit(1)

    splits = {
        'train': args.split[0],
        'dev': args.split[1],
        'test': None
    }

    if not args.no_test:
        if len(args.split) < 3:
            print("Test set wanted, but only two splits parameters given")
            sys.exit(1)
        splits['test'] = args.split[2]

    print("Loading data from file {}".format(args.file))
    all_data = _load_data(args.file)

    print("Fixing data")
    all_data = fix_data(all_data, args.replace_umlauts)

    print("Building speaker stats cache")
    speaker_stats = build_speaker_stats(all_data)

    if args.seed:
        print("Doing a single split using seed: {}".format(args.seed))
        balanced, partition = do_split(speaker_stats, splits, args.seed, verbose=True)
    else:
        seed = DEFAULT_SEED
        print("Starting search for a good split, starting with seed: {}".format(seed))
        balanced = False
        while not balanced:
            balanced, partition = do_split(speaker_stats, splits, seed, verbose=True)
            if not balanced:
                seed = random.randint(1, 9999999)
        print("\n\nSplit successful using seed: {}".format(seed))

    if args.stats_only:
        sys.exit(0)

    train, dev, test = collect_data(all_data, partition)
    save_splits(train, dev, test, prefix=args.out_prefix)


if __name__ == "__main__":
    args_parser = load_arg_parser()
    main(args_parser.parse_args(sys.argv[1:]))
