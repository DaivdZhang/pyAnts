import requests
import threading
import queue
import os
from cli_parse import args_

__all__ = ["worker"]


_mutex = threading.Lock()


class _Target(object):
    def __init__(self, url, splits, filename=None, thread=1):
        """

        :type url: str
            url to download

        :type splits: int
            the num of threads to download

        :type filename: str
            using this name to save file
        """
        self.url = url
        self.filename = filename if filename else url.split('/')[-1]
        self.splits = splits
        self.thread = thread
        self.content_length = self._get_length()

    def _get_length(self):
        """

        :rtype: int
        """
        try:
            res = requests.head(self.url)
            return int(res.headers['Content-Length'])
        except requests.HTTPError as e:
            print(e)
            exit(1)


def _split(length, splits):
    """

    :type length: int
        the content length of target

    :type splits: int
        slice num

    :rtype: list
    """
    offset = length//splits
    slices = [[i*offset, i*offset+offset] for i in range(splits)]
    slices[-1][-1] = length - 1
    return slices


def _build_headers(range_):
    """

    :type range_: list
    :rtype: dict
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
        refer to _Target.content_length

    :type num: int
        thread num

    :rtype: queue.Queue
    """
    s = _split(length, num)
    q = queue.Queue()
    for _ in s:
        q.put(_)
    return q


def _save(filename, content, offset):
    with _mutex:
        with open(filename, 'rb+') as file:
            file.seek(offset)
            file.write(content)


def _download(url, filename, q, buffer_size=8388608):
    """

    :type url: str
        refer to _Target.url

    :type filename: str
        refer to _Target.filename

    :type q: queue.Queue
    """
    while not q.empty():
        range_ = q.get()
        headers = _build_headers(range_)
        content = b''
        try:
            res = requests.get(url, headers=headers, stream=True)
            for i in res.iter_content(chunk_size=1024):
                content += i
                if len(content) > buffer_size:
                    _save(filename, content, range_[0])
                    range_[0] += len(content)
                    content = b''
            _save(filename, content, range_[0])
        except requests.HTTPError:
            q.put(range_)
        finally:
            q.task_done()


def worker(target, path=None):
    """

    :type target: _Target
    :type path: str
        dir to save file
    """
    f1 = path + target.filename
    if not os.path.isfile(path+target.filename):
        with open(f1, 'wb'):
            pass

    work_queue = _create_queue(target.content_length, target.splits)
    threads = []
    for i in range(target.thread):
        threads.append(threading.Thread(target=_download, args=(target.url, f1, work_queue)))
    for t in threads:
        t.daemon = True
        t.start()
    work_queue.join()

if __name__ == "__main__":
    _url, _splits, _thread, _path, _filename = args_

    if _thread > 4:  # avoid ddos server
        raise ValueError("too many threads!\n DO NOT SURPASS 4 THREADS!\n")

    _target = _Target(_url, _splits, _filename, _thread)

    print("target size: %.3f MB" % (_target.content_length/1024/1024))
    worker(_target, _path)
    print("%s downloaded! at %s" % (_target.filename, _path))
