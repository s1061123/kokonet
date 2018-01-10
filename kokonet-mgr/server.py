#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, requests, etcd3, json, sys
import pprint
from flask import Flask, request, jsonify, json, url_for, abort, Response
from flask import redirect, render_template

app = Flask(__name__)
app.debug = True
pp = pprint.PrettyPrinter(indent=2)

'''
comment
'''

#parameters
if "VPP_CONTROLLER_URL" in os.environ:
    vpp_controller_url = os.environ["VPP_CONTROLLER_URL"]
else:
    vpp_controller_url = "http://10.0.0.10:5000"

if "VPP_VTEP_IP" in os.environ:
    switch_ctrl_ip = { os.environ["VPP_VTEP_IP"]: vpp_controller_url }
else:
    switch_ctrl_ip = { "10.1.1.1": vpp_controller_url }

if "ETCD_CLIENT_HOST" in os.environ:
    etcd_host = os.environ["ETCD_CLIENT_HOST"]
else:
    etcd_host = "127.0.0.1"

if "ETCD_CLIENT_PORT" in os.environ:
    etcd_port = int(os.environ["ETCD_CLIENT_PORT"])
else:
    etcd_port = 2379

#const 
switch_vnid_range_begin = 1000
switch_vnid_range_end = 2000
switch_endpoint = {}
etcd = None

def init():
    global switch_vnid_range_begin, switch_vnid_range_end
    global vpp_controller_url, switch_ctrl_ip, etcd_host, etcd_port

    #print current configuration
    print("vpp_controller_url:%s"%vpp_controller_url)
    print("switch_ctrl_ip:%s"%switch_ctrl_ip)
    print("etcd:%s:%d"%(etcd_host, etcd_port))
    sys.stdout.flush()

    etcd = etcd3.client(host = etcd_host, port = etcd_port)
    (v, meta) = etcd.get('kokonet/vnid_range')
    if v == None:
        range_json = json.dumps({'begin':switch_vnid_range_begin,
                                 'end':switch_vnid_range_end})
        etcd.put('kokonet/vnid_range', range_json)
    else:
        range_json = json.loads(v)
        switch_vnid_range_begin = range_json['begin']
        switch_vnid_range_end = range_json['end']

    return

def vtep_config_add(hostip, switchip, vni):
    resp = requests.post('%s/vtep'%(vpp_controller_url),
            json.dumps({'src': switchip, 'dst': hostip, 'vni': vni}),
            headers={'Content-Type':'application/json',
                     'Accept': 'application/json'})
    return resp.json()

def vtep_config_del(hostip, switchip, vni):
    resp = requests.post('%s/vtep/delete'%(vpp_controller_url),
            json.dumps({'src': switchip, 'dst': hostip, 'vni': vni}),
            headers={'Content-Type':'application/json',
                     'Accept': 'application/json'})
    return resp.json()

def get_endpoint_data(request_data):
    hostip = request_data['hostip']
    switchip = request_data['switchip']
    containerid = request_data['containerid']
    cniargs = request_data['cniargs']
    ifname = request_data['ifname']

    return { 'hostip': hostip, 'switchip': switchip,
             'containerid': containerid, 'ifname': ifname}

@app.route('/vtep/new', methods={'GET', 'POST'})
def get_new_vtep_info():
    if request.method == "POST":
        # param: hostip, vppip, container id, ifname/koko, (XXX)cni_args
        # return: vnid, (XXX)address (if possible)
        for i in range(switch_vnid_range_begin, switch_vnid_range_end):
            if str(i) not in switch_endpoint:
                endpoint_data = get_endpoint_data(request.json)
                switch_endpoint[str(i)] = endpoint_data

                #add key into etcd
                etcd = etcd3.client(host = etcd_host, port = etcd_port)
                etcd.put('kokonet/%s/%d'%(endpoint_data['switchip'], i),
                         json.dumps(endpoint_data))
                #send to vtep_driver
                vtep_config_add(endpoint_data['hostip'],
                                endpoint_data['switchip'], i)
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
            vtep_config_del(hostip, switchip, i)

            etcd = etcd3.client(host = etcd_host, port = etcd_port)
            etcd.delete('kokonet/%s/%s'%(switchip, i))

            del switch_endpoint[i]
            #print("%s deleted"%i)
            return json.dumps({'error': 'OK'})
    return json.dumps({'error': 'Not Found'})

@app.route('/vtep', methods={'GET'})
def get_vtep_info():
    #TBD
    return json.dumps({'error': 'TBD'})

@app.route('/status', methods={'GET'})
def get_status():
    sys.stdout.flush()
    return json.dumps({'error': 'OK'})

if app.debug:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

init()

# in case of gunicorn,
# gunicorn server:app --bind <ip>:80
if __name__ == '__main__':
    app.run(port=80)
