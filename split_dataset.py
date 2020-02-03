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
                'speaker_id': row[1].strip(),
                'age': row[2].strip(),
                'sex': row[3].strip(),
                'region_of_birth': row[4].strip(),
                'region_of_youth': row[5].strip(),
                'text': ', '.join(row[6:]).strip()
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
            print("Speaker id not int", item['speaker_id'])
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

def distribute_speakers(speakers, train_size, dev_size, test_size):
    no_train = int(len(speakers) * train_size)
    no_dev = int(len(speakers) * dev_size)
    random.shuffle(speakers)
    return (speakers[:no_train], speakers[no_train:no_train+no_dev], speakers[no_train+no_dev:])

if __name__ == "__main__":
    train = load_train()
    speakers = find_speakers(train)
    train, dev, test = distribute_speakers(speakers, 0.6, 0.2, 0.2)
    
    