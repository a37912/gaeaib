from models import Rss
from tipfy.ext.jinja2 import render_template
from tipfy import RequestHandler, NotFound, Response
from cgi import escape

def add(board, thread, post, data):
   cache = Rss.load("thread", board, thread)

   if not cache:
     cache = Rss.create("thread", board, thread)

   rendered = render_template("rss_post.xml", 
	board = board,
        thread = thread,
        data = escape(data),
        post = post,
        cache = cache,
   )
   # FIXME: cant save long posts (>500)
   if len(rendered) > 500:
     rendered = "too long"

   cache.posts.append(rendered)
   cache.posts = cache.posts[-20:]
   xml = render_template("rss.xml",
	board = board, thread = thread, cache=cache)
   cache.xml = xml.encode("utf8")
   cache.put()

class ViewThread(RequestHandler):
  def get(self, board, thread):
    cache = Rss.load("thread", board, thread) 

    if not cache:
      raise NotFound()  

    return Response(cache.xml,
      content_type="application/rss+xml; charset=UTF-8")
   
