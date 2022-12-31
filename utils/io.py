import os


def mkdirp(path: str):
    if not os.path.isdir(path):
        os.mkdir(path)