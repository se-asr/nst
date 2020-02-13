import sys
import random
import re
import argparse

DEFAULT_SEED = 1337


BAD_SOUND_FILES = [
    './train/Stasjon3/280799/adb_0467/speech/scr0467/03/04670303/r4670265/u0265070.wav',
    './train/Stasjon6/060799/adb_0467/speech/scr0467/06/04670605/r4670479/u0479151.wav',
    './train/Stasjon5/220799/adb_0467/speech/scr0467/05/04670505/r4670441/u0441079.wav',
    './train/Stasjon7/100799/adb_0467/speech/scr0467/07/04670706/r4670580/u0580189.wav',
    './train/Stasjon7/210799/adb_0467/speech/scr0467/07/04670707/r4670619/u0619087.wav',
    './train/Stasjon20/191099/adb_0467_2/speech/scr0467/20/04672001/r4670086/u0086079.wav',
    './train/Stasjon7/160799/adb_0467/speech/scr0467/07/04670706/r4670598/u0598102.wav',
    './train/Stasjon7/100899/adb_0467/speech/scr0467/07/04670707/r4670672/u0672205.wav'
]

def load_arg_parser():
    parser = argparse.ArgumentParser(description='Split input data file in \
                                                  three sets')
    parser.add_argument('--seed', dest='seed', type=int, help='applies seed to random split, use to achieve same results as earlier run')
    parser.add_argument('--split', dest='split', nargs='+', type=int, help='split sizes to use [train, dev, test] (default: 0.6 0.2 0.2)', default=[60, 20, 20])
    parser.add_argument('--file', type=str, help='path of input file (default: all-train.csv)', default='all-train.csv')
    parser.add_argument('--out-prefix', type=str, help='prefix for out files (default: <empty string>, produces train.csv dev.csv test.csv)', default='')
    parser.add_argument('--no-test', help='merge dev and test sets to one file, useful if you have already set aside a test set', action='store_true')
    parser.add_argument('--replace-umlauts', help='replace umlauts in Swedish with double letter combinations (å->aa, ä->ae, ö->oe)', action='store_true')
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


def normalize(text, replace_umlauts):
    text = text.lower()
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    text = re.sub("[ ]{2,}", " ", text)
    text = text.replace(".", "")
    text = text.replace(",", "")
    text = text.replace(";", "")
    text = text.replace("?", "")
    text = text.replace("!", "")
    text = text.replace(":", "")
    text = text.replace("\"", "")
    text = text.replace("\\", " ")
    text = text.replace("é", "e")
    text = text.replace("&", "och")
    text = text.replace("  ", " ")
    if (replace_umlauts):
        text = text.replace("å", "aa")
        text = text.replace("ä", "ae")
        text = text.replace("ö", "oe")
    text = text.strip()
    return text


def find_speakers(data_list):
    speakers = []
    speaker_ids = []
    data = data_list.copy()

    for item in data:
        speaker_item = item.copy()

        if (speaker_item['speaker_id'] not in speaker_ids):
            del speaker_item['text']
            del speaker_item['wav_file_name']
            del speaker_item['duration']
            del speaker_item['file_size']
            speakers.append(speaker_item)
            speaker_ids.append(speaker_item['speaker_id'])
    return speakers


def distribute_speakers(speakers, train_size, dev_size, seed):
    speakers_by_region = dict()
    for speaker in speakers:
        region = speaker['region_of_youth']
        if region not in speakers_by_region.keys():
            speakers_by_region[region] = []
        speakers_by_region[region].append(speaker)

    train = []
    dev = []
    test =  []
    random.seed(seed)
    for region in speakers_by_region:
        no_train = int(len(speakers_by_region[region]) * train_size)
        no_dev = int(len(speakers_by_region[region]) * dev_size)

        random.shuffle(speakers_by_region[region])

        train.extend(speakers_by_region[region][:no_train])
        dev.extend(speakers_by_region[region][no_train:no_train+no_dev])
        test.extend(speakers_by_region[region][no_train+no_dev:])

    return (train, dev, test)


# Distributes items of the "all-train" file according to the speaker
# distribution
def distribute_items(speakers_ids_train, speakers_ids_dev,
                     speakers_ids_test, data_list):
    train = []
    dev = []
    test = []
    trcount = dcount = tcount = 0
    for item in data_list:
        if item['speaker_id'] in speakers_ids_train:
            train.append(item)
            trcount += 1
        elif item['speaker_id'] in speakers_ids_dev:
            dev.append(item)
            dcount += 1
        elif item['speaker_id'] in speakers_ids_test:
            test.append(item)
            tcount += 1
    print(trcount, dcount, tcount)
    return (train, dev, test)


