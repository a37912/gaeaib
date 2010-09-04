import logging

from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.api import images

#from google.appengine.api import channel
from tipfy import NotFound
import rainbow
from const import *

## Helper: functon to grab last thread list for board
#
# @param board - string board name
def get_threads(board):

  threads = memcache.get("threadlist-%s" % board) or []

  # map list of thread ids to fetch
  ids = map(str,threads)

  # grab data from cache
  data =  memcache.get_multi(ids, "posts-%s-" % board)

  ret = []
  for thread in threads:
    content = data.get(str(thread))

    if not content:
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
        'id' : thread,
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

  # create new thread
  if thread == 'new':
    thread = memcache.incr("posts-%s" % board, initial_value=0)
    thread_clean(board)
    new = True
  else:
    thread = int(thread)
    new = False

  # FIXME: dont allow to post to nonexstand thread
  posts = memcache.get("posts-%s-%d" % (board, thread))
  if not posts:
    posts = []

  if not new and not posts:
    raise NotFound()

  rb = rainbow.make_rainbow(ip, board, thread)
  data['rainbow'] = rb
  data['rainbow_html'] = rainbow.rainbow(rb)

  # FIXME: move to field
  data['name'] = data.get("name") or "Anonymous"

  if new:
    newpost = thread
  else:
    newpost = memcache.incr("posts-%s" % board, initial_value=0)

  # save thread and post number
  data['post'] = newpost
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

  # save to cache
  memcache.set("posts-%s-%d" % (board, thread), posts)
  memcache.set("post-%s-%d" % (board,newpost), data)

  # debug
  key = "posts-%s-%d" % (board, thread)

  logging.info("saved %s" % key)

  if new or not data.get("sage"):
    thread_bump(board, thread)

  return newpost, thread

  #key = "update-thread-%s-%d" % (board, thread)
  #if not new:
  #  channel.send_message(key, dumps(data))

## Helper: bumps thread to the top
#
# @param board - string board name
# @param thread - thread id
#
# @note - can be called at thread creat time
def thread_bump(board, thread):
  threads = memcache.get("threadlist-%s" % board) or []

  if thread in threads:
    threads.remove(thread)

  threads.insert(0, thread)

  memcache.set("threadlist-%s" % board, threads)

## Helper: deletes old threads
#
# @param board - string board nam
# 
# @note called before creating new thread
def thread_clean(board):
  threads = memcache.get("threadlist-%s" % board) or []

  if len(threads) < THREAD_PER_PAGE:
    return

  to_remove = map(str, threads[THREAD_PER_PAGE-1:])
  #memcache.delete_multi(to_remove, key_prefix="posts-%s-" % board)

  memcache.set("threadlist-%s" % board, threads[:THREAD_PER_PAGE-1])


