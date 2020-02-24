import os
import csv
import sys
import subprocess
from util import normalize

DEV_NULL = open(os.devnull, 'w')

if __name__ == "__main__":
    rows = []
    with open(sys.argv[1], "r") as input_file:
        input_csv = csv.reader(input_file)
        for row in input_csv:
            rows.append(row)

    with open(sys.argv[1], "w") as input_file:
        writer = csv.writer(input_file)
        for row in rows:
            if (row[0].endswith(".mp3")):
                row[0] = "./" + row[0][:-4] + ".wav"
            duration_in_seconds = float(subprocess.check_output(['soxi', '-D', row[0]], stderr=DEV_NULL))
            if duration_in_seconds < 10.0:
                normalized = normalize(row[2])
                if normalized.strip() != '':
                    writer.writerow([row[0], row[1], normalized])
