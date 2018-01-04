#!/usr/bin/env python
'''
vpp_hello_world.py
'''
from __future__ import print_function
 
import os, ctypes
import fnmatch
from ipaddress import *
 
from vpp_papi import VPP 

class vpp_ctl:
	vpp_json_dir = '/usr/share/vpp/api'
	jsonfiles = []
	vpp = None
	
	def __init__(self):
		# construct a list of all the json api files
		for root, dirnames, filenames in os.walk(self.vpp_json_dir):
    			for filename in fnmatch.filter(filenames, '*.api.json'):
        			self.jsonfiles.append(os.path.join(self.vpp_json_dir, filename))
 
                if vpp_ctl.vpp != None:
                    return

		if not self.jsonfiles:
    			print('Error: no json api files found')
			exit(-1)
 
		vpp_ctl.vpp = VPP(self.jsonfiles)
		r = vpp_ctl.vpp.connect('papi')
		if r != None:
			print(r)
 
        def get_version(self):
		rv = self.vpp.show_version()
		return (rv.version.decode().rstrip('\0x00'))
		# VPP version = 17.04-rc0~192-gc5fccc0c

	def getvpp(self):
                return vpp_ctl.vpp

	def getintf(self):
		for intf in vpp_ctl.vpp.sw_interface_dump():
			print(intf.interface_name.decode())

	def create_vxlan_vtep(self, src, dst, vxid):
		srcip = str(IPv4Address(unicode(src)).packed)
		dstip = str(IPv4Address(unicode(dst)).packed)
                decap_next_idx = ctypes.c_uint32(-1).value
		rv = vpp_ctl.vpp.vxlan_add_del_tunnel(is_add=True, src_address=srcip, dst_address=dstip, \
                        vni=vxid, decap_next_index=decap_next_idx)
		if rv.retval != 0:
			print("Error:", rv)
                        return None
		else:
			print("OK:", rv)
                        return rv.sw_if_index
 
	def delete_vxlan_vtep(self, src, dst, vxid):
		srcip = str(IPv4Address(unicode(src)).packed)
		dstip = str(IPv4Address(unicode(dst)).packed)
		rv = vpp_ctl.vpp.vxlan_add_del_tunnel(is_add=False, src_address=srcip, dst_address=dstip, vni=vxid)
		if rv.retval != 0:
			#print("Error:", rv)
                        return None
		else:
			#print("OK:", rv)
                        return None

        def get_vxlan_vtep(self):
                rv = vpp_ctl.vpp.vxlan_tunnel_dump(sw_if_index=ctypes.c_uint32(-1).value)
                retval_vxlan = []
                for intf in rv:
                    if intf.is_ipv6:
                        retval_vxlan.append({    'vxid': intf.vni, 
                                                'src': str(ip_address(intf.src_address)), 
                                                'dst': str(ip_address(intf.dst_address)), 
                                                'sw_if_index': intf.sw_if_index })
                    else:
                        retval_vxlan.append({    'vxid': intf.vni, 
                                                'src': str(ip_address(intf.src_address[:4])), 
                                                'dst': str(ip_address(intf.dst_address[:4])), 
                                                'sw_if_index': intf.sw_if_index })
                return retval_vxlan
 
        def add_xconnect_idx(self, idx1, idx2):
                rv = self.vpp.sw_interface_set_l2_xconnect(enable=True, rx_sw_if_index=idx1, tx_sw_if_index=idx2)
		if rv.retval != 0:
			print("Error:", rv)
                        return rv

                rv = self.vpp.sw_interface_set_l2_xconnect(enable=True, rx_sw_if_index=idx2, tx_sw_if_index=idx1)
		if rv.retval != 0:
                        self.vpp.sw_interface_set_l2_xconnect(enable=False, rx_sw_if_index=idx1, tx_sw_if_index=idx2)
			print("Error:", rv)
                        return rv

                return None

        def del_xconnect_idx(self, idx1, idx2):
                rv1 = self.vpp.sw_interface_set_l2_xconnect(enable=False, rx_sw_if_index=idx1, tx_sw_if_index=idx2)
                rv2 = self.vpp.sw_interface_set_l2_xconnect(enable=False, rx_sw_if_index=idx2, tx_sw_if_index=idx1)
		if rv1.retval != 0 or rv2.retval != 0:
                        return (rv1, rv2)
                return None

        def get_xconnect(self):
                rv = self.vpp.l2_xconnect_dump()
                xconnect_vals = set([])
                for i in rv:
                    if i.rx_sw_if_index < i.tx_sw_if_index:
                        xconnect_vals.add((i.rx_sw_if_index, i.tx_sw_if_index))
                return list(xconnect_vals)

        def get_vxlan_ifindex(self, src, dst, vxid):
                rv = self.vpp.vxlan_tunnel_dump(sw_if_index=ctypes.c_uint32(-1).value)
                for intf in rv:
                    if intf.is_ipv6:
                        if intf.vni == vxid and \
                           ip_address(intf.src_address) == ip_address(unicode(src)) and \
                           ip_address(intf.dst_address) == ip_address(unicode(dst)):
                               return intf.sw_if_index
                    else:
                        print("i:", intf.vni, ip_address(intf.src_address[:4]), \
                                ip_address(intf.dst_address[:4]), intf.sw_if_index)
                        if intf.vni == vxid and \
                           ip_address(intf.src_address[:4]) == ip_address(unicode(src)) and \
                           ip_address(intf.dst_address[:4]) == ip_address(unicode(dst)):
                               return intf.sw_if_index
                return None

	def disconnect(self):
		rc = vpp_ctl.vpp.disconnect()
		if rc != 0:
			print(rc)

if __name__ == "__main__":
    v = vpp_ctl()
    print (v.get_xconnect())
    v.disconnect()
