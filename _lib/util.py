import os

#:  .. versionadded:: 0.10.0
DIR = 0x4000
#:  .. versionadded:: 0.10.0
FILE = 0x8000


def read_at(path, offset=0, n=None):
    '''Read from file at specified offset.

    Parameters
    ----------
    path : str
        Path of file to read.
    offset : int, optional
        Offset from start of file (in bytes).
    n : int, optional
        Number of bytes to read. By default, read to end of file.


    .. versionadded:: 0.10.0
    '''
    with open(path, 'r') as input_:
        input_.seek(offset)
        return input_.read(n)


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def is_dir(path):
    '''.. versionadded:: 0.10.0'''
    try:
        return True if os.stat(path)[0] & DIR else False
    except OSError:
        return False


def is_file(path):
    '''.. versionadded:: 0.10.0'''
    try:
        return True if os.stat(path)[0] & FILE else False
    except OSError:
        return False


def rmtree(directory):
    for entry in os.ilistdir(directory):
        is_dir = entry[1] == 0x4000
        if is_dir:
            rmtree(directory + '/' + entry[0])
        else:
            os.remove(directory + '/' + entry[0])
    os.rmdir(directory)


def copyfile(src_path, dst_path, chunk_size=1024):
    with open(src_path, 'rb') as input_:
        with open(dst_path, 'wb') as output:
            while True:
                data = input_.read(chunk_size)
                output.write(data)
                if not data:
                    break


def copytree(src_dir, dst_dir, verbose=False):
    for entry in os.ilistdir(src_dir):
        is_dir = entry[1] == 0x4000
        src_path = src_dir + '/' + entry[0]
        dst_path = dst_dir + '/' + entry[0]
        if is_dir:
            if not exists(dst_path):
                os.mkdir(dst_path)
            copytree(src_path, dst_path)
        else:
            copyfile(src_path, dst_path)
            if verbose:
                print('copied: `%s` to `%s`' % (src_path, dst_path))


def walk_files(top):
    '''Return a list of full paths, one to each file under specified dir.


    .. versionadded:: 0.10.0
    '''
    paths = []
    top_ = '' if top == '/' else top
    for p in os.listdir(top):
        full_p = top_ + '/' + p
        if is_dir(full_p):
            paths += [p_i for p_i in walk_files(full_p)]
        elif is_file(full_p):
            paths.append(full_p)
    return paths


def walk_stat(top):
    '''Return a list of stat tuples, one to each file under specified dir.


    .. versionadded:: 0.10.0
    '''
    return [(p, ) + os.stat(p) for p in walk_files(top)]
