# -*- coding: utf-8 -*-
import logging
from time import time
from uuid import uuid4 as uuid
from cgi import escape
from tipfy import RequestHandler, Response, NotFound, get_config
from tipfy.ext.session import SessionMiddleware, SecureCookieMixin, CookieMixin
from tipfy.ext.jinja2 import render_template

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import channel
from google.appengine.api import images
from google.appengine.api import prospective_search as  matcher
from google.appengine.runtime.apiproxy_errors import OverQuotaError

from django.utils.simplejson import dumps
import util
from models import Board, BoardCounter, Thread, Cache
from mark import markup
import rainbow

def json_response(data):
  return Response(
      dumps(data),
      content_type="text/javascript",
  )

class ApiPost(RequestHandler):
  def get(self, board, num):
    post = util.get_post(board, num)

    if not post:
      raise NotFound

    post['html'] = markup(
        board = board,
        postid = num,
        data = post.get("text")
    )
    post['full_html'] = render_template("post.html", post=post, board=board)

    return json_response( post )

class ApiLastPost(RequestHandler):
  def get(self, board):
    board = BoardCounter.get_by_key_name(board)

    return json_response(board.counter if board else None)

class ApiThreadList(RequestHandler):
  def get(self, board):
    return json_response( Board.load(board) )

class ApiThread(RequestHandler):
  def get(self, board, num):
    thread_db = Thread.load(num, board)

    if not thread_db:
      raise NotFound()

    return json_response( {
      "posts" : thread_db.posts,
      "skip" : 0,
      "subject" : thread_db.subject
    } )

class ApiBoard(RequestHandler):
  def get(self, board):
    return json_response(util.get_threads(board, fmt_name='plain'))

class ApiBoardList(RequestHandler):
  def get(self):
    boardq = BoardCounter.all()

    return json_response(
        [
          {
            "code":board.code,
            "name":board.name,
            "last" : board.counter,
          }
          for board in boardq
        ]
    )

class ApiBoardBumped(RequestHandler):
  BOARDS = dict(get_config("aib", "boardlist"))
  DEF_COUNT = 5+ len(BOARDS)
  def load(self, lim=None):
    boardq = BoardCounter.all(keys_only=True)
    boardq.order("-date_modify")
    boardq.filter("old", True)

    if not lim:
      lim = self.DEF_COUNT

    return [
          k.name() 
          for k in boardq.fetch(lim)
          if k.name() not in self.BOARDS
    ]
  def get(self, lim=None):

    blist = memcache.get("bumplist")

    if not blist:
      blist = self.load(lim)
      memcache.set("bumplist", blist, time=60*5)

    return Response(
        "boardbump = %s" % dumps(blist),
        content_type="text/javascript",
    )

class Delete(RequestHandler):
  def post(self, board, thread, post):
    util.delete_post(board, thread, post, "ANAL RAPED")
    return Response("ok")

class Unban(RequestHandler):
  def get(self, ip):
    qkey = "ip-%s" % ip
    memcache.delete(qkey)

    return Response("free")

MONTH = 2592000
class UpdateToken(RequestHandler, SecureCookieMixin, CookieMixin):
  middleware = [SessionMiddleware]

  WATCH_TIME = get_config("aib.util", "watch_time")

  def post(self, board, thread):
    # FIXME: move subscribe crap somewhere out

    rb = rainbow.make_rainbow(self.request.remote_addr, board, thread)
    person_cookie = self.get_secure_cookie("person", True, max_age=MONTH)
    person = person_cookie.get("update", str(uuid()))

    person_cookie['update'] = person

    subid = "%s/%s/%s/%d" %(rb, person, board, thread, )


    token = memcache.get(subid)

    if not token:
      token = channel.create_channel(subid)
      memcache.set(subid, token)

    try:
        query = 'thread:%d board:%s' %(thread, board)

        matcher.subscribe(util.Post, query, subid,
        topic='post',
        lease_duration_sec=self.WATCH_TIME)
    except OverQuotaError:
        logging.error("subscribe failed")
        token = None

    post_level = util.post_level(self.request.remote_addr)

    return json_response( 
        {
          "token" : token,
          "post_quota" : post_level,
          "watcher_time" : self.WATCH_TIME,
        }
    )

class ApiLastImage(RequestHandler):
  def get(self):
    bbq = blobstore.BlobInfo.all()
    bbq.order("-creation")

    return json_response(
      [
          {
            "key" : str(info.key()),
            "url" : images.get_serving_url(str(info.key())),
          }  
          for info in bbq
      ]
    )

class ApiMarkup(RequestHandler):
  def post(self):
    text = self.request.form.get("text", "")

    ret = {
      'html' : markup(
        board = 'test',
        postid = '123',
        data = escape(text),
      )
    }

    return json_response(ret)

