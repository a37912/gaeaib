import logging
from tipfy import redirect, get_config

REDIRECT = "http://www.gaech.org"
FRM = 'gaeaib.appspot.com'
class RedirMW(object):
  def pre_dispatch(self, handler):
    if get_config("tipfy", "dev"):
      return

    if  handler.request.method == 'POST':
      return

    if FRM != handler.request.host:
      return

    return redirect(REDIRECT+handler.request.path)
