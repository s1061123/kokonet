# kokonet: simple CNI plugin for point-to-point based network in Kubernetes

# Current status

Not officially released yet. Update documents and some tools, then released. Stay tune!
Feel free to ask any detail to me (= Tomofumi Hayashi / s1061123@gmail.com)

# What is 'kokonet'?

`kokonet` provides simple point-to-point based network (using vxlan for now) for Kubernetes as following chaining topology.

```
+-------+       +-------+         +-------+
| Pod A |-------| Pod B |---------| Pod C |
+-------+       +-------+         +-------+
```

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
