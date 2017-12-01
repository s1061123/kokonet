// Copyright 2017 CNI authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"encoding/json"
	//"errors"
	"fmt"
	"net"
	"runtime"
	"os"
	"bytes"

	"net/http"

	"github.com/containernetworking/cni/pkg/invoke"
	"github.com/containernetworking/cni/pkg/skel"
	"github.com/containernetworking/cni/pkg/types"
	"github.com/containernetworking/cni/pkg/types/current"
	"github.com/containernetworking/cni/pkg/version"
	//"github.com/containernetworking/plugins/pkg/ip"
	//"github.com/containernetworking/plugins/pkg/ipam"

	koko "github.com/redhat-nfvpe/koko/api"
)

// K8sArgs is the valid CNI_ARGS used for Kubernetes
type K8sArgs struct {
	types.CommonArgs
	K8S_POD_NAME               types.UnmarshallableString
	K8S_POD_NAMESPACE          types.UnmarshallableString
	K8S_POD_INFRA_CONTAINER_ID types.UnmarshallableString
}

type PluginConf struct {
	types.NetConf
	RuntimeConfig *struct {
		SampleConfig map[string]interface{} `json:"sample"`
	} `json:"runtimeConfig"`

	Delegate    map[string]interface{} `json:"delegate"`
	MgmtNetwork map[string]interface{} `json:"mgmt_network"`
	// koko specific parameters
	ParentIF	string		`json:"vtep_parent_if"`
	SrcIpAddress    string		`json:"vtep_src_ip"`
	InterfaceNames	[]string	`json:"interfaces"`
	VtepIP		string		`json:"vtep_ip"`
	ControllerURI	string		`json:"controller_uri"`

	RawPrevResult *map[string]interface{} `json:"prevResult"`
	PrevResult    *current.Result         `json:"-"`
}

type NetworkManagerVtepReq struct {
	Hostip      string `json:"hostip"`
	Switchip    string `json:"switchip"`
	ContainerID string `json:"containerid"`
	IfName      string `json:"ifname"`
	CNIArgs     string `json:"cniargs"`
}

type NetworkManagerVtepRepl struct {
	Error	    string `json:"error"`
	Vnid	    int	`json:"vnid"`
	Address	    []string `json:"address"`
}

func init() {
	// this ensures that main runs only on main thread (thread group leader).
	// since namespace ops (unshare, setns) are done for a single thread, we
	// must ensure that the goroutine does not jump from OS thread to thread
	runtime.LockOSThread()
}

// parseConfig parses the supplied configuration (and prevResult) from stdin.
func parseConfig(stdin []byte) (*PluginConf, error) {
	conf := PluginConf{}

	if err := json.Unmarshal(stdin, &conf); err != nil {
		return nil, fmt.Errorf("failed to parse network configuration: %v", err)
	}

	// Parse previous result. Remove this if your plugin is not chained.
	if conf.RawPrevResult != nil {
		resultBytes, err := json.Marshal(conf.RawPrevResult)
		if err != nil {
			return nil, fmt.Errorf("could not serialize prevResult: %v", err)
		}
		res, err := version.NewResult(conf.CNIVersion, resultBytes)
		if err != nil {
			return nil, fmt.Errorf("could not parse prevResult: %v", err)
		}
		conf.RawPrevResult = nil
		conf.PrevResult, err = current.NewResultFromResult(res)
		if err != nil {
			return nil, fmt.Errorf("could not convert result to current version: %v", err)
		}
	}
	// End previous result parsing

	if conf.Delegate == nil {
		return nil, fmt.Errorf(`"delegate" is a required field in config, it should be the config of the main plugin to use`)
	}
	// Do any validation here
	if conf.ParentIF == "" {
		return nil, fmt.Errorf("ParentIF must be specified")
	}
	if len(conf.InterfaceNames) == 0 {
		return nil, fmt.Errorf("interfaceNames must be specified")
	}
	if conf.VtepIP == "" {
		return nil, fmt.Errorf("VtepIP must be specified")
	}
	if conf.ControllerURI == "" {
		return nil, fmt.Errorf("ControllerURI must be specified")
	}
	/*
	if conf.MgmtNetwork == nil {
		return nil, fmt.Errorf("MgmtNetwork: Err in delegate conf")
	}
	*/
	//XXX: Add more

	return &conf, nil
}

func getifname() (f func() string) {
	var interfaceIndex int
	f = func() string {
		ifname := fmt.Sprintf("net%d", interfaceIndex)
		interfaceIndex++
		return ifname
	}

	return
}

func delegateAdd(argif string, netconf map[string]interface{}) (*types.Result, error) {
	netconfBytes, err := json.Marshal(netconf)
	if err != nil {
		return nil, fmt.Errorf("Ratchet: error serializing multus delegate netconf: %v", err)
	}

	if os.Setenv("CNI_IFNAME", argif) != nil {
		return nil, fmt.Errorf("Ratchet: error in setting CNI_IFNAME")
	}

	result, err := invoke.DelegateAdd(netconf["type"].(string), netconfBytes)
	if err != nil {
		return nil, fmt.Errorf("Ratchet: error in invoke Delegate add - %q: %v", netconf["type"].(string), err)
	}

	return &result, nil
}

