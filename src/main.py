# -*- coding: utf-8 -*-


import sys

if 'lib' not in sys.path:
    sys.path[0:0] = ['lib', 'distlib', 'distlib.zip']

import config
import tipfy

application = tipfy.make_wsgi_app(config.config)


def main():
    # Run it!
    tipfy.run_wsgi_app(application)

if __name__ == '__main__':
    main()
