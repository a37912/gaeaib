import logging
from tipfy import RequestHandler, Response
from google.appengine.api import memcache
from google.appengine.ext import db
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
    return json_response( 
        {
          "posts" : Thread.load(num, board),
          "skip" : 0,
        }
    )

class ApiBoard(RequestHandler):
  def get(self, board):
    return json_response(util.get_threads(board, 'plain'))

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

    th = Thread.get(db.Key.from_path(
      "Board", board, 
      "Thread", thread
      )
    )

    for idx,p in enumerate(th.posts):
      if p.get("post") != post:
        continue

      logging.info("found: %r" % p)

      if p.get("key"):
        p.pop("key", None)
        p.pop("image", None)

        try:
          th.images.remove(p.get("key"))
        except:
          pass

        logging.info("removed image %r" % p)

      else:
        p['text'] = 'Fuuuuuu'
       
      p['rainbow_html'] = u'<b>ANAL RAPED</b>'

      break

    th.put()

    key = "posts-%s-%d" %(board, thread)
    memcache.set(key, th.posts)

    Cache.delete(
      (
        dict(Board=board, Thread=thread),
        dict(Board=board)
      )
    )

    return Response("ok")

class Unban(RequestHandler):
  def get(self, ip):
    qkey = "ip-%s" % ip
    memcache.delete(qkey)

    return Response("free")

