# Copyright (C) Italo Valcy S Brito <italovalcy@ufba.br>
#
# Simple multiswitch L2 application
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

from ryu.base import app_manager
from ryu.controller import ofp_event,dpset
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, tcp, udp
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
import networkx as nx
from queue_manager import QueueManager
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
from ryu.lib.ovs import bridge
#from ovs_vsctl import VSCtl


myapp_name = 'simple_switch_api'
base_url = '/simpleswitch'

#  Criacao de variavel global

TOTAL_BANDWIDTH = 6000000

s1_eth1 = QueueManager("s1-eth1")
s1_eth1.set_max_bw(TOTAL_BANDWIDTH)

s3_eth2 = QueueManager("s3-eth2")
s3_eth2.set_max_bw(TOTAL_BANDWIDTH)

s2_eth3 = QueueManager("s2_eth3")
s2_eth3.set_max_bw(TOTAL_BANDWIDTH)

s2_eth1 = QueueManager("s2-eth1")
s2_eth1.set_max_bw(TOTAL_BANDWIDTH)

s1_eth3 = QueueManager("s1-eth3")
s1_eth3.set_max_bw(TOTAL_BANDWIDTH)

s3_eth1 = QueueManager("s3-eth1")
s3_eth1.set_max_bw(TOTAL_BANDWIDTH)



def reserv_bw (switch_port, queue, bw):
	list_queue = []
	list_bw = []

	if isistance (queue, list):
		for q in queue:
			list_queue.append(q)

	else:
		list_queue.append(queue)


	if isistance (bw, list):
		for each_bw in bw:
			list_bw.append(each_bw)

	else:
		list_bw.append(bw)


	switch_port.set_list_queue(list_queue)
	switch_port.set_queue_bw(list_bw)
	switch_port.update_queue()




