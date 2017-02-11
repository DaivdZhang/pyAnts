import requests
import threading
import queue
import os
import time
from cli_parse import args_
from progressbar import progressbar, WIDGETS


__all__ = ["worker"]

_mutex = threading.Lock()


class _Target(object):
    def __init__(self, url, splits, filename=None, thread=1):
        """

        :type url: str
            url to download

        :type splits: int
            slice target file to this num

        :type filename: str
            using this name to save file

        :type thread: int
            the num of threads to download
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
        every split's range_

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
        _.append(3)  # retry = 3
        q.put(_)
    return q


def _save(filename, content, offset):
    """

    :type filename: str
        refer to _Target.filename

    :type content: bytes
        content of target

    :type offset: int
        location to write content

    :rtype:
    """
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
        store splits

    :type buffer_size: int
    """
    content = b''
    while not q.empty():
        range_ = q.get()
        retry = range_.pop()
        if retry == 0:
            raise requests.HTTPError

        headers = _build_headers(range_)
        try:
            res = requests.get(url, headers=headers, stream=True)
            for i in res.iter_content(chunk_size=1024):
                content += i
                if len(content) > buffer_size:
                    _save(filename, content, range_[0])
                    range_[0] += len(content)
            _save(filename, content, range_[0])
        except requests.HTTPError:
            range_.append(retry - 1)
            q.put(range_)
        finally:
            content = b''
            q.task_done()


def run(target, q, path=None):
    """

    :type target: _Target

    :type q: queue.Queue
        store splits

    :type path: str
        dir to save file
    """
    f1 = path + target.filename
    if not os.path.isfile(path+target.filename):
        with open(f1, 'wb'):
            pass

    threads = [threading.Thread(target=progressbar, args=(f1, target.content_length, WIDGETS))]
    for i in range(target.thread):
        t = threading.Thread(target=_download, args=(target.url, f1, q))
        threads.append(t)
    for t in threads:
        t.daemon = True
        t.start()

if __name__ == "__main__":
    _url, _splits, _thread, _path, _filename = args_

    if _thread > 4:  # avoid ddos server
        raise ValueError("too many threads!\n DO NOT SURPASS 4 THREADS!\n")

    _target = _Target(_url, _splits, _filename, _thread)
    _work_queue = _create_queue(_target.content_length, _target.splits)

    print("filename: %s" % _target.filename)
    print("target size: %.3f MB" % (_target.content_length/1024/1024))
    run(_target, _work_queue, _path)
    _work_queue.join()
    time.sleep(1)
    if _path == '':
        _path = os.path.abspath('.')
    print("\ndownloaded! at %s" % _path)