# Returns a string given an item
# Item can be either dict or something castable to string
def item_to_str(item):
    if (isinstance(item, dict)):
        item_str = ""
        for key in item.keys():
            item_str += str(item[key])
        return item_str
    else:
        return str(item)


def check_distinctness(train, dev, test):
    exists = set()
    for item in train:
        exists.add(item_to_str(item))
    for item in dev:
        if item_to_str(item) in exists:
            print("Duplicate item!")
            print(item)
            return False
        else:
            exists.add(item_to_str(item))
    for item in test:
        if item_to_str(item) in exists:
            print("Duplicate item!")
            print(item)
            return False
    return True


# Checks if the datasets are balanced according to some metrics
def check_balance(train, dev, test, data_list, split):
    metrics = ['age', 'sex', 'region_of_youth']     #Metrics with multiple values
    integer_metrics = ['duration', 'file_size']     #Metrics with single value

    train_stats = get_stats(train, metrics, integer_metrics)
    dev_stats = get_stats(dev, metrics, integer_metrics)
    test_stats = get_stats(test, metrics, integer_metrics)
    all_train_stats = get_stats(data_list, metrics, integer_metrics)

    total_rows = {
        'train': len(train),
        'dev': len(dev),
        'test': len(test)
    }

    print("### Checking region of youth")
    res = check_locations(train_stats['region_of_youth'], dev_stats['region_of_youth'], test_stats['region_of_youth'], all_train_stats['region_of_youth'], total_rows, 0.20)
    print_result("Region of youth", res)
    if (not res):
        return False

    print("### Checking duration")
    res = check_duration(train_stats['duration'], dev_stats['duration'], test_stats['duration'], split, 0.05)
    print_result("Duration", res)
    if (not res):
        return False

    print("### Checking gender")
    res = check_gender(train_stats['sex'], dev_stats['sex'], test_stats['sex'], 0.05)
    print_result("Gender", res)
    if (not res):
        return False

    return True


def print_result(metric, res):
    if res:
        print("### {}: ✓".format(metric))
    else:
        print("### {}: ✖".format(metric))
    print("\n")


# Returns the largest difference between the items provided
def maxdiff(*stats):
    return max(stats) - min(stats)


# Returns false if any of the locations has
def check_locations(train_locations, dev_locations, test_locations,
                    all_train_locations, total_rows, threshold):
    train_locations = location_partition(train_locations, total_rows['train'])
    dev_locations = location_partition(dev_locations, total_rows['dev'])
    test_locations = location_partition(test_locations, total_rows['test'])
    all_train_locations = location_partition(all_train_locations,
                                             total_rows['train'] +
                                             total_rows['dev'] +
                                             total_rows['test'])

    success = True
    for location in all_train_locations:
        if maxdiff(train_locations[location]/all_train_locations[location],
                   dev_locations[location]/all_train_locations[location],
                   test_locations[location]/all_train_locations[location]
                   ) > threshold:
            print("{} is unbalanced".format(location))
            print(train_locations[location]/all_train_locations[location],
                  dev_locations[location]/all_train_locations[location],
                  test_locations[location]/all_train_locations[location])
            success = False
    return success


# Returns how big part of the dataset is from each location
def location_partition(location_stats, total_rows):
    stats = location_stats.copy()
    for location in stats:
        stats[location] = stats[location]/total_rows
    return stats


# Returns false if the difference in gender distribution is greater
# than the threshold
def check_gender(train_gender, dev_gender, test_gender, threshold):
    train_diff = gender_difference(train_gender)
    dev_diff = gender_difference(dev_gender)
    test_diff = gender_difference(test_gender)
    print("\nGender difference in absolute percents")
    print("Threshold: {}".format(threshold))
    print("train: {}\ndev: {}\ntest: {}\n".format(train_diff, dev_diff, test_diff))

    return maxdiff(train_diff, dev_diff, test_diff) < threshold


# Returns the difference between genders in a split
def gender_difference(gender_stats):
    male = gender_stats['Male'] / (gender_stats['Male'] + gender_stats['Female'])
    female = gender_stats['Female'] / (gender_stats['Male'] + gender_stats['Female'])
    return abs(male - female)


def check_duration(train_duration, dev_duration, test_duration, split,
                   threshold):
    total_duration = (train_duration + dev_duration + test_duration)
    train_duration = train_duration/total_duration
    dev_duration = dev_duration/total_duration
    test_duration = test_duration/total_duration
    print("\nDuration difference in absolute percents")
    print("Threshold: {}".format(threshold))
    print("train: {}\ndev: {}\ntest: {}\n".format(train_duration, dev_duration, test_duration))
    return (abs(train_duration - split['train']) < threshold and
            abs(dev_duration - split['dev']) < threshold and
            abs(test_duration - split['test']) < threshold)


