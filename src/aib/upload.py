from google.appengine.ext import blobstore
from google.appengine.api import images

from tipfy import RequestHandler, Response
from tipfy.ext.blobstore import BlobstoreDownloadMixin, BlobstoreUploadMixin

class PostUrl(RequestHandler):
  def get(self):
    return Response( 
      blobstore.create_upload_url("/post_img")
    )


class PostImage(RequestHandler, BlobstoreUploadMixin):
  def get(self, img):
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
 

