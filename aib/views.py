from django.shortcuts import render_to_response as render, redirect
from django.http import HttpResponse, Http404
from django import forms
from django.conf import settings

from google.appengine.api import memcache

import logging
from md5 import md5
from google.appengine.ext import db
from google.appengine.api import images
import recaptcha

# TODO: move out
# New post or thread form
class PostForm(forms.Form):

  name = forms.CharField(required=False)
  sage = forms.BooleanField(required=False)
  text = forms.CharField(widget=forms.Textarea, required=False)
  image = forms.FileField(required=False) # FIXME: gae vs pil

# TODO: move out
class Image(db.Model):
  data = db.BlobProperty()
  full_hash = db.StringProperty()

# temporary here is list of boards
boardlist = ['a', 'b', 'mod']
THREAD_PER_PAGE = 5
REPLIES_MAIN = 5

## View: Main page - board list
#
def index(request):
  return render("index.html", {"boards" : boardlist})

## Helper: functon to grab last thread list for board
#
# @param board - string board name
def get_threads(board):

  threads = memcache.get("threadlist-%s" % board) or []

  # map list of thread ids to fetch
  ids = map(str,threads)

  # grab data from cache
  data =  memcache.get_multi(ids, "posts-%s-" % board)
  logging.info("grabbed ids %s, prefix %s, got %s" %(
    str(ids),
    "posts-%s-" % board,
    str(data.keys()),
    )
  )

  ret = []
  for thread in threads:
    content = data.get(str(thread))

    if not content:
      continue

    if len(content) > REPLIES_MAIN+1:
      end = content[-REPLIES_MAIN:]
      omitt = len(content) - REPLIES_MAIN - 1
    else:
      end = content[1:]
      omitt = 0
      

    thread_data = {
        'op' : content[0],
        'posts' : end,
        'id' : thread,
        "skipmsg" : "%d omitted" % omitt if omitt else None,
      }

    ret.append( thread_data )

  return ret

## View: board page is a list of threads
#
# @param board - string board name
def board(request, board):

  data = {}
  data['post_form'] = PostForm() # new post form
  data['board_name'] = board # board name
  data['threads'] = get_threads(board) # last threads
  data['show_captcha'] = True
  data['reply'] = True

  logging.info("board %s %s" % (board, str(memcache.get("thread"))))

  return render("thread.html", data)

## View: saves new post
#
# @param board - string board name
# @param thread - thread id where to post or "new"
def post(request, board, thread):

  # TODO: redirect to rickroll
  if request.method != 'POST':
    return redirect("/%s" % board)

  # validate post form
  form = PostForm(request.POST, request.FILES)

  if form.is_valid():
    ip = request.META.get("REMOTE_ADDR")

    if thread == 'new':
      check_captca(request.POST, ip)

    # if ok, save
    logging.info("data valid")
    save_post(form.cleaned_data, board, thread, 
        request.META.get("REMOTE_ADDR")
    )
  else:
    # FIXME: show nice error page
    return redirect("/%s" % board)

  # TODO: redirect to thread or to board
  return redirect("/%s" % board)

## Helper: checks recaptcha answer
def check_captca(post, ip):
  challenge = post.get('recaptcha_challenge_field')
  response  = post.get('recaptcha_response_field')

  cResponse = recaptcha.submit( challenge, response, 
      settings.RECAPTCHA_PRV, ip
  )
  if not cResponse.is_valid:
    raise Http404

## Helper: calculates 5 colors for post
def make_rainbow(ip, board, thread):
  key = "%s-%s-%s-%s" %(
      settings.SECRET_KEY, ip, board, thread
  )

  codes = [[]]
  for x in md5(key).digest()[:15]:
    codes[-1].append(ord(x))

    if len(codes[-1]) == 3:
      codes.append([])

  logging.info("code: %s" % str(codes))

  return codes[:-1]

