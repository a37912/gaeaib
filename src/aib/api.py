from tipfy import RequestHandler, Response
from google.appengine.api import memcache
from django.utils.simplejson import dumps

class ApiPost(RequestHandler):
  TPL = {
      "thread" : "posts-%(board)s-%(num)d",
      "post" : "post-%(board)s-%(num)d",
      "lastpost" : "posts-%(board)s",
      "threadlist" : "threadlist-%(board)s"
  }
  def get(self, mode, board, num=None):
    key = self.TPL.get(mode)
    posts = memcache.get(key % {"board":board, "num":num})

    return Response(
        dumps(posts),
        content_type="text/javascript",
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

