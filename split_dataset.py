# read all-train file
# randomly split into train,dev,dev-test 60/20/20
# check that each constraint is less than 5% difference
# write to new csvs, train.csv dev.csv test.csv

import os
import sys
import random

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

def filter_item(item):
    filter_functions = [
        lambda x: x == '( ... tyst under denna inspelning ...)',
        lambda x: x.endswith(('\\Punkt', '\\Komma', '\\Frågetecken', '\\Utropstecken'))
    ]
    for func in filter_functions:
        if (func(item)):
            return False
    return True

def normalize(item):
    item['text'] = item['text'].lower()

def find_speakers(data_list):
    speakers = []
    speaker_ids = []

    for item in data_list.copy():
        if (item['speaker_id'].startswith("#")):
            item['speaker_id'] = item['speaker_id'][1:] #remove '#' from start of some speaker ids
        
        try:
            item['speaker_id'] = int(item['speaker_id'])
        except:
            continue

        if (item['speaker_id'] not in speaker_ids):
            if (not filter_item(item['text'])):
                continue
            normalize(item)
            del item['text']
            del item['wav_file_name']
            speakers.append(item)
            speaker_ids.append(item['speaker_id'])
    return speakers

def distribute_speakers(speakers, train_size, dev_size, seed):
    no_train = int(len(speakers) * train_size)
    no_dev = int(len(speakers) * dev_size)
    random.seed(seed)
    random.shuffle(speakers)
    return (speakers[:no_train], speakers[no_train:no_train+no_dev], speakers[no_train+no_dev:])

def distribute_items(speakers_ids_train, speakers_ids_dev, speakers_ids_test, data_list):
    train = []
    dev = []
    test = []
    trcount = dcount = tcount = 0
    for item in data_list.copy():
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

def check_distinctness(train, dev, test):
    for item in train:
        if item in dev or item in test:
            print("Duplicate item!")
            print(item)

def check_balance(train, dev, test):
    metrics = ['age', 'sex', 'region_of_youth'] #Metrics with multiple answers
    integer_metrics = ['duration', 'file_size']   #Metrics with an integer value
    train_stats = get_stats(train, metrics, integer_metrics)
    dev_stats = get_stats(dev, metrics, integer_metrics)
    test_stats = get_stats(test, metrics, integer_metrics)
    
    train_stats['age'] = average_age(train_stats['age'])
    dev_stats['age'] = average_age(dev_stats['age'])
    test_stats['age'] = average_age(test_stats['age'])

    dataset_stats = {'train':train_stats, 'dev':dev_stats, 'test':test_stats}
    total_rows = dict()
    for dataset in dataset_stats:
        total_rows[dataset] = get_total_texts_in_split(dataset_stats[dataset])

    check_gender(train_stats['sex'], dev_stats['sex'], test_stats['sex'], 0.05)
    check_locations(train_stats['region_of_youth'], dev_stats['region_of_youth'], test_stats['region_of_youth'], total_rows, 0.10)
    
def maxdiff(*stats):
    return max(stats) - min(stats)

def get_total_texts_in_split(dataset):
    total = 0
    for sex in dataset['sex'].values():
        total += sex
    return total
    
def check_locations(train_locations, dev_locations, test_locations, total_rows, threshold):    
    train_locations = location_partition(train_locations, total_rows['train'])
    dev_locations = location_partition(dev_locations, total_rows['dev'])
    test_locations = location_partition(test_locations, total_rows['test'])

    for location in train_locations:
        if maxdiff(train_locations[location], dev_locations[location], test_locations[location]) > threshold:
            print("{} is passing the threshold for unbalance".format(location))
            return False
    return True
    
def location_partition(location_stats, total_rows):
    stats = location_stats.copy()
    for location in stats:
        stats[location] = stats[location]/total_rows
    return stats

def check_gender(train_gender, dev_gender, test_gender, threshold):
    train_diff = gender_difference(train_gender)
    dev_diff = gender_difference(dev_gender)
    test_diff = gender_difference(test_gender)
    print(train_diff, dev_diff, test_diff)
    return maxdiff(train_diff, dev_diff, test_diff) > threshold

def gender_difference(gender_stats):
    male = gender_stats['Male'] / (gender_stats['Male'] + gender_stats['Female'])
    female = gender_stats['Female'] / (gender_stats['Male'] + gender_stats['Female'])
    return abs(male - female)

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

if __name__ == "__main__":
    seed = "1337"
    print("Loading data from file")
    data_list = load_train()
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
    # print("Checking distinctness")
    # check_distinctness(train, dev, test)
    
    