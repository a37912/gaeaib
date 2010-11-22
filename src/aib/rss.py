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
        posts = post,
   )
   import logging
   logging.info("render: %r" % rendered)

   cache.posts.append(rendered)
   cache.put()

class ViewThread(RequestHandler):
  def get(self, board, thread):
    cache = Rss.load("thread", board, thread) 

    if not cache:
      raise NotFound()  

    xml = render_template("atom_full.xml",
	board = board, thread = thread, posts = cache. posts)

    
    return Response(xml, content_type="application/atom+xml")
   
