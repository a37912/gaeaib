# -*- coding: utf-8 -*-
import logging
from cgi import escape

from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response

from render import Render
from models import Thread
from mark import markup

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

  if len(thread.posts) > 1:
    thread.put()
  else:
    thread.delete()

  render.save()

  deferred.defer(do_render_cache, thq.cursor())


class RenderCache(RequestHandler):
  def get(self):
    do_render_cache()
    return Response("yarr nom-nom")


