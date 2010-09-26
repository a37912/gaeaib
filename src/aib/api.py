import logging
from uuid import uuid4 as uuid
from tipfy import RequestHandler, Response
from tipfy.ext.session import SessionMiddleware, SecureCookieMixin, CookieMixin

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import channel

from django.utils.simplejson import dumps
import util
from models import Board, Thread, Cache

def json_response(data):
  return Response(
      dumps(data),
      content_type="text/javascript",
  )

class ApiPost(RequestHandler):
  def get(self, board, num):
    return json_response( util.get_post(board, num) )

class ApiLastPost(RequestHandler):
  def get(self, board):
    key = "posts-%s" % board
    post = memcache.get(key)

    if post != None:
      return json_response(post)

    board = Board.get_by_key_name(board)

    if board:
      post = board.counter
      memcache.set(key, post)
    else:
      post = None

    return json_response(post)

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

  def post(self, board, thread):
    key = "update-thread-%s-%d" % (board, thread)
    person_cookie = self.get_secure_cookie("person", True)
    person = person_cookie.get("update", str(uuid()))
    person_cookie['update'] = person

    watchers = memcache.get(key) or []
    if person not in watchers:
      watchers.append(person)
      memcache.set(key, watchers[:20], time=60*20) # FIXME

    token = channel.create_channel(person+key)

    return json_response( {"token" : token} )
