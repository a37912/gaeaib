import logging
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import memcache

from tipfy import RequestHandler, Response
from tipfy.ext.blobstore import BlobstoreDownloadMixin, BlobstoreUploadMixin

from const import *

class PostUrl(RequestHandler):
  def get(self):
    qkey = "ip-img-%s" % self.request.remote_addr
    quota = memcache.get(qkey) or 0
    quota += 1
    memcache.set(qkey, quota, time=POST_IMG_INERVAL*quota)

    logging.info("image quota %r = %d" % (self.request.remote_addr, quota ) )

    if quota > POST_IMG_QUOTA:
      return Response("http://winry.on.nimp.org/")


    return Response( 
      blobstore.create_upload_url("/post_img")
    )


class PostImage(RequestHandler, BlobstoreUploadMixin):
  def get(self, img):

    info = blobstore.BlobInfo.get(blobstore.BlobKey(img))

    if 'image/' not in info.content_type:
      info.delete()
      return Response('{"err": "not image"}')

    return Response( '{"img":"%s"}' % img )

  def post(self):
    upload_files = self.get_uploads('image')
    blob_info = upload_files[0]

    key = str(blob_info.key())

    return Response(
      status = 302,
      headers = { "Location" : "/post_img/%s" % key }
    )

class ViewImage(RequestHandler, BlobstoreDownloadMixin):
  def get(self, img):
    key = blobstore.BlobKey(img)

    url = images.get_serving_url(img, 48)
    url = url.replace("0.0.0.0", self.request.host.split(":")[0])

    return Response(
      status = 302,
      headers = { "Location" : str(url) },
    )
 

