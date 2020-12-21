import os


def locate(filename, search_path=os.environ['PATH'], path_sep=os.pathsep):
    """
    Helper function to locate a file in the os PATH.
    """

    for path in search_path.split(path_sep):
        cur = os.path.join(path, filename)
        if os.path.exists(cur):
            return os.path.abspath(cur)
    return None
