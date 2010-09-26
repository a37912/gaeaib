import logging
from tipfy import redirect, get_config

REDIRECT = "http://www.bloop.ru"
FRM = ('gaeaib.appspot.com',)
class RedirMW(object):
  def pre_dispatch(self, handler):
    if get_config("tipfy", "dev"):
      return

    if  handler.request.method == 'POST':
      return

    if handler.request.host not in FRM:
      return

    return redirect(REDIRECT+handler.request.path)
