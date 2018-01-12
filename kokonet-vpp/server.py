#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import vpp
from flask import Flask, request, jsonify, json, url_for, abort, Response
from flask import redirect, render_template

app = Flask(__name__)
app.debug = True
pp = pprint.PrettyPrinter(indent=2)

'''
comment
'''
v = vpp.vpp_ctl()

@app.route('/vpp_version')
def get_vpp_version():
    ver = v.get_version()
    return ver

@app.route('/status')
def get_status():
    return json.dumps({'error': 'OK'})

# see 00_notebook/home_backup/src/CNI_script/server.py 
# request.form['scripts'] // for POST
# request.args.get('') // for GET
@app.route('/vtep', methods={'POST','GET'})
def add_vtep():
    if request.method == "POST":
        srcip = request.json['src']
        dstip = request.json['dst']
        vni = int(request.json['vni'])
        
        rv = v.create_vxlan_vtep(srcip, dstip, vni)
        if rv == None:
            return json.dumps({'error': 'NG!'})
        #print(rv)
        return json.dumps({'error': 'OK', "sw_if_index": rv})
    else: # case for GET
        # vpp_ip, koko_ip, vxid
        vxlan_list = v.get_vxlan_vtep()
        return json.dumps({'vxlan': vxlan_list, 'error': 'OK'})

@app.route('/vtep/delete', methods={'POST'})
def delete_vtep():
    srcip = request.json['src']
    dstip = request.json['dst']
    vni = int(request.json['vni'])

    rv = v.delete_vxlan_vtep(srcip, dstip, vni)
    if rv != None:
        return json.dumps({'error': 'NG!'})
    return json.dumps({'error': 'OK'})

@app.route('/vtep_ifindex/<vppip>/<hostip>/<vnid>', methods={'GET'})
def get_ifindex(vppip, hostip, vnid):
    ifindex = v.get_vxlan_ifindex(vppip, hostip, int(vnid))
    if ifindex == None:
        return json.dumps({'error': 'Not found'})
    return json.dumps({'error': 'OK', 'ifindex':ifindex})

@app.route('/vtep_connect', methods={'POST','GET'})
def xconnect():
    if request.method == "POST":
        # vxid1, vxid2
        sw_if_index1 = int(request.json['sw_if_index1'])
        sw_if_index2 = int(request.json['sw_if_index2'])
        rv = v.add_xconnect_idx(sw_if_index1, sw_if_index2)
        if rv != None:
            return json.dumps({'error': 'NG'})
        return json.dumps({'error': 'OK'})

    else: # case for GET
        # vpp_ip, koko_ip, vxid
        xconnect_list = v.get_xconnect()
        return json.dumps({'xconnect': xconnect_list, 'error': 'OK'})

@app.route('/vtep_connect/delete', methods={'POST'})
def delete_xconnect():
    # vxid1, vxid2
    print("DELETE:" + request.json['sw_if_index1'] + '/' + request.json['sw_if_index2'])
    sw_if_index1 = int(request.json['sw_if_index1'])
    sw_if_index2 = int(request.json['sw_if_index2'])
    rv = v.del_xconnect_idx(sw_if_index1, sw_if_index2)
    if rv != None:
        return json.dumps({'error': 'NG'})
    return json.dumps({'error': 'OK'})

if app.debug:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)


# in case of gunicorn,
# gunicorn server:app --bind <ip>:5000
if __name__ == '__main__':
    app.run()
