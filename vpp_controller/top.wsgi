#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, os.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from server import app as application

if __name__ == '__main__':
    application.run()
