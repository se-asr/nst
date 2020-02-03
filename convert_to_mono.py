import subprocess
import os
import sys

DEV_NULL = open(os.devnull, 'w')


def convert_to_mono(file_name, overwrite=True):
    # ffmpeg -y -i <input file> -ac 1 -ab 512k <output file>
    out_file = file_name.replace(".wav", "_mono.wav", 1)
    code = subprocess.call(['ffmpeg', '-y', '-i', file_name, '-ac', '1', '-ab', '512k', out_file], stdout=DEV_NULL, stderr=DEV_NULL)
    if not code == 0:
        return False # Failed to convert
    if overwrite:
        code = subprocess.call(['mv', out_file, file_name], stdout=DEV_NULL, stderr=DEV_NULL)
    return code == 0


if __name__ == "__main__":
    with open("all-train.csv", "r") as f:
        f.readline() # Skip header row
        for line in f:
            file_name = line.split(",", 1)[0]
            success = convert_to_mono(file_name)
            if not success:
                print("Failed to convert {0}".format(file_name))
                continue


