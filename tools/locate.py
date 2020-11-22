import os


def locate(filename, search_path=os.environ['PATH'], pathsep=os.pathsep):
    for path in search_path.split(pathsep):
        cur = os.path.join(path, filename)
        if os.path.exists(cur):
            return os.path.abspath(cur)
    return None