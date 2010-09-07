import logging

from google.appengine.api import memcache
from google.appengine.ext import db

from tipfy import RequestHandler, redirect, Response, NotFound
from tipfy.ext.jinja2 import render_response, render_template

from forms import PostForm
from util import get_threads, save_post, get_post

from const import *
import models
from redir import RedirMW

## View: Main page - board list
#
class Index(RequestHandler):
  #middleware = [RedirMW]
  def get(self, tpl):
    return render_response(tpl, boards = boardlist_order)

## View: board page is a list of threads
#
# @param board - string board name
class Board(RequestHandler):
  #middleware = [RedirMW]

  def get(self, board):

    cache = models.Cache.load(Board=board)
    if cache:
      return Response(cache)

    data = {}
    data['post_form'] = PostForm() # new post form
    data['threads'] = get_threads(board) # last threads
    data['show_captcha'] = True
    data['reply'] = True
    data['board_name'] = boardlist.get(board, 'WHooo??')
    data['board'] = board # board name
    data['boards'] = boardlist_order

    html = render_template("thread.html", **data)
    models.Cache.save(data = html, Board=board)

    return Response(html)

## View: saves new post
#
# @param board - string board name
# @param thread - thread id where to post or "new"
class Post(RequestHandler):
  def get(self, board, thread):
    return redirect("/%s/%d" %( board, thread) )

  def post(self, board, thread):
    logging.info("post called")

    ip = self.request.remote_addr

    qkey = "ip-%s" % ip
    quota = memcache.get(qkey) or 0
    quota += 1
    memcache.set(qkey, quota, time=POST_INERVAL*quota)

    logging.info("ip: %s, quota: %d" % (ip, quota))

    if quota >= POST_QUOTA:
      return redirect("http://winry.on.nimp.org" )

    # validate post form
    form = PostForm(self.request.form)

    if not form.validate:
      return redirect("/%s" % board)

    # if ok, save
    logging.info("data valid %r" %( form.data,))
    post, thread = save_post(self.request, form.data, board, thread)

    return redirect("/%s/%d" % (board, thread))

## View: show all posts in thread
#
# @param board - string board name
# @Param thread - thread id where
class Thread(RequestHandler):
  #middleware = [RedirMW]

  def get(self, board, thread):
    cache = models.Cache.load(Board=board, Thread=thread)
    if cache:
      return Response(cache)

    _thread_data = models.Thread.load(thread, board)
    content = _thread_data.get('posts')

    if not content:
      raise NotFound

    thread_data = {
      'op' : content[0],
      'posts' : content[1:],
      'id' : thread,
      'subject' : _thread_data.get('subject'),
    }

    data = {}
    data['threads'] = (thread_data,)
    data['post_form'] = PostForm()
    data['board_name'] = boardlist.get(board, "Woooo???")
    data['board'] = board
    key = "update-thread-%s-%d" % (board, thread)
    #data['thread_token'] = channel.create_channel(key)
    data['boards'] = boardlist_order

    html = render_template("thread.html", **data)

    models.Cache.save(data = html, Board=board, Thread=thread)

    return Response(html)

class PostRedirect(RequestHandler):
  def get(self, board, post):
    post_data = get_post(board, post)

    thq = models.Thread.all(keys_only=True)
    thq.ancestor( db.Key.from_path("Board", board))
    thq.filter("post_numbers", post)

    thread = thq.get()

    if not thread:
      raise NotFound()

    return redirect("/%s/%d/#p%d"% 
        (board, thread.id(), post)
      )
