# read all-train file
# randomly split into train,dev,dev-test 60/20/20
# check that each constraint is less than 5% difference
# write to new csvs, train.csv dev.csv test.csv

import os
import sys
import random
import re
import copy

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
                'file_size': float(row[2].strip()),
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
        lambda x: ("è" or "ü" or "î" or "ÿ") in x
    ]
    for func in filter_functions:
        if (func(text)):
            return True
    return False

def normalize(text):
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
    text = text.strip()
    text = text.lower()
    return text

# Finds every unique speaker in the dataset
def find_speakers(data_list):
    speakers = []
    speaker_ids = []
    data = data_list.copy()
    for item in data:
        speaker_item = item.copy()
        if (speaker_item['speaker_id'].startswith("#")):
            speaker_item['speaker_id'] = speaker_item['speaker_id'][1:] #remove '#' from start of some speaker ids
       
        if (speaker_item['speaker_id'] not in speaker_ids):
            if (filter_text(speaker_item['text'])):
                continue
            del speaker_item['text']
            del speaker_item['wav_file_name']
            speakers.append(speaker_item)
            speaker_ids.append(speaker_item['speaker_id'])
    return speakers

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
        if (not filter_text(item['text'])):    
            if item['speaker_id'] in speakers_ids_train:
                normalize(item['text'])
                train.append(item)
                trcount += 1
            elif item['speaker_id'] in speakers_ids_dev:
                normalize(item['text'])
                dev.append(item)
                dcount += 1
            elif item['speaker_id'] in speakers_ids_test:
                normalize(item['text'])
                test.append(item)
                tcount += 1
    print(trcount, dcount, tcount)
    return (train, dev, test)

# Checks whether any of the items exists in more than one dataset
# WARNING: Takes LOOOOOONG time to run
def check_distinctness(train, dev, test):
    for item in train:
        if item in dev or item in test:
            print("Duplicate item!")
            print(item)

# Checks if the datasets are balanced according to some metrics
def check_balance(train, dev, test):
    metrics = ['age', 'sex', 'region_of_youth']     #Metrics with multiple values
    integer_metrics = ['duration', 'file_size']     #Metrics with single value

    train_stats = get_stats(train, metrics, integer_metrics)
    dev_stats = get_stats(dev, metrics, integer_metrics)
    test_stats = get_stats(test, metrics, integer_metrics)

    # train_stats['age'] = average_age(train_stats['age'])
    # dev_stats['age'] = average_age(dev_stats['age'])
    # test_stats['age'] = average_age(test_stats['age'])
    dataset_stats = {'train':train_stats, 'dev':dev_stats, 'test':test_stats}
    total_rows = dict()
    for dataset in dataset_stats:
        total_rows[dataset] = get_total_texts_in_split(dataset_stats[dataset])

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

def fix_data(data_list):
    items_to_remove = []
    for i in range(len(data_list)):
        if (filter_text(data_list[i]['text'])):     # Filter out items with text that we don't want
            items_to_remove.append(i)
        if (data_list[i]['duration'] >= 10.0):      # Deepspeech cant handle clips 10 seconds and longer
            items_to_remove.append(i)

    # Reverse the list to mitigate index out of bounds when removing items
    items_to_remove.reverse()
    for item in items_to_remove:
        del data_list[item]
        
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
    
    # Get ids for each speaker
    train_ids = [item['speaker_id'] for item in train_speakers]
    dev_ids = [item['speaker_id'] for item in dev_speakers]
    test_ids = [item['speaker_id'] for item in test_speakers]

    print("Distributing items according to speaker distribution")
    train, dev, test = distribute_items(train_ids, dev_ids, test_ids, data_list)
    
    print("Checking balance")
    check_balance(train, dev, test)
    
    