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
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
import networkx as nx
from webob import Response
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
from ryu.lib.ovs import bridge
#from ovs_vsctl import VSCtl


myapp_name = 'simple_switch_api'
base_url = '/simpleswitch'
parser=''

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
        self.qos_list = ['00:00:00:00:00:01']
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
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        global parser
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
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        print "\n$$$$$$$$\nmatch: %s"   % match
        print "Action: %s " % actions

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
        msg = ev.msg
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #obter o numero da porta em que foi recebida a mensagem de packet in
        in_port = msg.match['in_port']


        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.src = dpid


        #aprender o endereco MAC para evitar FLOOD uma proxima vez
        self.mac_to_port.setdefault(dpid, {})


        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time, except if received
        # in backbone port
        if in_port not in self.net.node[dpid].get('backbone_ports', []):
            self.mac_to_port[dpid][src] = in_port
            self.mac_to_sw[src] = [dpid, in_port]

        print "### %s" % dst     
        if dst in self.mac_to_sw:
            dst_sw = self.mac_to_sw[dst][0]
            out_port = self.mac_to_sw[dst][1]
        else:
            dst_sw = None

        # if destination switch (dst_sw) is known, then we just search for a
        # path on the graph and install a flow along this path. Otherwise, we
        # flood the packet into the access ports for all switches


        if dst_sw:
            path = nx.shortest_path(self.net, dpid, dst_sw)
            self.oldpath = path
            self.dst = dst_sw
            print "\n \n Caminho ", path

            self.logger.info("==> path(src=%s,dst=%s): %s", dpid, dst_sw, path)
            
            for i in range(len(path)-1,-1,-1):
                sw = path[i]

                buff_id = None
                if i == 0: # first switch
                    match_in_port = in_port
                    buff_id = msg.buffer_id
                else:
                    prev_sw = path[i-1]
                    match_in_port = self.net.edge[prev_sw][sw]['dport']
                if i == len(path)-1:
                    action_out_port = out_port
                else:
                    next_sw = path[i+1]
                    action_out_port = self.net.edge[sw][next_sw]['sport']
                self.logger.info("==> add_flow sw=%s match_in_port=%s action_out_port=%s", sw, match_in_port, action_out_port)
                match = parser.OFPMatch(eth_dst=dst)
                #actions.insert(0,parser.OFPActionSetQueue(0))

                actions = [parser.OFPActionOutput(action_out_port)]
                #actions.insert(0,parser.OFPActionSetQueue(0))
                self.add_flow(self.net.node[sw]['conn'], 1, match, actions, buff_id)
            indice = "%s-%s" % (src, dst)
            self.fluxos_ativos[indice] = {'src' : src, 'dst' : dst, 'in_port' : in_port, 'out_port' : out_port, 'path' : path}
        else:
            #self.logger.info("===> Destino nao conhecido")
            for sw in self.net.nodes():
                access_ports = set(self.net.node[sw]['ports']) - set(self.net.node[sw].get('backbone_ports', []))
                self.logger.info("=====> sw=%s ports=%s backbone_ports=%s access_ports=%s" %
                        (sw, self.net.node[sw]['ports'],  self.net.node[sw].get('backbone_ports', []), access_ports))
                actions = []
                for p in access_ports:
                    actions = [parser.OFPActionOutput(p)]
                data = msg.data
                datapath = self.net.node[sw]['conn']
                out = parser.OFPPacketOut(datapath=datapath,
                        in_port = ofproto.OFPP_LOCAL,
                        buffer_id=ofproto.OFP_NO_BUFFER,
                        actions=actions, data=data)
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


    def reservarecurso(self, sw, src, dst, path, output_ports,mac_dst):
        
        output_port = output_ports[dst]
        match = parser.OFPMatch(eth_dst=mac_dst)

        actions = [parser.OFPActionOutput(output_port)]
        actions.insert(0,parser.OFPActionSetQueue(0))
        # if ALGO:
        #     actions.insert(0,parser.OFPActionSetQueue(0))
        # elif ALGO:
        #     actions.insert(0,parser.OFPActionSetQueue(0))
        # elif ALGO:
        #     actions.insert(0,parser.OFPActionSetQueue(0))
        print "\n@@@@@\nmatch: %s"   % match
        print "Action: %s " % actions
        self.add_flow(self.net.node[sw]['conn'], 1, match, actions)
        self.logger.info("==> OutPut=%s match_dst=%s action=%s", output_port, match, actions)
        #status = self.set_queue(sw, output_port)
        # if status:
            #   # TODO: modificar o fluxo de src para dst nesse switch fazendo com que a action agora seja set_queue=1
        #     #      # curl -X POST -d '{"match": {"nw_dst": "10.0.0.1", "nw_proto": "UDP", "tp_dst": "5002"}, "actions":{"queue": "1"}}' http://localhost:8080/qos/rules/0000000000000001
        #     pass



    def novarota(self, sw, client_ip):
        #newpath = nx.shortest_path(self.net, self.src, self.dst)

        """
        			h6 -- sw6---- sw5 -- h5 (10.0.0.5)
       					   |	   |
         (10.0.0.1) h1 -- sw1     sw4 -- h4 (10.0.0.4)
                            |      |
         (10.0.0.2) h3 -- sw3-----sw2 -- h2 (10.0.0.3)

        """
        src=''
        dst='' 
        curpath=''
        output_ports=''

        if client_ip == "10.0.0.1":
            curpath = [1,3,2]

        elif client_ip == "10.0.0.3":
            curpath = [3,2]

        elif client_ip == "10.0.0.4":
            curpath = [4,2]

        elif client_ip == "10.0.0.5":
            curpath = [5,4,2]

        elif client_ip == "10.0.0.6":
            curpath = [6,5,4,2]

        for idx,sw in enumerate(curpath):
            if sw == 1:
                if idx < len(curpath) -1:
                    dst = "h1"
                    mac_dst="00:00:00:00:00:01"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]

                print "Modifica fluxos do no 1"
                output_ports = {"s6": 2, "s3": 1,"h1": 3}

            elif sw == 2:
                if idx < len(curpath) -1:
                    dst = "h2"
                    mac_dst="00:00:00:00:00:02"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]

                print "modifica fluxos do no 3"
                #output_ports = {3: 2, 2: 1}
                output_ports = {"s3": 1, "s4": 2, "h2": 3}

            elif sw == 3:
                if idx < len(curpath) -1:
                    dst = "h3"
                    mac_dst = "00:00:00:00:00:03"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]

                print "modifica fluxos do no 4"
                # output_ports = {4: 1, 2: 2}
                output_ports = {"s1": 1, "s2": 2, "h3": 3}

            elif sw == 4:
                if idx < len(curpath) -1:
                    dst = "h4"
                    mac_dst = "00:00:00:00:00:04"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]

                print "modifica fluxos do no 5"
                output_ports = {"s5": 2,"s2": 1, "h4": 3}

            elif sw == 5:
                if idx < len(curpath) -1:
                    dst = "h5"
                    mac_dst = "00:00:00:00:00:05"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]
                    

                print "modifica fluxos do no 6"
    #            output_ports = {6: "s6-eth1", 5: "s5-eth1", 4: "s4-eth1", 2: "s2-eth3"}
                output_ports = {"s6": 2, "s4": 1,"h5": 3}
        
            elif sw == 6:
                if idx < len(curpath) -1:
                    dst = "h6"
                    mac_dst = "00:00:00:00:00:06"
                else:
                    dst = "s%s" % curpath[idx +1]
                    mac_dst = "00:00:00:00:00:0%s" % curpath[idx +1]
                    
                print "modifica fluxos do no 6"
    #            output_ports = {6: "s6-eth1", 5: "s5-eth1", 4: "s4-eth1", 2: "s2-eth3"}
                output_ports = {"s5": 1, "s1": 2, "h6": 3}
                
            self.reservarecurso(src, dst, curpath, output_ports,mac_dst)
