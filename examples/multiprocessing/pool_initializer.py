import logging

from lithops import multiprocessing as mp


# import multiprocessing as mp


def work(num):
    global param1, param2
    return param1, param2


def initializer_function(arg1, arg2):
    global param1, param2
    param1 = arg1
    param2 = arg2


# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger(mp.__name__).setLevel(logging.DEBUG)


with mp.Pool(initializer=initializer_function, initargs=('important global arg', 123456)) as p:
    res = p.map(work, [0] * 3)
    print(res)
