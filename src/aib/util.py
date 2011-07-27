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
from google.appengine.api import prospective_search as  matcher

from google.appengine.api import channel
from django.utils.simplejson import dumps
from tipfy import NotFound, get_config
import rainbow
from models import Board, BoardCounter, Thread, ThreadIndex, Cache
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


  threads = []

  board_db = Board.get_by_key_name(board)
  if board_db:
    threads = board_db.linked

    if not threads:
      threads = [ (board, th) for th in board_db.thread]

  per_page = get_config('aib.ib', 'thread_per_page')
  threads = threads[per_page*page:per_page*(page+1)]
  logging.info("threadlist in %r : %r" % (board, threads))

  # grab data from cache
  data =  Thread.load_list(threads)

  return [ fmt(th) for th in data if th ]

def thread_plain(thread):

  return {
    "posts" : thread.posts,
    "skip" : thread.skip,
    "subject" : thread.subject,
  }


def thread_page(thread):
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


def option_trollsign(request, data):

  from random import randint
  if not randint(0, 4):
      data['typ'] = 'modpost'
      data['name'] = 'Winry'


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
def save_post(request, data, board, thread, ip):

  def board_increment():
    board_db = BoardCounter.get_by_key_name(board)

    if not board_db:
      board_db = BoardCounter(key_name = board, thread = [])

    board_db.counter += 1
    board_db.put()

    return board_db.counter

  postid = db.run_in_transaction(board_increment,)

  # create new thread
  new = False
  if thread == 'new':
    new = True
    if data.get("sage"):
      raise NotFound() # FIXME: move to form

    thread = postid
    posts = []
    thread_db = Thread.create(thread, board)
    thread_db.posts = []
    thread_db.subject = data.get("subject")[:SUBJECT_MAX]
  else:
    thread = int(thread)

    thread_db = Thread.load(thread, board)

    if not thread_db:
      raise NotFound()

  per_page = get_config('aib.ib', 'thread_per_page')
  pages = get_config('aib.ib', 'board_pages')

  rb = rainbow.make_rainbow(ip, board, thread)
  data['rainbow'] = rb
  data['overlay'] = board in OVER
  
  data['text_html'] = markup(
        board=board, postid=postid,
        data=escape(data.get('text')),
  )

  # save thread and post number
  data['post'] = postid
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
  thread_db.put()

  r = Render(thread=thread_db)
  r.post_html = ''
  r.add(data, new) # WARNING: side effect on data
  r.save()

  deferred.defer(save_post_defer,
      thread_db.boards, thread,
      r.post_html, data.get('text_html'),
      postid,
      len(thread_db.posts),
      data.get("sage"),
  )

  # send notify
  thread_flag = 'new' if new else 'sage' if data.get("sage") else 'bump'
  match_msg = Post(board = board, thread = thread, thread_flag = thread_flag)
  match_msg.data = dict(
    board = board,
    thread = thread,
    html = r.post_html,
    text = data.get('text'),
    last = postid,
    count = len(thread_db.posts),
    evt = 'newpost'
  )

  matcher.match(match_msg, topic='post',
      result_task_queue='postnotify')

  return postid, thread


def save_post_defer(boards, thread, html, text_html, postid, count, sage):

  index_regen(Thread.gen_key(thread, boards[0]))

  rss.add(boards[0], thread, postid, text_html)

  if not sage:
    bump(boards, thread)

  # TODO: generate last 5 messages here
  # thread_snippet(board, thread)

def bump(boards, thread):

  board_db = Board.get_by_key_name(boards)
  main = boards[0]

  for x,(name,board) in enumerate(zip(boards,board_db)):
    if not board:
      board = Board(key_name=name)
      board.linked = []
      board_db[x] = board

    if not board.linked and board.thread:
      board.linked = [
        (board.code, th)
        for th in
        board.thread
      ]

    if (main,thread) in board.linked:
      board.linked.remove((main,thread))

    board.linked.insert(0, (main,thread))

  main_db = board_db[0]
  if thread in main_db.thread:
    main_db.thread.remove(thread)

  main_db.thread.insert(0, thread)

  db.put(board_db)


def index_regen(tkey):
  index = ThreadIndex(parent=tkey, key_name="idx")
  index.put()


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

from .matcher import Post