class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        #Inicializa a tabela de enderecos MAC
        self.mac_to_port = {}
        self.mac_to_sw = {}
        self.net = nx.DiGraph()
        self.topology_api_app = self
        self.oldpath = None
        self.src = None
        self.dst = None
        self.fluxos_ativos = {}
        self.ovs_bridge = {}
        wsgi = kwargs['wsgi']
        wsgi.register(SimpleSwitchWSGIApp,{myapp_name: self})
        # OVSDB_ADDR = 'tcp:127.0.0.1:6632'
        # ovs_vsctl = VSCtl(OVSDB_ADDR)


    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def datapath_handler(self, ev):
        if ev.enter:
            ports = []
            for p in ev.ports:
                if p.port_no != ev.dp.ofproto.OFPP_LOCAL:
                    ports.append(p.port_no)
            self.net.add_node(ev.dp.id, {'all_ports': ev.ports, 'ports': ports, 'conn': ev.dp})
            self.logger.debug('OFPStateChange switch entered: datapath_id=0x%016x ports=%s' % (ev.dp.id, ev.ports))
        else:
            self.logger.debug('OFPStateChange switch leaves: datapath_id=0x%016x' % (ev.dp.id))
            self.net.remove_node(ev.dp.id)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
    	global s1_eth1, s3_eth2, s2_eth3, s2_eth1, s1_eth3, s3_eth1
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        #self.add_flow(datapath, 0, match, actions)

        print "sw == %s" % (str(datapath.id)) 
        if str(datapath.id) == '1':
            # H4 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            # H6 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(1)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s1_eth1, 0, "4000000")
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(3)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s2_eth1, 0, "4000000")


            # H5 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

        elif str(datapath.id) == '3':
            # H4 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s3_eth2, 0, "4000000")
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s3_eth1, 0, "4000000")

            # H3 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(2)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s3_eth2, 0, "4000000")
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s3_eth1, 0, "4000000")

            # H3 <==> H2
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

        elif str(datapath.id) == '2':
            # H4 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(3)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s2_eth3, 0, "4000000")
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            actions.insert(0,parser.OFPActionSetQueue(0))
            self.add_flow(datapath, 0, match, actions)
            reserv_bw(s2_eth1, 0, "4000000")

            # H2 <==> H3
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

        elif str(datapath.id) == '4':
            # H4 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            # H4 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            # H2 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            # H3 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            # H5 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            
            # H2 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            
            # # H2 <==> H6
            # match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:06')
            # actions = [parser.OFPActionOutput(2)]
            # self.add_flow(datapath, 0, match, actions)
            # match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:02')
            # actions = [parser.OFPActionOutput(1)]
            # self.add_flow(datapath, 0, match, actions)
        

        elif str(datapath.id) == '6':
            # H4 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            # H6 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            # H5 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H5 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            
        

        elif str(datapath.id) == '5':
            # H4 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H5 <==> H1
            match = parser.OFPMatch(eth_src='00:00:00:00:00:01', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:01')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)

            # H5 <==> H4
            match = parser.OFPMatch(eth_src='00:00:00:00:00:04', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:04')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H2 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:02', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:02')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H3 <==> H5
            match = parser.OFPMatch(eth_src='00:00:00:00:00:03', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:03')
            actions = [parser.OFPActionOutput(1)]
            self.add_flow(datapath, 0, match, actions)

            # H5 <==> H6
            match = parser.OFPMatch(eth_src='00:00:00:00:00:05', eth_dst='00:00:00:00:00:06')
            actions = [parser.OFPActionOutput(2)]
            self.add_flow(datapath, 0, match, actions)
            match = parser.OFPMatch(eth_src='00:00:00:00:00:06', eth_dst='00:00:00:00:00:05')
            actions = [parser.OFPActionOutput(3)]
            self.add_flow(datapath, 0, match, actions)


    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def remove_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
                                    match=match)
        datapath.send_msg(mod)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)

        links = []
        backbone_ports = {}
        for link in links_list:
            links.append((link.src.dpid,link.dst.dpid,{
                'sport':link.src.port_no, 'dport':link.dst.port_no}))
            backbone_ports.setdefault(link.src.dpid, [])
            backbone_ports[link.src.dpid].append(link.src.port_no)
        self.logger.debug("add_nodes: %s" % (switches))
        self.net.add_nodes_from(switches)
        self.logger.debug("add_edges: %s" % (links))
        self.net.add_edges_from(links)
	print "@@@ Sw: %s" % str(switches)
        print "@@@ links: %s " % str(links)
        for sw in backbone_ports:
            self.net.node[sw]['backbone_ports'] = backbone_ports[sw]
            self.logger.debug("backbone_ports[%s] = %s " % (sw, backbone_ports[sw]))
      
        print  self.net.nodes()
        print  self.net.edges()


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # the flows are configured statically
        return

        msg = ev.msg
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        #ipv4_pkt = pkt.get_protocol(ipv4.ipv4)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

 
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #remote_addr = req.remote_addr
        # #obter o numero da porta em que foi recebida a mensagem de packet in
        in_port = msg.match['in_port']
        dst = eth.dst
        src = eth.src
        #self.logger.info("origem e: %s", src)

        dpid = datapath.id
        
        self.src = dpid

        # #aprender o endereco MAC para evitar FLOOD uma proxima vez
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("destino e: %s", dst)

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time, except if received
        # in backbone port
        if in_port not in self.net.node[dpid].get('backbone_ports', []):
            self.mac_to_port[dpid][src] = in_port
            self.mac_to_sw[src] = [dpid, in_port]

        if dst in self.mac_to_sw:
            dst_sw = self.mac_to_sw[dst][0]
            out_port = self.mac_to_sw[dst][1]
        else:
            dst_sw = None
            out_port = ofproto.OFPP_FLOOD


        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:



            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                source_address = ip.src
                destination_address = ip.dst

                if ((source_address == "10.0.0.1") and (destination_address == "10.0.0.2")):
                # eth.src = "00:00:00:00:00:01"
                # eth.dst = "00:00:00:00:00:02"
                    match = parser.OFPMatch(eth_dst=dst)
                    actions = [parser.OFPActionOutput(action_out_port)]
                    self.add_flow(self.net.node[sw]['conn'], 1, match, actions, buff_id)
                    indice = "%s-%s" % (src, dst)
                    self.fluxos_ativos[indice] = {'src' : src, 'dst' : dst, 'in_port' : in_port, 'out_port' : out_port}

                    self.logger.info("Origem: %s, Destino: %s, in_port: %s, out_port: %s", source_address, destination_address, in_port, out_port)

                elif ((source_address == "10.0.0.1") and (destination_address == "10.0.0.6")):
                 # eth.src = "00:00:00:00:00:01"
                 # eth.dst = "00:00:00:00:00:02"
                    match = parser.OFPMatch(eth_dst=dst)
                    actions = [parser.OFPActionOutput(action_out_port)]
                    self.add_flow(self.net.node[sw]['conn'], 1, match, actions, buff_id)
                    indice = "%s-%s" % (src, dst)
                    self.fluxos_ativos[indice] = {'src' : src, 'dst' : dst, 'in_port' : in_port, 'out_port' : out_port}

                    self.logger.info("Origem: %s, Destino: %s, in_port: %s, out_port: %s", source_address, destination_address, in_port, out_port)

            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
                
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)







    def set_queue(self, dpid, port_name):
        # inicializar a conexao com o switch
        if self.ovs_bridge.get(dpid, None) is None:
            ovs_bridge = bridge.OVSBridge(self.CONF, dpid, "tcp:127.0.0.1:6632")
            self.ovs_bridge[dpid] = ovs_bridge
            try:
                ovs_bridge.init()
            except:
                print 'ERROR: ovsdb addr is not available.'
                return False

        # criacao da fila
        try:
            queue_type = 'linux-htb'
            queue_config = [{"max-rate": "500000"}, {"min-rate": "2000000"}] ## TODO: e se houverem mais de uma fila em um switch?!
            self.ovs_bridge[dpid].set_qos(port_name, type=queue_type,
                                        max_rate=None,
                                        queues=queue_config)
        except Exception as msg:
            print "ERROR: falha ao criar a fila - %s" % (msg)
            return False

        return True


    def reservarecurso(self, src, dst, path, output_ports):
   # switch_list = get_switch(self.topology_api_app, None)
   # switches=[switch.dp.id for switch in switch_list]
     	for sw in path:
