import glob

def find_dupes():
    speakers = set()
    for file_name in glob.glob("./test/**/*/*.spl", recursive=True):
        with open(file_name, encoding='latin-1') as f:
            for line in f:
                if "1=Speaker ID>" in line:
                    line = line.replace("1=Speaker ID>", "", 1)
                    line = ''.join(c for c in line if c.isdigit())
                    line = line.strip()
                    if line != "":
                        speakers.add(line)

    dup_count = 0
    duplicate_files = set()
    for file_name in glob.glob("./train/**/*/*.spl", recursive=True):
        with open(file_name, encoding='latin-1') as f:
            for line in f:
                if "1=Speaker ID>" in line:
                    line = line.replace("1=Speaker ID>", "", 1)
                    line = ''.join(c for c in line if c.isdigit())
                    if line in speakers:
                        print("Found duplicate speaker \"{0}\" in file: {1}".format(line, file_name))
                        duplicate_files.add(file_name)
                        dup_count += 1

    print("Found {0} duplicates".format(dup_count))
    print("Files to remove:")
    for f in duplicate_files:
        print(f)
    print("Directories to remove:")
    for f in duplicate_files:
        f = f.replace("data", "speech")
        f = f.replace(".spl", "/")
        print(f)

if __name__ == "__main__":
    find_dupes()
