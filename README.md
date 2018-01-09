# kokonet: simple CNI plugin for point-to-point based network in Kubernetes

# What is 'kokonet'?

`kokonet` provides simple point-to-point based network (using vxlan for now) for Kubernetes as following chaining topology.
<rawtext>
+-------+       +-------+         +-------+
| Pod A |-------| Pod B |---------| Pod C |
+-------+       +-------+         +-------+
</rawtext>

# Components

`kokonet` consists of following components:

- cni plugin (kokonet-cni)
This plugin adds one or more vxlan interface to switch
- network manager (kokonet-mgr)
This manager controls kubernetes node and software switch and connects containers
- node agent (kokonet-agent)
This agent sits on kubernetes node and it changes containers' ip address
- software switch (kokonet-vpp)
This component has VPP (from fd.io) and its driver. All container's data traffic goes to this switch and it connects each containers' endpoints

# How to install?

To be written in wiki

# Future works

- Document
- GUI (well, if possible)
- Other network topology

# FAQ (Frequentry Asked Question)

Please file issue ticket in github if you have question about kokonet.
