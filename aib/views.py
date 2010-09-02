import logging
from md5 import md5

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.ext import blobstore

from tipfy import RequestHandler, Response, redirect
from tipfy.ext.jinja2 import render_response

from wtforms import Form
from wtforms.fields import TextField

from traceback import format_exc

import recaptcha
import rainbow


# TODO: move out
# New post or thread form
class PostForm(Form):

  name = TextField()
  sage = TextField()
  text = TextField()

# temporary here is list of boards
boardlist = ['a', 'b', 'mod']
THREAD_PER_PAGE = 5
REPLIES_MAIN = 5

## View: Main page - board list
#
class Index(RequestHandler):
  def get(self):
    return render_response("index.html", boards = boardlist)

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
class Board(RequestHandler):
  def get(self, board):

    data = {}
    data['post_form'] = PostForm() # new post form
    data['board_name'] = board # board name
    data['threads'] = get_threads(board) # last threads
    data['show_captcha'] = True
    data['reply'] = True
    
    logging.info("board %s %s" % (board, str(memcache.get("thread"))))

    return render_response("thread.html", **data)

## View: saves new post
#
# @param board - string board name
# @param thread - thread id where to post or "new"
class Post(RequestHandler):
  def post(self, board, thread):
    logging.info("post called")

    # validate post form
    form = PostForm(self.request.form)

    if form.validate:
      ip = self.request.remote_addr

      # if ok, save
      logging.info("data valid %r" %( form.data,))
      try:
        #save_image(request, form.cleaned_data)
        save_post(form.data, board, thread, ip)
      except:
        logging.error(
           format_exc() 
        )
        raise
      finally:
        logging.info("after save")

    else:
      # FIXME: show nice error page
      return redirect("/%s" % board)

    # TODO: redirect to thread or to board
    return redirect("/%s" % board)

## Helper: calculates 5 colors for post
def make_rainbow(ip, board, thread):
  secret = 'YOBA'# FIXME
  key = "%s-%s-%s-%s" %(secret, ip, board, thread)

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
  logging.info("data: %r" % data)
  if not (data.get("image") or data.get("text")):
    raise Http404

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

THUMB_WIDTH = 250
THUMB_HEIGH = 250

## Helper: saves image to db
#
# @param data - post data
def save_image(request, data):

  # check, if there is image
  image = get_uploads(request, field_name="image")
  if not image:
    logging.info("no image")
    return

  [image] = image

  # zomg
  full_data = blobstore.fetch_data(image.key(), 0, 50000) 
  full_info = images.Image(image_data=full_data)
  logging.info("image size: %d x %d" %( full_info.width, full_info.height))

  # resize
  full = images.Image(blob_key=str(image.key()))

  if full_info.width > THUMB_WIDTH or full_info.height > THUMB_HEIGH:
    full.resize(width=250, height=250)
    full.im_feeling_lucky()
    thumb = full.execute_transforms(output_encoding=images.JPEG)

    # save thumb to db
    thumb_db = Thumb(data=thumb, full=image,)
    key = thumb_db.put()

    # format addr
    thumb_addr = "thumb/" + str(key)
  else:
    thumb_addr = "image/" + str(image.key())


  # replace image with hash
  data['image'] = {
      "key" : str(image.key()),
      "content_type" : image.content_type,
      "size" : image.size,
      "thumb" : thumb_addr,
      "xy" : "%dx%d" %(full_info.width, full_info.height),
  }


## View: show all posts in thread
#
# @param board - string board name
# @Param thread - thread id where
class Thread(RequestHandler):
  def get(self, board, thread):

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
    data['upload_url'] = blobstore.create_upload_url(
        "/%s/%d/post/" % (board, thread),
    )

    return render_response("thread.html", **data)

# TODO: move out of django
## View load image
#
# @param image_hash - requested image hash
def image(request, image_key):
  blobinfo = blobstore.BlobInfo(blobstore.BlobKey(image_key))

  logging.info("requested %s got %s" % (
    str(image_key),
    str(blobinfo)
    )
  )
  
  return send_blob(request, blobinfo)

def thumb(request, thumb_key):
  thumb = db.get(db.Key(thumb_key))

  return HttpResponse(thumb.data, mimetype="image")


