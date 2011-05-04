# -*- coding: utf-8 -*-
import logging
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response, get_config

from aib.models import Thread, ThreadIndex, Board, BoardCounter, Cache
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

  thq = ThreadIndex.all(keys_only=True)
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
  thq = ThreadIndex.all(keys_only=True)
  thq.filter("post_count", 1)

  if cursor:
    thq.with_cursor(cursor)

  thread_idx = thq.get()

  if not thread_idx:
    logging.info("stop thread clean")
    return

  thread = db.get(thread_idx.parent())

  if thread:

    board = Board.get_by_key_name(thread.board)

    if len(thread.posts) == 1:
      db.delete(thread)
    else:
      logging.error("crap, post count %d, %r" % (len(thread.posts), thread_idx))
  else:
    logging.error("crap, no thread for %r" % thread_idx)

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

  board_c = BoardCounter(key_name=board.key().name())
  board_c.counter = board._entity.get('counter')
  board_c.put()

  threads = Thread.load_list(board.thread, board.key().name())

  board.thread = [th for (th,data) in threads if data]
  fill_board(board)

  board.put()
  Cache.remove("board", board.key().name())

  deferred.defer(do_clean_board, thq.cursor())

TMAX = get_config('aib.ib', 'thread_per_page') * get_config('aib.ib','board_pages')

def fill_board(board):
  logging.info("fill board %s" % board.code)
  threads = Thread.all()
  threads.filter("board", board.code)
  threads.order("-id")

  for thread in threads.fetch(TMAX):

    logging.info("here is thread %r" % thread)

    if len(board.thread) >= TMAX:
      return

    if thread.id not in board.thread:
      logging.info("add now")
      board.thread.append(  thread.id )