#         if client_ip == "10.0.0.1":
#             # oldpath = sw1 <-> sw3 <-> sw2
#             # newpath = sw1 <-> sw6 <-> sw5 <-> sw4 <-> sw2
#             print "Modifica fluxos do no 1"
#             curpath = [1,3,2]
#             output_ports = {"00:00:00:00:00:01": 1, "00:00:00:00:00:03": 2, "00:00:00:00:00:02": 1}
#             src = "00:00:00:00:00:01"
#             dst = "00:00:00:00:00:01"
#             self.reservarecurso(src, dst, curpath, output_ports)

#         elif client_ip == "10.0.0.3":

#             print "modifica fluxos do no 3"
#             curpath = [3,2]
#             #output_ports = {3: 2, 2: 1}
#             output_ports = {"00:00:00:00:00:03": 2, "00:00:00:00:00:02": 1}
#             src = "00:00:00:00:00:03"
#             dst = "00:00:00:00:00:03"
#             self.reservarecurso(src, dst, curpath, output_ports)

#             # oldpath = sw3 <-> sw2
#             # newpath = sw3 <-> sw1 <-> sw6 <-> sw5 <-> sw4 <-> sw2

#         elif client_ip == "10.0.0.4":

#             print "modifica fluxos do no 4"
#             curpath = [4,2]
#             # output_ports = {4: 1, 2: 2}
#             output_ports = {"00:00:00:00:00:04": 1, "00:00:00:00:00:02": 2}
#             src = "00:00:00:00:00:04"
#             dst = "00:00:00:00:00:04"
#             self.reservarecurso(src, dst, curpath, output_ports)

