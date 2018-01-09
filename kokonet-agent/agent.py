#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, etcd3, json, subprocess
import pprint

def get_addr_diff(containerid, old_vals, new_vals):
    print(containerid, ':', old_vals, '->', new_vals)
    if old_vals == '':
        old_set = set()
    else:
        old_set = set(json.loads(old_vals)['address'])
    if new_vals == '':
        return (set(), old_set)

    new_set = set(json.loads(new_vals)['address'])
    new_addrs = new_set - old_set
    remove_addrs = old_set - new_set
    print("to be added:", new_addrs)
    print("to be removed:", remove_addrs)
    return (new_addrs, remove_addrs)

def change_addr(etcd, hostip, containerif, old_vals, new_vals):
    (new_addrs, remove_addrs) = get_addr_diff(containerif, old_vals, new_vals)
    n = containerif.split('/')
    containerid = n[0]
    ifname = n[1]

    (nsname, meta) = etcd.get('kokonet/netns/%s/%s'%(hostip, containerid))

    for i in remove_addrs:
        cmd = "/app/koro netns /host%s address del %s dev %s"%(nsname, i, ifname)
        ret = subprocess.call(cmd.split())
        print("cmd:", cmd, ret)
    for i in new_addrs:
        cmd = "/app/koro netns /host%s address add %s dev %s"%(nsname, i, ifname)
        ret = subprocess.call(cmd.split())
        print("cmd:", cmd, ret)

if __name__ == '__main__':
    if "ETCD_CLIENT_HOST" in os.environ:
        etcd_host = os.environ["ETCD_CLIENT_HOST"]
    else:
        etcd_host = "10.0.0.21"
    
    if "ETCD_CLIENT_PORT" in os.environ:
        etcd_port = int(os.environ["ETCD_CLIENT_PORT"])
    else:
        etcd_port = 2379
    
    if "DATAPLANE_IP" in os.environ:
        hostip = os.environ["DATAPLANE_IP"]
    else:
        print("Please set dataplane ip of this host!")
        sys.exit()

    print("ETCD:%s:%d"%(etcd_host, etcd_port))
    print("DATAPLANE_IP:", hostip)
    sys.stdout.flush()
    
    etcd = etcd3.client(host = etcd_host, port = etcd_port)
    cache = {}

    while True:
        ev_iterator, cancel = etcd.watch_prefix('kokonet/ip/%s'%hostip)
        for event in ev_iterator:
            key = event.key.decode('utf-8')
            keys = key.split('/')
            if keys[0] == 'kokonet' and keys[1] == 'ip' and \
               keys[2] == hostip and len(keys) == 5:
                   containerid = keys[3]
                   ifname = keys[4]
                   containerif = "%s/%s"%(containerid,ifname)

                   if type(event) == etcd3.events.PutEvent:
                       val = event.value.decode('utf-8')
                       print("containerid/ifname: %s"%containerif)
                       print(json.loads(val)['address'])
                       if containerif in cache:
                           change_addr(etcd, hostip, containerif, cache[containerif], val)
                       else:
                           change_addr(etcd, hostip, containerif, '', val)
                       cache[containerif] = val
                   elif type(event) == etcd3.events.DeleteEvent:
                       print("containerid/ifname: %s"%containerif)
                       change_addr(etcd, hostip, containerif, '', '')
                       del cache[containerif]
        
            print(event)
