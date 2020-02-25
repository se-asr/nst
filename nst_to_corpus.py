#!/usr/bin/env python3
import sys

from split_dataset import load_train, load_test


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        print("usage: ./nst_to_corpus.py <train/test> <destination.txt>")
        sys.exit(1)
    source = args[0].strip()
    destination = args[1].strip()

    if source == "train":
        data = load_train()
    elif source == "test":
        data = load_test()
    else:
        print("unknown dataset:", source, "(should be train or test)")
        sys.exit(1)

    sentences = ' '.join([d['text'] for d in data])

    with open(destination, 'w') as f:
        f.write(sentences)
