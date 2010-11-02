# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import db

from tipfy import RequestHandler, redirect, Response, NotFound, get_config
from tipfy.ext.jinja2 import render_response, render_template

from tipfy.ext.session import SessionMiddleware, SecureCookieMixin, CookieMixin

from forms import PostForm
from util import get_threads, save_post, get_post, delete_post

from const import *
import models
from redir import RedirMW
import mark
mark.install_jinja2()

import antiwipe

## View: Main page - board list
#
class Index(RequestHandler):
  middleware = [RedirMW]
  def get(self, tpl):
    return render_response(tpl, boards =  get_config("aib", "boardlist"))

## View: board page is a list of threads
#
# @param board - string board name
class Board(RequestHandler):
  middleware = [RedirMW]

  def get(self, board, page=0):

    if page > BOARD_PAGES:
      raise NotFound()

    if page == 0:
      cache = models.Cache.load("board", board)
      if cache:
        return Response(cache.data)

    data = {}
    data['threads'] = get_threads(board,page=page) # last threads
    data['show_captcha'] = True
    data['reply'] = True
    data['board_name'] = get_config("aib.boards", board) or "Woooo???"
    data['board'] = board # board name
    data['boards'] =  get_config("aib", "boardlist")
    data['pages'] = range(BOARD_PAGES)

    html = render_template("board.html", **data)

    if page == 0:
      cache = models.Cache.create("board", board)
      cache.data = html
      cache.put()

    return Response(html)

## View: saves new post
#
# @param board - string board name
# @param thread - thread id where to post or "new"
class Post(RequestHandler, SecureCookieMixin):
  middleware = [SessionMiddleware]
  def get(self, board, thread):
    return redirect("/%s/%d" %( board, thread) )

  def post(self, board, thread):
    logging.info("post called")

    if not antiwipe.check(self.request.remote_addr):
      logging.warning("wipe redirect: %r" % self.request.remote_addr)
      return redirect("http://winry.on.nimp.org" )

    # validate post form
    form = PostForm(self.request.form)

    if not form.validate():
      return redirect("/%s/" % board)

    # if ok, save
    logging.info("data valid %r" %( form.data,))
    post, thread = save_post(self.request, form.data, board, thread)
    
    key = board + "%d" % post
    cookie = self.get_secure_cookie(key)
    cookie["win"] = key

    return redirect("/%s/%d" % (board, thread))

## View: show all posts in thread
#
# @param board - string board name
# @Param thread - thread id where
class Thread(RequestHandler):
  middleware = [RedirMW]

  def get(self, board, thread):
    cache = models.Cache.load("thread", board, thread)
    if cache:
      return Response(cache.data)
    else:
      raise NotFound

class PostRedirect(RequestHandler):
  def get(self, board, post):
    post_data = get_post(board, post)

    thq = models.Thread.all(keys_only=True)
    thq.filter("board", board)
    thq.filter("post_numbers", post)

    thread = thq.get()

    if not thread:
      raise NotFound()

    return redirect("/%s/%d/#p%d"% 
        (board, thread.id(), post)
      )


## View: Rapes specifiend post
#
# @param board - string board name
# @param thread - thread id
# @param post - post id which will be deleted
class DeletePost(RequestHandler, SecureCookieMixin, CookieMixin):
  middleware = [SessionMiddleware]
  def get(self, board, thread, post):
    
    key = board + "%d" % post
    cookie = self.get_secure_cookie(key, True)
    if cookie.get('win') == key:
      if delete_post(board, thread, post, "AN HERO"):
        self.delete_cookie(key)

    return redirect("/%s/%d" %( board, thread) )

