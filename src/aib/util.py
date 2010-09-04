import logging

from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.api import images

#from google.appengine.api import channel
from tipfy import NotFound
import rainbow
from const import *
from models import Board, Thread, Cache

## Helper: functon to grab last thread list for board
#
# @param board - string board name
def get_threads(board):

  threads = Board.load(board)
  logging.info("threadlist in %r : %r" % (board, threads))

  # grab data from cache
  data =  Thread.load_list(threads, board)

  ret = []
  for num,content in data:

    if not content:
      logging.info("skip %d" % num)
      continue

    if len(content) > REPLIES_MAIN+1:
      end = content[-REPLIES_MAIN:]
      omitt = len(content) - REPLIES_MAIN - 1
    else:
      end = content[1:]
      omitt = 0
      
    thread_data = {
        'op' : content[0],
        'posts' : end,
        'id' : int(num),
        "skipmsg" : "%d omitted" % omitt if omitt else None,
      }

    ret.append( thread_data )

  return ret

## Helper: saves post to thread
#
# @param data - valid cleaned data from form
# @param board - string board name
# @param thread - thread id where to post or "new"
def save_post(data, board, thread, ip):

  board_db = Board.get_by_key_name(board)

  if not board_db:
    board_db = Board(key_name = board, thread = [])

  board_db.counter += 1

  # create new thread
  if thread == 'new':

    if data.get("sage"):
      raise NotFound() # FIXME: move to form

    thread = board_db.counter
    posts = []
  else:
    thread = int(thread)
    if thread not in board_db.thread:
      raise NotFound()

    board_db.thread.remove(thread)
    posts = Thread.load(thread, board)

    if not posts:
      raise NotFound()

  board_db.thread.insert(0, thread)
  board_db.thread = board_db.thread[:THREAD_PER_PAGE]

  rb = rainbow.make_rainbow(ip, board, thread)
  data['rainbow'] = rb
  data['rainbow_html'] = rainbow.rainbow(rb)

  # FIXME: move to field
  data['name'] = data.get("name") or "Anonymous"

  # save thread and post number
  data['post'] = board_db.counter
  data['thread'] = thread
  now = datetime.now()
  data['time'] = now.strftime("%Y-%m-%d, %H:%M")
  data['timestamp'] = int(now.strftime("%s"))

  img_key = data.get("key")

  if img_key:
    blob_key = blobstore.BlobKey(img_key)
    blob_info = blobstore.BlobInfo.get(blob_key)

    data['image'] = {
        "size" : blob_info.size,
        "content_type" : blob_info.content_type,
        "full" : images.get_serving_url(img_key),
        "thumb" : images.get_serving_url(img_key, 200),
    }

  posts.append(data)

  thread_db = Thread.save(thread, board, posts)

  db.put( (thread_db, board_db))
  Cache.delete(
    (
      dict(Board=board, Thread=thread),
      dict(Board=board)
    )
  )
  memcache.set("threadlist-%s" % board, board_db.thread)

  memcache.set_multi(
      dict( 
        [
          (str(p.get("post")), p) 
          for p in posts
        ] 
      ),
      key_prefix = "post-%s" % board,
  )

  return board_db.counter, thread

  #key = "update-thread-%s-%d" % (board, thread)
  #if not new:
  #  channel.send_message(key, dumps(data))

