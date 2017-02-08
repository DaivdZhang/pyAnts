import requests
import threading
import queue
import os

__all__ = ["worker"]


_mutex = threading.Lock()


class _Target(object):
    def __init__(self, url, splits, filename=None):
        self.url = url
        self.filename = filename if filename else url.split('/')[-1]
        self.thread_num = splits
        self.content_length = self._get_length()

    def _get_length(self):
        headers = {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.\
                   0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729)"}
        res = requests.get(self.url, headers)
        return int(res.headers['Content-Length'])


def _split(length, num):
    """

    :type length: int
    :type num: int
    :return:
    """
    offset = length//num
    slices = [[_i*offset, _i*offset+offset] for _i in range(num)]
    slices[-1][-1] = ''
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
        _range = q.get()
        headers = _build_headers(_range)
        try:
            res = requests.get(url, headers=headers)
            with _mutex:
                with open(filename, 'rb+') as file:
                    file.seek(_range[0])
                    file.write(res.content)
        except requests.HTTPError:
            q.put(_range)
        finally:
            q.task_done()


def worker(url, splits=2, path=''):
    """

    :type url: str
    :type splits: int
    :type path: str
    :return:
    """
    target = _Target(url, splits)
    filename = path + target.filename
    if not os.path.isfile(path+target.filename):
        with open(filename):
            pass
    print("target size: %.3f MB\n" % (target.content_length/1024/1024))

    work_queue = _create_queue(target.content_length, splits)
    threads = []
    for i in range(splits):
        threads.append(threading.Thread(target=_download, args=(url, filename, work_queue)))
    for t in threads:
        t.setDaemon(True)
        t.start()
    work_queue.join()
    print("%s downloaded! at %s\n" % (target.filename, path))
