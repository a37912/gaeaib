# -*- coding: utf-8 -*-
import logging
import re

from google.appengine.ext import db
from google.appengine.api import users

from tipfy import RequestHandler, redirect, Response, NotFound, get_config
from tipfy.ext.jinja2 import render_response, render_template

from tipfy.ext.session import SessionMiddleware, SecureCookieMixin, CookieMixin

from forms import PostForm
from util import get_threads, save_post, get_post, delete_post

import models
from redir import RedirMW
import mark
mark.install_jinja2()

import antiwipe

REDIRECT = ['http://danbooru.donmai.us/post/index?tags=winry_rockbell']

def redirect_out():
  import random
  [url] = random.sample(REDIRECT, 1)
  return redirect(url)

class StyleSetMW(object):
  CHAN = re.compile("^http://(%s).*" % str.join("|", 
      get_config("aib", "chanlist")
    )
  )

  def post_dispatch(self, handler, response):
    ref = handler.request.referrer or ""

    if re.match(self.CHAN, ref):
      response.set_cookie("style", "photon")

    return response


## View: Main page - board list
#
class Index(RequestHandler):
  middleware = [RedirMW]
  def get(self, tpl):
    return render_response(tpl, boards =  get_config("aib", "boardlist"))

def boardlink(board):

  import math
  return {
      "code" : board.code,
      "name" : board.name or board.code,
      "size" : min(50,max(20,math.sqrt(board.counter))),
  }

class Boardlist(RequestHandler):
  BOARDLIM = 100
  def get(self):
    return render_response(
        "boardlist.html", 
        boards =  get_config("aib", "boardlist"),
        allboards = map(
          boardlink,
          models.BoardCounter.all().fetch(self.BOARDLIM)
        ),
    )


## View: board page is a list of threads
#
# @param board - string board name
class Board(RequestHandler):
  middleware = [RedirMW, StyleSetMW]

  PAGES = get_config("aib.ib", "board_pages")
  NAMES = dict(get_config("aib", "boardlist"))
  OVER = get_config("aib", "overlay")
 
  def get(self, board, page=0):

    if page > self.PAGES:
      raise NotFound()

    if page == 0:
      cache = models.Cache.load("board", board)
      if cache:
        return Response(cache.data)

    data = {}
    data['threads'] = get_threads(board,page=page) # last threads
    data['show_captcha'] = True
    data['reply'] = True
    data['board_name'] = self.NAMES.get(board) or "Woooo???"
    data['board'] = board # board name
    data['boards'] =  get_config("aib", "boardlist")
    data['pages'] = range(self.PAGES)

    data['overlay'] = board in self.OVER

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

  def post(self, board, thread, ajax=False):
    if not re.match('^\w+$', board):
      raise NotFound
    logging.info("post called")

    if not antiwipe.check(self.request.remote_addr):
      logging.warning("wipe redirect: %r" % self.request.remote_addr)
      return redirect_out()

    if not ajax:
      person_cookie = self.get_secure_cookie("person", True)
      #if not person_cookie.get("update"):
      #  return redirect_out()


    # validate post form
    form = PostForm(self.request.form)

    if not form.validate():
      return redirect("/%s/" % board)

    logging.info("data: %r" % form.data)
    logging.info("form: %r" % self.request.form)

    # if ok, save
    post, thread = save_post(self.request, form.data, board, thread)
    
    key = board + "%d" % post
    cookie = self.get_secure_cookie(key)
    cookie["win"] = key

    if ajax:
      return Response('{"post":%d }' % post)

    return redirect("/%s/%d/" % (board, thread))

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

    thq = models.ThreadIndex.all(keys_only=True)
    thq.filter("board", board)
    thq.filter("post_numbers", post)

    thread = thq.get()

    if not thread:
      raise NotFound()

    return redirect("/%s/#p%d"% 
        (thread.parent().name(), post)
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

    user = users.get_current_user()
    mods = get_config("aib.ib", "mod_name")

    if cookie.get('win') == key or (user and user.email() in mods):
      if delete_post(board, thread, post, "AN HERO"):
        self.delete_cookie(key)

    return redirect("/%s/%d" %( board, thread) )

