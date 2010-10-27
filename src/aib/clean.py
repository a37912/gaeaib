import logging
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response

from aib.models import Thread, Board, Cache
from aib.const import *
#import restore

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
  thq = Thread.all()

  if cursor:
    thq.with_cursor(cursor)

  thread = thq.get()

  if not thread:
    logging.info("stop thread clean")
    return

  board = Board.get(thread.parent_key())

  if len(thread.posts) < 5: # FIXME: magic number
    db.delete(thread)
    logging.info("purged thread")

  deferred.defer(do_clean_thread, thq.cursor())


class CleanCache(RequestHandler):
  def get(self):
    do_clean_cache()
    return Response("yarr nom-nom")

def do_clean_cache(cursor=None):
  cacheq = Cache.all()

  if cursor:
    cacheq.with_cursor(cursor)

  cache = cacheq.get()

  if not cache:
    logging.info("stop cache clean")
    return

  if cache.parent_key().kind() == 'Board':
    db.delete(cache)
  #elif cache.parent_key().kind() == 'Thread':
  #  restore.from_cache(cache)

  deferred.defer(do_clean_cache, cacheq.cursor())


class CleanBoard(RequestHandler):
  def get(self):
    do_clean_board()
    return Response("yarr")

def do_clean_board(cursor=None):
  thq = Board.all()

  if cursor:
    thq.with_cursor(cursor)

  board = thq.get()

  if not board:
    logging.info("stop board clean")
    return

  threads = Thread.load_list(board.thread, board.key().name())

  board.thread = [th for (th,data) in threads if data]
  fill_board(board)

  board.put()

  deferred.defer(do_clean_board, thq.cursor())

TMAX =THREAD_PER_PAGE*BOARD_PAGES
def fill_board(board):
  threads = Thread.all(keys_only=True)
  threads.ancestor(board)
  threads.order("-__key__")

  for thread in threads.fetch(TMAX):

    if len(board.thread) >= TMAX:
      return

    if thread.id() not in board.thread:
      board.thread.append(  thread.id() )