## Helper: saves post to thread
#
# @param data - valid cleaned data from form
# @param board - string board name
# @param thread - thread id where to post or "new"
def save_post(data, board, thread, ip):

  # create new thread
  if thread == 'new':
    thread = memcache.incr("posts-%s" % board, initial_value=0)
    thread_clean(board)
    new = True
  else:
    thread = int(thread)
    new = False

  # FIXME: dont allow to post to nonexstand thread
  posts = memcache.get("posts-%s-%d" % (board, thread))
  if not posts:
    posts = []

  if not new and not posts:
    raise Http404

  # FIXME: move to validation
  if not (data.get("image") or data.get("text")):
    raise Http404

  save_image(data)

  data['rainbow'] = make_rainbow(ip, board, thread)

  # FIXME: move to field
  data['name'] = data.get("name") or "Anonymous"

  if new:
    newpost = thread
  else:
    newpost = memcache.incr("posts-%s" % board, initial_value=0)

  # save thread and post number
  data['post'] = newpost
  data['thread'] = thread

  posts.append(data)

  # save to cache
  memcache.set("posts-%s-%d" % (board, thread), posts)

  # debug
  key = "posts-%s-%d" % (board, thread)

  logging.info("saved %s" % key)

  if new or not data.get("sage"):
    thread_bump(board, thread)

## Helper: bumps thread to the top
#
# @param board - string board name
# @param thread - thread id
#
# @note - can be called at thread creat time
def thread_bump(board, thread):
  threads = memcache.get("threadlist-%s" % board) or []

  if thread in threads:
    threads.remove(thread)

  threads.insert(0, thread)

  memcache.set("threadlist-%s" % board, threads)

## Helper: deletes old threads
#
# @param board - string board nam
# 
# @note called before creating new thread
def thread_clean(board):
  threads = memcache.get("threadlist-%s" % board) or []

  if len(threads) < THREAD_PER_PAGE:
    return

  to_remove = map(str, threads[THREAD_PER_PAGE-1:])
  memcache.delete_multi(to_remove, key_prefix="posts-%s-" % board)

  memcache.set("threadlist-%s" % board, threads[:THREAD_PER_PAGE-1])

## Helper: saves image to db
#
# @param data - post data
def save_image(data):

  # check, if there is image
  image = data.get("image")
  logging.info("data: %s, image %s" % (str(data), str(image)))
  if not image:
    return

  # read data
  image = image.read()

  # make hash
  image_hash = md5(image).hexdigest()

  # save main image to db
  image_db = Image(data=image, full_hash=image_hash, key_name=image_hash)
  image_db.put()

  # save main image to cache
  memcache.set("image_%s" % image_hash, image)

  logging.info("saved %s" % str(image_db.key().name()))

  # resize
  full = images.Image(image)
  full.resize(width=250, height=250)
  full.im_feeling_lucky()
  thumb = full.execute_transforms(output_encoding=images.JPEG)

  # save thumb to db
  thumb_db = Image(data=thumb, 
      full_hash=image_hash,
      key_name="thumb_%s" % image_hash)
  thumb_db.put()

  # save thumb to cache
  memcache.set("image_thumb_%s" % image_hash, thumb)

  logging.info("saved %s" % str(thumb_db.key().name()))

  # replace image with hash
  data['image'] = image_hash


## View: show all posts in thread
#
# @param board - string board name
# @Param thread - thread id where
def thread(request, board, thread):
  thread = int(thread)

  content = memcache.get("posts-%s-%d" % (board, thread))

  if not content:
    raise Http404

  thread_data = {
    'op' : content[0],
    'posts' : content[1:],
    'id' : thread,
  }

  data = {}
  data['threads'] = (thread_data,)
  data['post_form'] = PostForm()

  return render("thread.html", data)

# TODO: move out of django
## View load image
#
# @param image_hash - requested image hash
def image(request, image_hash):

  logging.info("load %s" % image_hash)

  data = memcache.get("image_%s" % image_hash)

  if not data:
    logging.info("cache miss")
  
    image = Image.get_by_key_name(image_hash)

    if not image:
      raise Http404

    data = image.data
    memcache.set("image_%s" % image_hash, data)
  else:
    logging.info("cache hit")

  return HttpResponse(data, mimetype="image/jpeg")


