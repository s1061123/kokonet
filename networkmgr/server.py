#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
from flask import Flask, request, jsonify, json, url_for, abort, Response
from flask import redirect, render_template
import requests

app = Flask(__name__)
app.debug = True
pp = pprint.PrettyPrinter(indent=2)

'''
comment
'''

#const 
switch_ctrl_ip = { "10.1.1.1": "http://10.61.123.20:5000/" }
switch_vnid_range_begin = 1000
switch_vnid_range_end = 2000
switch_endpoint = {}

def init():
    # XXX: do etcd initialize
    return

def vtep_config_add(hostip, switchip, vni):
    resp = requests.post('http://10.61.123.20:5000/vtep',
            json.dumps({'src': switchip, 'dst': hostip, 'vni': vni}),
            headers={'Content-Type':'application/json',
                     'Accept': 'application/json'})
    return resp.json()

def vtep_config_del(hostip, switchip, vni):
    resp = requests.post('http://10.61.123.20:5000/vtep/delete',
            json.dumps({'src': switchip, 'dst': hostip, 'vni': vni}),
            headers={'Content-Type':'application/json',
                     'Accept': 'application/json'})
    return resp.json()

@app.route('/vtep/new', methods={'GET', 'POST'})
def get_new_vtep_info():
    if request.method == "POST":
        # param: hostip, vppip, container id, ifname/koko, (XXX)cni_args
        # return: vnid, (XXX)address (if possible)
        hostip = request.json['hostip']
        switchip = request.json['switchip']
        containerid = request.json['containerid']
        cniargs = request.json['cniargs']
        ifname = request.json['ifname']
        print(cniargs)
        for i in range(switch_vnid_range_begin, switch_vnid_range_end):
            if str(i) not in switch_endpoint:
                switch_endpoint[str(i)] = { 'hostip': hostip, 
                                            'switchip': switchip,
                                            'containerid': containerid,
                                            'ifname': ifname}
                vtep_config_add(hostip, switchip, i)
                break
        return json.dumps({'error': 'OK', 'vnid': i})
    else: # GET
        return json.dumps({'error': 'OK'})

@app.route('/vtep/delete', methods={'POST'})
def delete_vtep_info():
    hostip = request.json['hostip']
    switchip = request.json['switchip']
    containerid = request.json['containerid']
    ifname = request.json['ifname']
    for i in switch_endpoint.keys():
        if switch_endpoint[i]["hostip"] == hostip and \
           switch_endpoint[i]["switchip"] == switchip and \
           switch_endpoint[i]["containerid"] == containerid and \
           switch_endpoint[i]["ifname"] == ifname:
            del switch_endpoint[i]
            vtep_config_del(hostip, switchip, i)
            #print("%s deleted"%i)
            return json.dumps({'error': 'OK'})
    return json.dumps({'error': 'Not Found'})

@app.route('/vtep', methods={'GET'})
def get_vtep_info():
    return json.dumps({'error': 'OK'})

if app.debug:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

# in case of gunicorn,
# gunicorn server:app --bind <ip>:80
if __name__ == '__main__':
    init()
    app.run(port=80)
