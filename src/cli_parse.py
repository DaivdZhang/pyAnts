import argparse

parser = argparse.ArgumentParser()
parser.add_argument(type=str, metavar="URL", dest="url")
parser.add_argument('-o', type=str, dest="filename", default=None, help="The name of the downloaded\
                    file")
parser.add_argument('-s', "--splits", metavar='N', type=int, dest="splits", default=1, help="Slice the\
                    file into N parts (default = 1)")
parser.add_argument('-t', "--thread", metavar='N', type=int, dest="thread", default=1, help="Downloadin\
                    g a file uses N threads (default = 1)")
parser.add_argument('-d', "--dir", type=str, dest="path", default='', help="The directory to store the\
                    downloaded file.")

args_ = parser.parse_args()
args_ = [args_.url, args_.splits, args_.thread, args_.path, args_.filename]
