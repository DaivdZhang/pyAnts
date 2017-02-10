import requests
import threading
import queue
import os
from cli_parse import args as args_

__all__ = ["worker"]


_mutex = threading.Lock()


class _Target(object):
    def __init__(self, url, splits, filename=None):
        self.url = url
        self.filename = filename if filename else url.split('/')[-1]
        self.thread_num = splits
        self.content_length = self._get_length()

    def _get_length(self):
        try:
            res = requests.head(self.url)
            return int(res.headers['Content-Length'])
        except requests.HTTPError as e:
            print(e)
            exit(1)


def _split(length, num):
    """

    :type length: int
    :type num: int
    :return:
    """
    offset = length//num
    slices = [[_i*offset, _i*offset+offset] for _i in range(num)]
    slices[-1][-1] = length - 1
    return slices


def _build_headers(range_):
    """

    :type range_: list
    :return:
    """
    headers = {"accept-encoding": '*',
               "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; \
                             .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.\
                             30729)"}
    headers.update({"range": "Bytes={0}-{1}".format(range_[0], range_[1])})
    return headers


def _create_queue(length, num):
    """

    :type length: int
    :type num: int
    :return:
    """
    s = _split(length, num)
    q = queue.Queue()
    for _ in s:
        q.put(_)
    return q


def _download(url, filename, q):
    """

    :type url: str
    :type filename: str
    :type q: queue.Queue
    :return:
    """
    while not q.empty():
        range_ = q.get()
        headers = _build_headers(range_)
        try:
            res = requests.get(url, headers=headers)
            if len(res.content) == range_[1] - range_[0] + 1:
                with _mutex:
                    with open(filename, 'rb+') as file:
                        file.seek(range_[0])
                        file.write(res.content)
            else:
                q.put(range_)
        except requests.HTTPError:
            q.put(range_)
        finally:
            q.task_done()


def worker(target, path=None):
    """

    :type target: _Target
    :type path: str
    :return:
    """
    f1 = path + target.filename
    if not os.path.isfile(path+target.filename):
        with open(f1, 'wb'):
            pass

    work_queue = _create_queue(target.content_length, target.thread_num)
    threads = []
    for i in range(target.thread_num):
        threads.append(threading.Thread(target=_download, args=(target.url, f1, work_queue)))
    for t in threads:
        t.setDaemon(True)
        t.start()
    work_queue.join()

if __name__ == "__main__":
    _url, _splits, _path, _filename = args_.url, args_.splits, args_.path, args_.filename
    _target = _Target(_url, _splits, _filename)

    print("target size: %.3f MB\n" % (_target.content_length / 1024 / 1024))
    worker(_target, _path)
    print("%s downloaded! at %s\n" % (_target.filename, _path))
