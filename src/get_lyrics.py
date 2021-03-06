'''
Main module: provide simple, ready-to-use functions
to get lyrics
'''
import functools
import multiprocessing
from multiprocessing import dummy as _multiprocdummy
import Queue

import pluginsystem

_multiproc = multiprocessing  # "back-up" of the module, see set_parallel


def set_parallel(method):
    '''
    Allows to choose between process based and threading based concurrency

    :arg method: can be 'process' or 'thread'
    :raises ValueError: If an invalid argument is given
    '''
    if method == 'process':
        globals()['multiprocessing'] = _multiproc
    elif method == 'thread':
        globals()['multiprocessing'] = _multiprocdummy
    else:
        raise ValueError('Supported method are "thread" and "multiprocessing"')


def get_ready_retrievers(artist=None, album=None, title=None, otherinfo=None, \
        request=(), timeout=-1, filename=None):
    '''
    .. note :: this is not meant to be used by the casual user. Use it if
      you are a developer or if you really do what you're doing

    This function will return an iterator over functions that take no arguments
    and will try to get data (that is, retrievers with arguments filled in)

    :param otherinfo: Other metadata, not worthing a function parameter
    :type otherinfo: dict
    :param request: all needed metadata. If empty, all will be searched
    :type request: tuple
    :param timeout: currently not supported
    :rtype: iterator
    '''
    song_metadata = otherinfo if otherinfo else {}
    if artist:
        song_metadata['artist'] = artist
    if album:
        song_metadata['album'] = album
    if title:
        song_metadata['title'] = title

    options = {}
    options['searching'] = request or ('lyrics', 'coverart')

    for name, plugin in pluginsystem.get_plugins().items():
        yield name, functools.partial(plugin.get_data, song_metadata, options)
    return


def _get_analyzer(name):
    '''
    Given a name, return an analyzer function(request, results, response)
    :type name: string
    :raises ValueError: non valid name
    '''
    #TODO: more flexible way (egg-based?)
    if name == 'first_match':
        return _first_match
    else:
        raise ValueError('%s is not a valid analyzer')


def _first_match(request, results, response):
    '''
    This analyzer checks only for the first result that satisfies the request.

    .. todo :: If resultA+resultB satisfies request, they should be returned
    '''
    while True:
        name, status, res = results.get()
        if status != 'ok':
            pass
        #request is satisfied
        elif False not in (x in res.keys() for x in request):
            response.put((name, res))
            return
        else:
            print 'nooo', res, request, [x in res for x in request]


def get_lyrics(artist=None, album=None, title=None, otherinfo=None, \
        request=(), timeout=None, filename=None, analyzer='first_match'):
    '''
    .. todo :: analyzers should have a way of keeping a "best-for-now" result

    Simply get lyrics

    :param otherinfo: Other metadata, not worthing a function parameter
    :type otherinfo: dict
    :param request: all needed metadata. If empty, all will be searched
    :type request: tuple
    :param timeout: timeout in seconds, None for no timeout
    :rtype: dict
    '''
    results = multiprocessing.Queue()
    response = multiprocessing.Queue()
    #this is a trick; finished will be filled with useless value, one per
    #process. When a process exits, it will pop. So, finished.join() is
    #equivalent to joining every process; the advantage is that it can be done
    #in a separate process
    finished = multiprocessing.JoinableQueue()

    analyzer = multiprocessing.Process(target=_get_analyzer(analyzer),
            args=(request, results, response))
    analyzer.name = 'analyzer'
    analyzer.daemon = True
    analyzer.start()

    def retriever_wrapper(name, retriever, results, finished):
        '''Call a retriever, handle its results'''
        def wrapped():
            finished.get()
            try:
                res = retriever()
            except Exception, exc:
                results.put((name, 'error', exc))
            else:
                results.put((name, 'ok', res))
            finally:
                finished.task_done()
        return wrapped

    processes = []
    for name, retriever in get_ready_retrievers(artist, album, title, \
            otherinfo, request, timeout, filename):
        finished.put(True)
        wrapped_retriever = retriever_wrapper(
                name, retriever, results, finished)
        p = multiprocessing.Process(target=wrapped_retriever)
        processes.append(p)
        p.daemon = True
        p.name = name
        p.start()

    def waiter(q):
        '''wait for every retriever to join, then unlock main flow'''
        finished.join()  # when every process has done
        response.put('finished')
    w = multiprocessing.Process(target=waiter, args=(finished,))
    w.daemon = True
    w.start()

    try:
        res = response.get(block=True, timeout=timeout)
    except Queue.Empty:
        return (None, None)
    else:
        if res == 'finished':
            return (None, None)
        return res
