from split_dataset import load_train, load_test

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

