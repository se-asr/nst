from util import load_processed_train, load_processed_test, load_processed_dev
from split_dataset import load_train, load_test


if __name__ == "__main__":
    train_processed = load_processed_train()
    test_processed = load_processed_test()
    dev_processed = load_processed_dev()
    train = load_train()
    test = load_test()

    total = {}
    total_count = len(train) + len(test)
    for item in train + test:
        total[item["wav_file_name"]] = item

    for item in train_processed + dev_processed + test_processed:
        try:
            del total[item["wav_file_name"]]
        except KeyError as e:
            print("file not found: {}".format(e))

    with open("filtered_files.txt", "w") as out:
        tystnad_count = 0
        duration_count = 0
        total_removed = len(total)

        for item in total.values():
            if (item["text"] == "( ... tyst under denna inspelning ...)"):
                tystnad_count += 1
            elif (item["duration"] >= 10.0):
                duration_count += 1
            else:
                out.write("{}, {}, {}\n".format(item["wav_file_name"], item["duration"], item["text"]))

        print("Amount of silent files: {}, {}%".format(tystnad_count, (tystnad_count/total_count)*100))
        print("Amount of files with too long duration: {}, {}%".format(duration_count, (duration_count/total_count) * 100))
        print("Total removed: {}, {}%".format(total_removed, total_removed/total_count))
        print("Total: {}".format(total_count))