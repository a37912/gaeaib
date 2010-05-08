import logging, os, sys

# Google App Engine imports.
from google.appengine.ext.webapp import util

# Force Django to reload its settings.

#
# Remove the standard version of Django.
for k in [k for k in sys.modules if k.startswith('django')]:
      del sys.modules[k]

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
settings._target = None
import django

import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher

def main():
    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()

    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
