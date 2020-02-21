import csv
import sys
from util import normalize, filter_text

if __name__ == "__main__":
    rows = []
    with open(sys.argv[1], "r") as input_file:
        input_csv = csv.reader(input_file)
        for row in input_csv:
            rows.append(row)

    with open(sys.argv[1], "w") as input_file:
        writer = csv.writer(input_file)
        for row in rows:
            writer.writerow([row[0], row[1], normalize(row[2], False)])
