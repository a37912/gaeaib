# -*- coding: utf-8 -*-
import logging
from cgi import escape

from google.appengine.ext import deferred, db
from tipfy import RequestHandler, Response

from render import Render
from models import Thread
from mark import markup
import rainbow

def do_render_cache(cursor=None):
  thq = Thread.all()

  if cursor:
    thq.with_cursor(cursor)

  thread = thq.get()

  if not thread:
    logging.info("stop thread clean")
    return

  render = Render(thread = thread)

  for idx,post in enumerate(thread.posts):
    if 'text' in post:
      post['text_html'] = markup(
            board=thread.board, postid=post.get("post"),
            data=escape(post.get('text', '')),
      )
      if 'rainbow_html' in post:
        post.pop("rainbow_html")
        post['rainbow'] = rainbow.make_rainbow(post['rainbow'])

    if 'image' in post and not post.get("key"):
      post.pop("image")
      post['name'] = 'Kuroneko'

    if idx == 0:
      render.create(post)
    else:
      render.append(post)

  thread.put()

  render.save()

  deferred.defer(do_render_cache, thq.cursor(), _queue="render")


class RenderCache(RequestHandler):
  def get(self):
    do_render_cache()
    return Response("yarr nom-nom")


