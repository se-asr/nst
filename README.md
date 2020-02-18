## NST Processing
This is a repo for processing the NST dataset in preparation for use with DeepSpeech.
There are a couple of useful scripts that can be used in different parts of the process.
* `check_regions.py`*:
Checks how many spaekers have different `region_of_youth` and `region_of_birth`
* `find_dup_speakers.py`*:
Checks whether or not there are speakers that exists in both test-set and train-set
* `mono.py`:
Downmixing audio files to mono channel
* `process_spl.py`:
Parser for spl files
* `split_dataset.py`:
Splits the dataset and apply some filtering and normalization

\* only used to validate the dataset, if you trust us you don't need to run these.
### Split dataset

`python split_dataset.py --help` produces the following output
```
usage: split_dataset.py [-h] [--seed SEED] [--split SPLIT [SPLIT ...]]
                        [--file FILE] [--out-prefix OUT_PREFIX] [--no-test]
                        [--replace-umlauts]

Split input data file in three sets

optional arguments:
  -h, --help            show this help message and exit
  --seed SEED           applies seed to random split, use to achieve same
                        results as earlier run
  --split SPLIT [SPLIT ...]
                        split sizes to use [train, dev, test] (default: 0.6
                        0.2 0.2)
  --file FILE           path of input file (default: all-train.csv)
  --out-prefix OUT_PREFIX
                        prefix for out files (default: <empty string>,
                        produces train.csv dev.csv test.csv)
  --no-test             merge dev and test sets to one file, useful if you
                        have already set aside a test set
  --replace-umlauts     replace umlauts in Swedish with double letter
                        combinations (å->aa, ä->ae, ö->oe)
  --stats-only          don't save splits into files, just display statistics
```

Split dataset uses the `all-train.csv` file created by `process_spl.py` to create 3 new files (train.csv, dev.csv, test.csv). This is done according to the split supplied to the `--split` flag.

If the current split in the dataset will be used you can supply the `--no-test` flag. This will merge the dev and test sets, creating only a train.csv and a dev.csv. Keep in mind that no split can be set to 0 though, so if you e.g. want a split of 80 20 0 you will have to set `--split 80 10 10` and then `--no-test`

Example call:

```
python split_dataset.py
        --seed 133337
        --split 60 20 20
        --file input.csv
        --out-prefix nst
```