# Calculates the average age of a dataset
def average_age(ages_dict):
    total = 0
    number_of_persons = 0
    for age in ages_dict.keys():
        try:
            total += int(age) * ages_dict[age]
            number_of_persons += ages_dict[age]
        except:
            continue
    return total/number_of_persons


def get_stats(dataset, metrics, integer_metrics):
    stats = dict()
    for stat in metrics:
        stats[stat] = dict()
    for stat in integer_metrics:
        stats[stat] = 0
    for item in dataset:
        for metric in metrics:
            try:
                stats[metric][item[metric]] += 1
            except:
                stats[metric][item[metric]] = 1

        for metric in integer_metrics:
            stats[metric] += item[metric]
    return stats


def filter_file_names(file_name):
    return file_name in BAD_SOUND_FILES


def fix_data(data_list, replace_umlauts):
    items_to_remove = []
    for i in range(len(data_list)):
        if (filter_text(data_list[i]['text'])):     # Filter out items with text that we don't want
            items_to_remove.append(i)
        if (data_list[i]['duration'] >= 10.0):      # Deepspeech cant handle clips 10 seconds and longer
            items_to_remove.append(i)
        if (data_list[i]['speaker_id'] == ''):
            items_to_remove.append(i)
        if (filter_file_names(data_list[i]['wav_file_name'])):
            items_to_remove.append(i)

        data_list[i]['speaker_id'].replace('#', '')
        data_list[i]['speaker_id'].replace('§', '')
        data_list[i]['speaker_id'].replace('¨', '')

        data_list[i]['text'] = normalize(data_list[i]['text'], replace_umlauts)
    # Reverse the list to mitigate index out of bounds when removing items
    items_to_remove.reverse()
    for item in items_to_remove:
        del data_list[item]


def format_item(item):
    item_str = ""
    item_str += item['wav_file_name']
    item_str += ","
    item_str += str(int(item['file_size']))
    item_str += ","
    item_str += item['text']
    item_str += "\n"
    return item_str


def iteration(speakers, split, seed):
    success = True
    print("seed is: ", seed)
    print("Distributing speakers in train, dev and test sets")
    train_speakers, dev_speakers, test_speakers = distribute_speakers(speakers, split['train'], split['dev'], seed)

    print("Checking speaker distinctness")
    success &= check_distinctness(train_speakers, dev_speakers, test_speakers)

    train_ids = [item['speaker_id'] for item in train_speakers]
    dev_ids = [item['speaker_id'] for item in dev_speakers]
    test_ids = [item['speaker_id'] for item in test_speakers]

    print("Distributing items according to speaker distribution")
    train, dev, test = distribute_items(
        train_ids, dev_ids, test_ids, data_list
    )

    print("Checking balance")
    success &= check_balance(train, dev, test, data_list, split)

    print("Checking distinctness")
    success &= check_distinctness(train, dev, test)

    return success, train, dev, test


if __name__ == "__main__":
    args_parser = load_arg_parser()

    args = args_parser.parse_args(sys.argv[1:])
    print(args)
    if (sum(args.split)!=100):
        print("Sum of split must be 100")
        exit(0)

    split = {
        'train': args.split[0]/100,
        'dev': args.split[1]/100,
        'test': args.split[2]/100
    }

    print("Loading data from file {}".format(args.file))
    data_list = _load_data(args.file)

    print("Fixing data")
    fix_data(data_list, args.replace_umlauts)

    print("Finding unique speakers")
    speakers = find_speakers(data_list)

    if (args.seed):
        res, train, dev, test = iteration(speakers, split, args.seed)
    else:
        seed = DEFAULT_SEED
        while True:
            res, train, dev, test = iteration(speakers, split, seed)
            if res:
                break
            seed = random.randint(1, 1000000)

    with open("{}train.csv".format(args.out_prefix), "w") as train_file:
        train_file.write('wav_filename,wav_filesize,transcript\n')
        for item in train:
            train_file.write(format_item(item))

    if (args.no_test):
        with open("{}dev.csv".format(args.out_prefix), "w") as dev_file:
            dev_file.write('wav_filename,wav_filesize,transcript\n')
            for item in dev+test:
                dev_file.write(format_item(item))
    else:
        with open("{}dev.csv".format(args.out_prefix), "w") as dev_file:
            dev_file.write('wav_filename,wav_filesize,transcript\n')
            for item in dev:
                dev_file.write(format_item(item))

        with open("{}test.csv".format(args.out_prefix), "w") as test_file:
            test_file.write('wav_filename,wav_filesize,transcript\n')
            for item in test:
                test_file.write(format_item(item))
