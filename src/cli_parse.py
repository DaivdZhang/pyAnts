import argparse

parser = argparse.ArgumentParser()
parser.add_argument(type=str, metavar="URL", dest="url")
parser.add_argument('-o', type=str, dest="filename", default=None)
parser.add_argument('-s', "--splits", type=int, dest="splits", default=1)
parser.add_argument('-t', "--thread", type=int, dest="thread", default=1)
parser.add_argument('-d', "--dir", type=str, dest="path", default='')

args_ = parser.parse_args()
args_ = [args_.url, args_.splits, args_.thread, args_.path, args_.filename]
