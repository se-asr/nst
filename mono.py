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


def convert_to_mono(file_name, overwrite=True):
    # ffmpeg -y -i <input file> -ac 1 -ab 512k <output file>
    out_file = file_name.replace(".wav", "_mono.wav", 1)
    code = subprocess.call(['ffmpeg', '-y', '-i', file_name, '-ac', '1', '-ab', '512k', out_file], stdout=DEV_NULL, stderr=DEV_NULL)
    if not code == 0:
        return False # Failed to convert
    if overwrite:
        code = subprocess.call(['mv', out_file, file_name], stdout=DEV_NULL, stderr=DEV_NULL)
    return code == 0


def convert_dataset(file_name):
    failed = 0
    not_mono = 0
    print("Converting all sound files specified in {} to mono...".format(file_name))
    with open(file_name, "r") as f:
        f.readline() # Skip header row
        for line in f:
            wav_file_name = line.split(",", 1)[0]
            success = convert_to_mono(file_name, overwrite=True)
            if not success:
                print("Failed to convert {}".format(wav_file_name))
                failed += 1
                continue
            success = confirm_is_mono(file_name)
            if not success:
                print("Not mono: {}".format(wav_file_name))
                not_mono += 1
                continue
    print("Coverting to mono complete.\nFailed: {}\nNon monoL: {}".format(failed, not_mono))


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Must specify either \"train\" or \"test\"")
        sys.exit(1)
    target = sys.argv[1].strip()
    if target == "train":
        convert_dataset("all-train.csv")
    elif target == "test":
        convert_dataset("all-test.csv")
    else:
        print("Unknown target \"{}\"".format(target))
        sys.exit(1)