#		if sw = "s1" and port_name = "s1-eth1"
#			print "Vem do H1 no Sw1"
			#queue_type = 'linux-htb'

            # TODO: criar a fila de QoS com Minimal-Rate no switch sw, conforme
            #     curl -X POST -d '{"port_name": "s1-eth1", "type": "linux-htb", "max_rate": "1000000", "queues": [{"max_rate": "500000"}, {"min_rate": "800000"}]}' http://localhost:8080/qos/queue/0000000000000001
            output_port = output_ports[sw]
            status = self.set_queue(sw, output_port)
            if status:
     	        # TODO: modificar o fluxo de src para dst nesse switch fazendo com que a action agora seja set_queue=1
                #      # curl -X POST -d '{"match": {"nw_dst": "10.0.0.1", "nw_proto": "UDP", "tp_dst": "5002"}, "actions":{"queue": "1"}}' http://localhost:8080/qos/rules/0000000000000001
                pass





    def modifica_fluxos(self, src, dst, newpath):
        indice = "%s-%s" % (src, dst)

        in_port = self.fluxos_ativos[indice]['in_port']
        out_port = self.fluxos_ativos[indice]['out_port']
        oldpath = self.fluxos_ativos[indice]['path']
        for i in range(len(newpath)-1,-1,-1):
            sw = newpath[i]
            if i == 0: # first switch
                match_in_port = in_port
            else:
                prev_sw = newpath[i-1]
                match_in_port = self.net.edge[prev_sw][sw]['dport']
            if i == len(newpath)-1:
                action_out_port = out_port
            else:
                next_sw = newpath[i+1]
                action_out_port = self.net.edge[sw][next_sw]['sport']
            self.logger.info("==> add_flow sw=%s match_in_port=%s action_out_port=%s", sw, match_in_port, action_out_port)
            datapath = self.net.node[sw]['conn']
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(in_port=match_in_port,
                    eth_dst=dst, eth_src=src)
            actions = [parser.OFPActionOutput(action_out_port)]
            self.add_flow(datapath, 1, match, actions)
        for sw in set(oldpath) - set(newpath):
            print "TODO: remover fluxos de %s" % (sw)
            datapath = self.net.node[sw]['conn']
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_dst=dst, eth_src=src)
            self.remove_flow(datapath, match)
        # TODO: Remover os fluxos da rota antiga cujos nos nao pertencam a rota nova!

class SimpleSwitchWSGIApp(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(SimpleSwitchWSGIApp, self).__init__(req, link, data, **config)
        self.myapp = data[myapp_name]

    @route(myapp_name, base_url + '/changeQuality/{oldqlt}/{newqlt}', methods=['GET'])
    def change_quality(self, req, **kwargs):
        print "KWARGS=%s" % (kwargs)
        print "RemoteAddr=|%s|" % (req.remote_addr)
        remote_addr = req.remote_addr
        oldqlt = int(kwargs['oldqlt'])
        newqlt = int(kwargs['newqlt'])
        if newqlt < oldqlt:
            self.myapp.reservarecurso(remote_addr)
        body = json.dumps([])
        return Response(content_type='application/json', body=body)
