# -*- coding: utf-8 -*-
import logging
from time import time
from uuid import uuid4 as uuid
from tipfy import RequestHandler, Response, NotFound, get_config
from tipfy.ext.session import SessionMiddleware, SecureCookieMixin, CookieMixin
from tipfy.ext.jinja2 import render_template

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import channel

from django.utils.simplejson import dumps
import util
from models import Board, Thread, Cache
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
    board = Board.get_by_key_name(board)

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
    boardq = Board.all()

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
  DEF_COUNT = 5
  BOARDS = dict(get_config("aib", "boardlist"))
  def load(self, lim=None):
    boardq = Board.all(keys_only=True)
    boardq.order("-date_modify")
    boardq.filter("old", True)
    boardq.filter("named", False)

    if not lim:
      lim = self.DEF_COUNT

    return [
          k.name() 
          for k in boardq.fetch(lim)
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

class UpdateToken(RequestHandler, SecureCookieMixin, CookieMixin):
  middleware = [SessionMiddleware]

  WATCH_TIME = get_config("aib.util", "watch_time")

  def post(self, board, thread):
    # FIXME: move subscribe crap somewhere out

    key = "upt-%s-%d" % (board, thread)
    person_cookie = self.get_secure_cookie("person", True)
    person = person_cookie.get("update", str(uuid()))

    person_cookie['update'] = person

    watchers = memcache.get(key) or []

    nwatchers = util.watchers_clean(watchers, person)
    nwatchers.insert(0, (time(),person))

    memcache.set(key, nwatchers, time=self.WATCH_TIME)

    token = memcache.get(person+key)

    if not token:
      logging.debug("cr: %r + %r" % (person, key))
      token = channel.create_channel(person+key)
      memcache.set(person+key, token)

    post_level = util.post_level(self.request.remote_addr)

    rb = rainbow.make_rainbow(self.request.remote_addr, board, thread)

    util.watchers_send(watchers, key, {
      "evt" : "enter",
      "rainbow" : rb,
      }
    )

    return json_response( 
        {
          "token" : token,
          "post_quota" : post_level,
          "watcher_time" : self.WATCH_TIME,
        }
    )
