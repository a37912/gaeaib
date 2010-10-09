import logging
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response

from aib.models import Thread, Board, Cache

class CleanBlob(RequestHandler):
  def get(self):
    do_clean()
    return Response("hello")

def do_clean(cursor=None):

  bq = BlobInfo.all()

  if cursor:
    bq.with_cursor(cursor)

  blob = bq.get()

  if not blob:
    return

  key = str(blob.key())

  thq = Thread.all(keys_only=True)
  thq.filter("images", key)

  th = thq.get()

  if th:
    logging.info("thread: %r" % th)
  else:
    logging.info("no thread for image %r" % key)

    blob.delete()

  deferred.defer(do_clean, bq.cursor(), _countdown=30)

class CleanThread(RequestHandler):
  def get(self):
    do_clean_thread()
    return Response("yarr")

def do_clean_thread(cursor=None):
  thq = Thread.all(keys_only=True)

  if cursor:
    thq.with_cursor(cursor)

  thread = thq.get()

  if not thread:
    logging.info("stop thread clean")
    return

  board = Board.get(thread.parent())

  if not board or thread.id() not in board.thread:
    db.delete(thread)
    logging.info("purged thread")

  deferred.defer(do_clean_thread, thq.cursor(), _countdown=10)


class CleanCache(RequestHandler):
  def get(self):
    do_clean_cache()
    return Response("yarr nom-nom")

def do_clean_cache(cursor=None):
  cacheq = Cache.all(keys_only=True)

  if cursor:
    cacheq.with_cursor(cursor)

  cache = cacheq.get()

  if not cache:
    return

  if cache.parent().kind() == 'Board':
    db.delete(cache)

  deferred.defer(do_clean_cache, cacheq.cursor(), _countdown=2)



