from models import Rss
from tipfy.ext.jinja2 import render_template
from tipfy import RequestHandler, NotFound, Response

def add(board, thread, post, data):
   cache = Rss.load("thread", board, thread)

   if not cache:
     cache = Rss.create("thread", board, thread)

   rendered = render_template("atom.xml", 
	board = board,
        thread = thread,
        data = data,
        post = post,
        cache = cache,
   )
   # FIXME: cant save long posts (>500)

   cache.posts.append(rendered)
   cache.posts = cache.posts[-20:]
   xml = render_template("atom_full.xml",
	board = board, thread = thread, cache=cache)
   cache.xml = xml.encode("utf8")
   cache.put()

class ViewThread(RequestHandler):
  def get(self, board, thread):
    cache = Rss.load("thread", board, thread) 

    if not cache:
      raise NotFound()  

    return Response(cache.xml, content_type="application/atom+xml")
   
