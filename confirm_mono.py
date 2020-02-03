import subprocess
import os
import sys

DEV_NULL = open(os.devnull, 'w')


def confirm_is_mono(file_name):
    try:
        channels = int(subprocess.check_output(["soxi", "-c", file_name], stderr=DEV_NULL))
        return channels == 1
    except subprocess.CalledProcessError as ex:
        print("Exception when checking: {0}".format(ex))
        return False


if __name__ == "__main__":
    with open("all-train.csv", "r") as f:
        f.readline() # Skip header row
        for line in f:
            file_name = line.split(",", 1)[0]
            success = confirm_is_mono(file_name)
            if not success:
                print("Not Mono: {0}".format(file_name))
                continue

