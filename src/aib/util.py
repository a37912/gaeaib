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
def get_threads(board, page=0, fmt_name="page"):

  _fmt = "thread_" + fmt_name
  if _fmt in globals():
    fmt = globals()[_fmt]
  else:
    fmt = thread_plain

  threads = Board.load(board)
  threads = threads[THREAD_PER_PAGE*page:THREAD_PER_PAGE*(page+1)]
  logging.info("threadlist in %r : %r" % (board, threads))

  # grab data from cache
  data =  Thread.load_list(threads, board)

  return [ fmt(num,th) for num,th in data if th ]

def thread_plain(num,thread):
  content = thread.get("posts")

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
    "subject" : thread.get("subject"),
  }


def thread_page(num,thread):
  content = thread.get("posts")

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
      "subject" : thread.get("subject"),
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


SUBJECT_MAX = 25
## Helper: saves post to thread
#
# @param request - request object
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
    thread_db = Thread.create(thread, board)
    thread_db.posts = []
    thread_db.subject = data.get("subject")[:SUBJECT_MAX]
  else:
    thread = int(thread)
    #if thread not in board_db.thread:
    #  raise NotFound()

    if thread in board_db.thread and not data.get("sage"):
      board_db.thread.remove(thread)

    thread_db = Thread.load(thread, board)

    if not thread_db:
      raise NotFound()

  if not data.get("sage"):
    board_db.thread.insert(0, thread)

  board_db.thread = board_db.thread[:THREAD_PER_PAGE*BOARD_PAGES]

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

  thread_db.posts.append(data)

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
  post = None #memcache.get(key)

  if post != None:
    logging.info("cache hit")
    return post

  thq = Thread.all()
  thq.ancestor( db.Key.from_path("Board", board))
  thq.filter("post_numbers", num)

  thread = thq.get()

  if not thread:
    return 

  [post] = [p for p in thread.posts if p.get('post') == num]

  memcache.set(key, post)

  return post

def delete_post(board,thread_num,post_num,rape_msg):

  th = Thread.get(db.Key.from_path(
      "Board", board, 
      "Thread", thread_num
      ))

  [post] = [p for p in th.posts if p.get('post') == post_num]
  logging.info("found: %r" % post)

  key = post.get("key")
  if key:
    post.pop("key", None)
    post.pop("image", None)
    info = blobstore.BlobInfo.get(
      blobstore.BlobKey(key))
    info.delete()
    
    try:
      th.images.remove(post.get("key"))
    except:
      pass
    
    logging.info("removed image %r" % post)
    
  else:
    post['text'] = 'Fuuuuuu'       
    post['rainbow_html'] = u'<b>' + rape_msg + '</b>'


  th.put()
  Cache.delete(
    (
      dict(Board=board, Thread=thread_num),
      dict(Board=board)
      )
    )
  
  key = "posts-%s-%d" %(board, thread_num)
  memcache.set(key, th.posts)
  return