#             # oldpath = sw4 <-> sw2
#             # newpath = sw4 <-> sw5 <-> sw6 <-> sw1 <-> sw3 <-> sw2

#         elif client_ip == "10.0.0.5":

#             print "modifica fluxos do no 5"
#             curpath = [5,4,2]
#             output_ports = {"00:00:00:00:00:05": 1, "00:00:00:00:00:04": 2, "00:00:00:00:00:02": 2}
#             src = "00:00:00:00:00:05"
#             dst = "00:00:00:00:00:05"
#             self.reservarecurso(src, dst, curpath, output_ports)

#             # oldpath = sw5 <-> sw4 <-> sw2
#             # newpath = sw5 <-> sw6 <-> sw1 <-> sw3 <-> sw2

#         elif client_ip == "10.0.0.6":

#             print "modifica fluxos do no 6"
#             curpath = [6,5,4,2]
# #            output_ports = {6: "s6-eth1", 5: "s5-eth1", 4: "s4-eth1", 2: "s2-eth3"}
#             output_ports = {"00:00:00:00:00:06": 1, "00:00:00:00:00:05": 1, "00:00:00:00:00:04": 2, "00:00:00:00:00:02": 2}
#             src = "00:00:00:00:00:06"
#             dst = "00:00:00:00:00:06"
#             self.reservarecurso(src, dst, curpath, output_ports)

            # oldpath = sw6 <-> sw5 <-> sw4 <-> sw2
            # newpath = sw6 <-> sw1 <-> sw3 <-> sw2

        #print "\n \n RECALCULANDO ", newpath

        #if self.oldpath != newpath:
        #    return newpath
        #return self.oldpath

        # 1) saber qual era a rota antiga de origem para destino
        # 2) procurar uma nova rota de origem para destino que nao seja a antiga
        # 3) modificar a tabela de fluxo dos switches para essa nova rota

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
            self.myapp.novarota(remote_addr)
        body = json.dumps([])
        return Response(content_type='application/json', body=body)
