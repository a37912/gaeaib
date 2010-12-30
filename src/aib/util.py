# -*- coding: utf-8 -*-
import logging
from time import time

from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import deferred

from google.appengine.api import channel
from django.utils.simplejson import dumps
from tipfy import NotFound, get_config
import rainbow
from models import Board, Thread, ThreadIndex, Cache
from render import Render
import rss
from mark import markup
from cgi import escape

## Helper: functon to grab last thread list for board
#
# @param board - string board name
def get_threads(board, page=0, fmt_name="page"):

  _fmt = "thread_" + fmt_name
  if _fmt in globals():
    fmt = globals()[_fmt]
  else:
    fmt = thread_plain

  per_page = get_config('aib.ib', 'thread_per_page')

  threads = Board.load(board) or []
  threads = threads[per_page*page:per_page*(page+1)]
  logging.info("threadlist in %r : %r" % (board, threads))

  # grab data from cache
  data =  Thread.load_list(threads, board)

  return [ fmt(num,th) for num,th in data if th ]

def thread_plain(num,thread):

  return {
    "posts" : thread.posts,
    "skip" : thread.skip,
    "subject" : thread.subject,
  }


def thread_page(num,thread):
  return thread

def option_saem(request, data):
  if data.get('name') != 'SAEM':
    return

  rb = rainbow.make_rainbow(data.get("rainbow"), data.get("post"))
  data['rainbow'] = rb


def option_useragent(request, data):
  from werkzeug.useragents import UserAgent
  ua = UserAgent(request.environ)

  if ua.platform or ua.cpu or ua.browser:
    cpu = "@" + ua.cpu if ua.cpu else ""
    data['agent'] = "%s%s / %s" %(ua.platform, cpu, ua.browser)
  else:
    data['agent'] = 'gays heaven'

def option_modsign(request, data):
  mods = get_config("aib.ib", "mod_name")

  user = users.get_current_user()
  if not user or user.email() not in mods:
    return

  if data.get('name') == mods.get(user.email()):
    data['typ'] = 'modpost'


SUBJECT_MAX = 25
OPTIONS = get_config("aib.util", "options")
OVER = get_config("aib", "overlay")
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
  new = False
  if thread == 'new':
    new = True
    if data.get("sage"):
      raise NotFound() # FIXME: move to form

    thread = board_db.counter
    posts = []
    thread_db = Thread.create(thread, board)
    thread_db.posts = []
    thread_db.subject = data.get("subject")[:SUBJECT_MAX]
  else:
    thread = int(thread)

    if thread in board_db.thread and not data.get("sage"):
      board_db.thread.remove(thread)

    thread_db = Thread.load(thread, board)

    if not thread_db:
      raise NotFound()

  if not data.get("sage"):
    board_db.thread.insert(0, thread)

  per_page = get_config('aib.ib', 'thread_per_page')
  pages = get_config('aib.ib', 'board_pages')

  board_db.thread = board_db.thread[:per_page*pages]

  rb = rainbow.make_rainbow(request.remote_addr, board, thread)
  data['rainbow'] = rb
  data['overlay'] = board in OVER
  
  data['text_html'] = markup(
        board=board, postid=board_db.counter,
        data=escape(data.get('text')),
  )

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

  for fname in OPTIONS.get(board, []):
    func = globals().get('option_'+fname)

    if func:
      func(request, data)

  thread_db.posts.append(data)

  db.put( (thread_db, board_db))
  Cache.remove("board", board)

  r = Render(thread=thread_db)
  r.add(data, new)
  r.save()

  deferred.defer(rss.add, board, thread, board_db.counter, 
	data.get("text_html") )
  deferred.defer(index_regen, thread_db.key())

  if not new:
    deferred.defer(
        watchers_post_notify,
        board, thread, r.post_html, 
        len(thread_db.posts), board_db.counter
    )

  return board_db.counter, thread

def index_regen(tkey):
  index = ThreadIndex(parent=tkey, key_name="idx")
  index.put()

def watchers_post_notify(board, thread, html, count, last):
  key = "upt-%s-%d" % (board, thread)
  send = { 
      "html" : html, 
      "evt" : "newpost" ,
      "count" : count,
      "last" : last,
  }

  watchers = memcache.get(key) or []
  watchers_send(
      watchers_clean(watchers),
      key,
      send
  )

def watchers_send(watchers, key, data):
  for wtime,person in watchers:
    try:
      channel.send_message(person+key, dumps(data))
    except channel.Error:
      pass


WATCHERS_MAX = get_config('aib.util', 'watches_max')
WATCHER_TIME = get_config('aib.util', 'watch_time')

def watchers_clean(watchers, exclude=None):
  now = time()
  nwatchers = []

  for wtime,person_check in watchers[:WATCHERS_MAX]:
    if (now - wtime) > WATCHER_TIME:
      continue

    if person_check == exclude:
      continue

    nwatchers.append((wtime, person_check))

  return nwatchers

POST_QUOTA = get_config('aib.antiwipe', 'quota')
def post_level(ip):
  qkey = "ip-%s" % ip
  post_quota = memcache.get(qkey) or 0

  if post_quota >= POST_QUOTA:
    quota_level = "err"
  elif post_quota >= (POST_QUOTA - (POST_QUOTA/3)):
    quota_level = "preerr"
  elif post_quota >= (POST_QUOTA/2):
    quota_level = "warn"
  else:
    quota_level = "ok"

  return quota_level

def get_post(board, num):
  key = "post-%(board)s-%(num)d" % {"board":board, "num":num}
  post = memcache.get(key)

  if post != None:
    logging.info("cache hit")
    return post

  thq = ThreadIndex.all(keys_only=True)
  thq.filter("board", board)
  thq.filter("post_numbers", num)

  thread_idx = thq.get()

  if not thread_idx:
    return 

  thread = db.get(thread_idx.parent())

  [post] = [p for p in thread.posts if p.get('post') == num]

  memcache.set(key, post)

  return post

## Helper: deletes image/post from the thread
#
# @param board - string board name
# @param thread_num - thread id
# @param post_num - post id 
# @param rape_msg - string replacement of the rainbow
# @return True if it's a text deletion else otherwise
def delete_post(board, thread_num, post_num, rape_msg):

  last_deletion = False
  th = Thread.load(thread_num, board)

  [post] = [p for p in th.posts if p.get('post') == post_num]
  logging.info("found: %r" % post)

  key = post.get("key")
  if key:
    post.pop("key", None)
    post.pop("image", None)
    info = blobstore.BlobInfo.get(
      blobstore.BlobKey(key))

    if info:
      info.delete()
    
    try:
      th.images.remove(post.get("key"))
    except:
      pass
    
    logging.info("removed image %r" % post)
    
  else:
    last_deletion = True
    post['text'] = 'Fuuuuuu'       
    post['text_html'] = 'Fuuuuuu'       
    post['rainbow_html'] = u'<b>' + rape_msg + '</b>'

  th.put()
  Cache.remove("board", board)

  r = Render(thread=th)
  #kind of shit:
  r.create(th.posts[0])
  for a_post in th.posts[1:]:
    r.append(a_post)
  r.save()
  
  return last_deletion
