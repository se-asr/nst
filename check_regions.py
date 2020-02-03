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


def check_regions(data):
    count = 0
    speaker_ids = set()
    for d in data:
        if d['region_of_birth'] != d['region_of_youth']:
            count += 1
            print("Non matching:\n", d, "\n\n")
            speaker_ids.add(d['speaker_id'])

    print("total non matching:", count)
    print("unique non matching:", len(speaker_ids))


if __name__ == "__main__":
    all_data = load_train()
    check_regions(all_data)

