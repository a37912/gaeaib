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
  thq = Thread.all(keys_only=True)

  if cursor:
    thq.with_cursor(cursor)

  if not thq.count(1):
    return

  for thread in thq.fetch(100):
    deferred.defer(process, thread, _queue='render')


  deferred.defer(do_render_cache, thq.cursor() )

def process(thread_key):
  logging.info('process %r' % thread_key)
  thread = db.get(thread_key)

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



class RenderCache(RequestHandler):
  def get(self):
    do_render_cache()
    return Response("yarr nom-nom")


