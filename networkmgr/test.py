#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import requests
import pprint
import json

if __name__ == '__main__':
    resp = requests.get('http://10.61.123.20:5000/vpp_version')
    print(resp.text)
    sys.exit(0)

    resp = requests.post('http://10.61.123.20:5000/',
            json.dumps({'a':'b'}),
            headers={'Content-Type':'application/json',
                     'Accept': 'application/json'})
    print(resp.text)
