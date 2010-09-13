import logging
from tipfy import RequestHandler, Response
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import blobstore
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

