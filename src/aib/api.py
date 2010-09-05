import logging
from tipfy import RequestHandler, Response
from google.appengine.api import memcache
from django.utils.simplejson import dumps
import util
from models import Board, Thread

def json_response(data):
  return Response(
      dumps(data),
      content_type="text/javascript",
  )



class ApiCacheGeneric(RequestHandler):
  TPL = {
      "thread" : "posts-%(board)s-%(num)d",
      "post" : "post-%(board)s-%(num)d",
      "lastpost" : "posts-%(board)s",
      "threadlist" : "threadlist-%(board)s"
  }
  def get(self, mode, board, num=None):
    key = self.TPL.get(mode)
    posts = memcache.get(key % {"board":board, "num":num})

    return json_response(posts)

class ApiPost(RequestHandler):
  def get(self, board, num):
    return json_response( util.get_post(board, num) )

class ApiBoard(RequestHandler):
  def get(self, board):
    return json_response(util.get_threads(board))

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

    key = "posts-%s-%d" % (board, thread)

    if post == thread:
      memcache.delete(key)
      return Response("wipe")

    posts = memcache.get(key) or []

    for offset, data in enumerate(posts):
      if data.get('post') == post:
        posts.pop(offset)
        break
    else:
      return Response("no")

    memcache.set(key, posts)

    return Response("ok")

class Unban(RequestHandler):
  def get(self, ip):
    qkey = "ip-%s" % ip
    memcache.delete(qkey)

    return Response("free")

