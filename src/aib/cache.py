from google.appengine.ext import deferred
from tipfy import RequestHandler, Response
from models import Cache

class Rebuild(RequestHandler):
  def get(self):
    do_rebuild()
    return Response("going")
     

def do_rebuild(cursor=None):
  cacheq = Cache.all()

  if cursor:
    cacheq.with_cursor(cursor)

  cache = cacheq.get()

  if not cache:
    import logging
    logging.info("stop rebuild")
    return

  if cache.data and not cache.comp:
    cache.comp = cache.data.encode('utf8')
    cache.data = None
    cache.put()

  deferred.defer(do_rebuild, cacheq.cursor())
