# -*- coding: utf-8 -*-
import logging
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response, get_config

from aib.models import Thread, ThreadIndex, Board, Cache
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
  thq.filter("post_count <", 5)

  if cursor:
    thq.with_cursor(cursor)

  thread_idx = thq.get()

  if not thread_idx:
    logging.info("stop thread clean")
    return

  thread = db.get(thread_idx.parent())

  board = Board.get_by_key_name(thread.board)

  if len(thread.posts) < 5: # FIXME: magic number
    db.delete(thread)
    logging.info("purged thread")
  else:
    assert False, "oops invalid post count"

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
  Cache.remove("board", board.key().name())

  deferred.defer(do_clean_board, thq.cursor())

TMAX = get_config('aib.ib', 'thread_per_page') * get_config('aib.ib','board_pages')

def fill_board(board):
  threads = Thread.all(keys_only=True)
  threads.filter("board", board)
  threads.order("-__key__")

  for thread in threads.fetch(TMAX):

    if len(board.thread) >= TMAX:
      return

    if thread.id() not in board.thread:
      board.thread.append(  thread.id() )

