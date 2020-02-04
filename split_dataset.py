import os
import sys
import random
import re

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

def normalize(text):
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
    text = text.replace("\\", "")
    text = text.replace("é", "e")
    text = text.replace("&", "och")
    text = text.strip()
    return text

def find_speakers(data_list):
    speakers = set()
    for item in data_list:
        speakers.add(item['speaker_id'])
    return list(speakers)

# Distributes speakers according to the dataset split sizes
def distribute_speakers(speakers, train_size, dev_size, seed):
    no_train = int(len(speakers) * train_size)
    no_dev = int(len(speakers) * dev_size)
    random.seed(seed)
    random.shuffle(speakers)
    return (speakers[:no_train], speakers[no_train:no_train+no_dev], speakers[no_train+no_dev:])

# Distributes items of the "all-train" file according to the speaker distribution
def distribute_items(speakers_ids_train, speakers_ids_dev, speakers_ids_test, data_list):
    train = []
    dev = []
    test = []
    trcount = dcount = tcount = 0
    data = data_list.copy()
    for item in data:
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
        else:
            exists.add(item_to_str(item))
    for item in test:
        if item_to_str(item) in exists:
            print("Duplicate item!")
            print(item)

# Checks if the datasets are balanced according to some metrics
def check_balance(train, dev, test):
    metrics = ['age', 'sex', 'region_of_youth']     #Metrics with multiple values
    integer_metrics = ['duration', 'file_size']     #Metrics with single value

    train_stats = get_stats(train, metrics, integer_metrics)
    dev_stats = get_stats(dev, metrics, integer_metrics)
    test_stats = get_stats(test, metrics, integer_metrics)

    total_rows = {
        'train': len(train),
        'dev': len(dev),
        'test': len(test)
    }

    print("### Checking gender")
    res = check_gender(train_stats['sex'], dev_stats['sex'], test_stats['sex'], 0.05)
    print_result("Gender", res)

    print("### Checking region of youth")
    res = check_locations(train_stats['region_of_youth'], dev_stats['region_of_youth'], test_stats['region_of_youth'], total_rows, 0.10)
    print_result("Region of youth", res)
    
def print_result(metric, res):
    if res:
        print("### {}: ✓".format(metric))
    else:
        print("### {}: ✖".format(metric))

# Returns the largest difference between the items provided
def maxdiff(*stats):
    return max(stats) - min(stats)

def get_total_texts_in_split(dataset):
    total = 0
    for sex in dataset['sex'].values(): # Any value would work here since the total amount of any stat is the same
        total += sex
    return total
    
# Returns false if any of the locations has 
def check_locations(train_locations, dev_locations, test_locations, total_rows, threshold):    
    train_locations = location_partition(train_locations, total_rows['train'])
    dev_locations = location_partition(dev_locations, total_rows['dev'])
    test_locations = location_partition(test_locations, total_rows['test'])

    for location in train_locations:
        if maxdiff(train_locations[location], dev_locations[location], test_locations[location]) > threshold:
            print("{} is passing the threshold for unbalance".format(location))
            return False
    return True
    
# Returns how big part of the dataset is from each location
def location_partition(location_stats, total_rows):
    stats = location_stats.copy()
    for location in stats:
        stats[location] = stats[location]/total_rows
    return stats

# Returns false if the difference in gender distribution is greater than the threshold 
def check_gender(train_gender, dev_gender, test_gender, threshold):
    train_diff = gender_difference(train_gender)
    dev_diff = gender_difference(dev_gender)
    test_diff = gender_difference(test_gender)

    return maxdiff(train_diff, dev_diff, test_diff) > threshold

# Returns the difference between genders in a split
def gender_difference(gender_stats):
    male = gender_stats['Male'] / (gender_stats['Male'] + gender_stats['Female'])
    female = gender_stats['Female'] / (gender_stats['Male'] + gender_stats['Female'])
    return abs(male - female)

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
    filter_functions = [
        lambda x: x == './train/Stasjon3/280799/adb_0467/speech/scr0467/03/04670303/r4670265/u0265070.wav',
        lambda x: x == './train/Stasjon6/060799/adb_0467/speech/scr0467/06/04670605/r4670479/u0479151.wav',
        lambda x: x == './train/Stasjon5/220799/adb_0467/speech/scr0467/05/04670505/r4670441/u0441079.wav'
    ]
    for func in filter_functions:
        if (func(file_name)):
            return True
    return False

def fix_data(data_list):
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

        data_list[i]['text'] = normalize(data_list[i]['text'])
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
    
if __name__ == "__main__":
    seed = "1337"
    print("Loading data from file")
    data_list = load_train()

    print("Fixing data")
    fix_data(data_list)

    print("Finding unique speakers")
    speakers = find_speakers(data_list)

    print("Distributing speakers in train, dev and test sets")
    train_speakers, dev_speakers, test_speakers = distribute_speakers(speakers, 0.6, 0.2, seed)

    print("Checking speaker distinctness")
    check_distinctness(train_speakers, dev_speakers, test_speakers)
    
    print("Distributing items according to speaker distribution")
    train, dev, test = distribute_items(train_speakers, dev_speakers, test_speakers, data_list)
    
    print("Checking distinctness")
    check_distinctness(train, dev, test)
        
    print("Checking balance")
    check_balance(train, dev, test)

    # make location threshold relative to total size
    # check duration
    # reshuffle if checks fail

    with open("train.csv", "w") as train_file:
        train_file.write('wav_filename,wav_filesize,transcript\n')
        for item in train:
            train_file.write(format_item(item))

    with open("dev.csv", "w") as dev_file:
        dev_file.write('wav_filename,wav_filesize,transcript\n')
        for item in dev:
            dev_file.write(format_item(item))
        
    with open("test.csv", "w") as test_file:
        test_file.write('wav_filename,wav_filesize,transcript\n')
        for item in test:
            test_file.write(format_item(item))
        
    