from tipfy import RequestHandler, Response
from render import Render
from models import Thread
from google.appengine.ext import deferred, db
from mark import markup
from cgi import escape

def do_render_cache(cursor=None):
  thq = Thread.all()

  if cursor:
    thq.with_cursor(cursor)

  thread = thq.get()

  if not thread:
    logging.info("stop thread clean")
    return

  board = thread.parent_key().name()
  render = Render(board=board, thread = thread.key().id())

  for idx,post in enumerate(thread.posts):
    post['text_html'] = markup(
          board=board, postid=post.get("post"),
          data=escape(post.get('text', '')),
    )

    if idx == 0:
      render.create(post)
    else:
      render.append(post)

  thread.put()
  render.save()

  deferred.defer(do_render_cache, thq.cursor(), _countdown=10)


class RenderCache(RequestHandler):
  def get(self):
    do_render_cache()
    return Response("yarr nom-nom")


