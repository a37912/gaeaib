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
def get_threads(board, fmt_name="page"):

  _fmt = "thread_" + fmt_name
  if _fmt in globals():
    fmt = globals()[_fmt]
  else:
    fmt = thread_plain

  threads = Board.load(board)
  logging.info("threadlist in %r : %r" % (board, threads))

  # grab data from cache
  data =  Thread.load_list(threads, board)

  return [ fmt(num,th) for num,th in data if th ]

def thread_plain(num,content):
  if len(content) > REPLIES_MAIN+1:
    _content = [content[0]]
    _content.extend( content[-REPLIES_MAIN:] )
    omitt = len(content) - REPLIES_MAIN - 1
  else:
    _content = content
    omitt = 0

  for post in _content:
    post.pop("rainbow_html")

  return {
    "posts" : _content,
    "skip" : omitt,
  }


def thread_page(num,content):
  if len(content) > REPLIES_MAIN+1:
    end = content[-REPLIES_MAIN:]
    omitt = len(content) - REPLIES_MAIN - 1
  else:
    end = content[1:]
    omitt = 0
      
  return {
      'op' : content[0],
      'posts' : end,
      'id' : int(num),
      "skipmsg" : "%d omitted" % omitt if omitt else None,
      "skip" : omitt,
  }

def option_saem(request, data):
  if data.get('name') != 'SAEM':
    return

  rb = rainbow.make_rainbow(data)
  data['rainbow'] = rb
  data['rainbow_html'] = rainbow.rainbow(rb)


def option_useragent(request, data):
  from werkzeug.useragents import UserAgent
  ua = UserAgent(request.environ)
  data['agent'] = "%s / %s" %(ua.platform, ua.browser)

## Helper: saves post to thread
#
# @param data - valid cleaned data from form
# @param board - string board name
# @param thread - thread id where to post or "new"
def save_post(request, data, board, thread):

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
    #if thread not in board_db.thread:
    #  raise NotFound()

    if thread in board_db.thread:
      board_db.thread.remove(thread)
    posts = Thread.load(thread, board)

    if not posts:
      raise NotFound()

  board_db.thread.insert(0, thread)
  board_db.thread = board_db.thread[:THREAD_PER_PAGE]

  rb = rainbow.make_rainbow(request.remote_addr, board, thread)
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

  for fname in board_options.get(board, []):
    func = globals().get('option_'+fname)

    if func:
      func(request, data)

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

  memcache.set("post-%s-%d" %(board, board_db.counter), data)

  return board_db.counter, thread

  #key = "update-thread-%s-%d" % (board, thread)
  #if not new:
  #  channel.send_message(key, dumps(data))


def get_post(board, num):
  key = "post-%(board)s-%(num)d" % {"board":board, "num":num}
  post = memcache.get(key)

  if post != None:
    logging.info("cache hit")
    return post

  thq = Thread.all()
  thq.filter("post_numbers", num)

  thread = thq.get()

  if not thread:
    return 

  [post] = [p for p in thread.posts if p.get('post') == num]

  memcache.set(key, post)

  return post