func delegateDel(argif string, netconf map[string]interface{}) error {
	netconfBytes, err := json.Marshal(netconf)
	if err != nil {
		return fmt.Errorf("Ratchet: error serializing multus delegate netconf: %v", err)
	}

	err = invoke.DelegateDel(netconf["type"].(string), netconfBytes)
	if err != nil {
		return fmt.Errorf("Ratchet: error in invoke Delegate del - %q: %v", netconf["type"].(string), err)
	}

	return err
}

// it sends REST API to get vnid and other info from network manager
func getNetworkEndpointInfo(isAdd bool, controllerURI string,
			    vtepreq NetworkManagerVtepReq) (repl NetworkManagerVtepRepl, err error) {
	var url string
	if isAdd {
		url = controllerURI + "vtep/new"
	} else {
		url = controllerURI + "vtep/delete"
	}

	jsonStr, err := json.Marshal(vtepreq)
	if err != nil {
		return repl, fmt.Errorf("json.Marshal failed")
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer([]byte(jsonStr)))
	if err != nil {
		return repl, fmt.Errorf("NewRequest failed")
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	defer resp.Body.Close()
	if err != nil {
		return repl, fmt.Errorf("Client send request failed")
	}
	if err := json.NewDecoder(resp.Body).Decode(&repl); err != nil {
		return repl, fmt.Errorf("Json decode error")
	}

	return repl, nil
}

func cmdAdd(args *skel.CmdArgs) error {
	conf, err := parseConfig(args.StdinData)
	if err != nil {
		return err
	}

	k8sArgs := K8sArgs{}
	if err = types.LoadArgs(args.Args, &k8sArgs); err != nil {
		return err
	}

	r, err := delegateAdd(args.IfName, conf.Delegate)
	if err != nil {
		return err
	}

	// if container is admin namespace, just add delegateAdd, then return
	if string(k8sArgs.K8S_POD_NAMESPACE) == "kube-system" {
		return nil
	}

	vtepreq := NetworkManagerVtepReq{}
	vtepreq.Hostip = conf.SrcIpAddress
	vtepreq.Switchip = conf.VtepIP
	vtepreq.ContainerID = args.ContainerID
	vtepreq.CNIArgs = args.Args

	vxlan := koko.VxLan{}
	conIF := koko.VEth{}
	conIF.NsName = args.Netns
	vxlan.ParentIF = conf.ParentIF
	vxlan.IPAddr = net.ParseIP(conf.VtepIP)
	for i := range conf.InterfaceNames {
		vtepreq.IfName = conf.InterfaceNames[i]
		conIF.LinkName = conf.InterfaceNames[i]

		repl, err := getNetworkEndpointInfo(true, conf.ControllerURI, vtepreq)
		if err != nil {
			return err
		}

		vxlan.ID = repl.Vnid
		if len(repl.Address) > 0 {
			for i := range repl.Address {
				ip, mask, err := net.ParseCIDR(repl.Address[i])
				if err != nil {
					return fmt.Errorf("failed to parse IP addr(%d) %s: %v",
							  i, repl.Address[i], err)
				}
				n := net.IPNet{
					IP: ip,
					Mask: mask.Mask,
				}
				conIF.IPAddr = append(conIF.IPAddr, n)
			}
		}
		if err := koko.MakeVxLan(conIF, vxlan); err != nil {
			return err
		}
	}

	result, _ := current.NewResultFromResult(*r)
	return types.PrintResult(result, conf.CNIVersion)
}

func cmdDel(args *skel.CmdArgs) error {
	conf, err := parseConfig(args.StdinData)
	if err != nil {
		return err
	}

	conIF := koko.VEth{}
	if args.Netns == "" {
		return nil
	}

	vtepreq := NetworkManagerVtepReq{}
	vtepreq.Hostip = conf.SrcIpAddress
	vtepreq.Switchip = conf.VtepIP
	vtepreq.ContainerID = args.ContainerID

	//XXX: Delete Interface
	conIF.NsName = args.Netns
	for i := range conf.InterfaceNames {
		conIF.LinkName = conf.InterfaceNames[i]
		vtepreq.IfName = conf.InterfaceNames[i]
		if err := conIF.RemoveVethLink(); err != nil {
			continue
			//return err
		}

		_, err := getNetworkEndpointInfo(false, conf.ControllerURI, vtepreq)
		if err != nil {
			continue
			//return err
		}
	}

	if err := delegateDel(args.IfName, conf.Delegate); err != nil {
		return err
	}

	return nil
}

func main() {
	skel.PluginMain(cmdAdd, cmdDel, version.PluginSupports("", "0.1.0", "0.2.0", version.Current()))
}
