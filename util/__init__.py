
def file_load(file):
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file, d, clear=True):
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)
