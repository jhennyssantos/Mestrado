#!/usr/bin/python

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Link
from mininet.link import TCLink, TCIntf
from mininet.node import OVSController, RemoteController, Node, Switch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os
from time import strftime,localtime,sleep

INITIAL_BW = 50

def create_topology():
    when = strftime("%Y-%m-%d_%H:%M:%S", localtime())
    info( '========== Experiment %s ==========\n' % (when) )
    net = Mininet (link=TCLink, autoSetMacs=True)
    info('\n')
    info('\n')
    info( '*** Adding switches\n' )
    s1 = net.addSwitch('s1')#, protocols='OpenFlow13')
    s2 = net.addSwitch('s2')#, protocols='OpenFlow13')
    s3 = net.addSwitch('s3')#, protocols='OpenFlow13')
    s4 = net.addSwitch('s4')#, protocols='OpenFlow13')
    
    linkopts=dict(bw=50,  delay='5ms')#,   use_htb=True)#, loss=0,max_queue_size=100)
    
    info( '*** Adding switch links\n' )
    net.addLink(s1,s2, bw = INITIAL_BW)#, bw=50, delay='5ms')#,**linkopts)
    net.addLink(s2,s3, bw = INITIAL_BW)#, bw=50, delay='5ms')#,**linkopts)
    net.addLink(s3,s4, bw = INITIAL_BW)#, bw=50, delay='5ms')#,**linkopts)
    net.addLink(s4,s1, bw = INITIAL_BW)#, bw=50, delay='5ms')#,**linkopts)
    
    info( '*** Adding hosts\n' )
    h1 = net.addHost( 'h1', ip='10.0.0.1/24' )
    h2 = net.addHost( 'h2', ip='10.0.0.2/24' )
    h3 = net.addHost( 'h3', ip='10.0.0.3/24' )
    h4 = net.addHost( 'h4', ip='10.0.0.4/24' )
    
    info( '*** Adding host links\n' )
    net.addLink(s1,h1)#,**linkopts)
    net.addLink(s2,h2)#,**linkopts)
    net.addLink(s3,h3)#,**linkopts)
    net.addLink(s4,h4)#,**linkopts)

    # Workaround parte 1 - para adicionar interface externa ao host h4
    net.addLink(s4,h4)

    net.addController('c', controller=RemoteController, ip='127.0.0.1', port=6633)
    net.build()
    net.start()

    # Workaround parte 2 - para adicionar interface externa ao host h4
    s4.cmd("ovs-vsctl del-port s4 s4-eth4")
    s4.cmd("ifconfig s4-eth4 10.10.10.2/30 up") ## ip do hospedeiro / controlador
    h4.cmd("ifconfig h4-eth1 10.10.10.1/30 up") ## ip do h4

    # Workaround parte 3 - configurar o h4 como gateway da rede
    h4.cmd("sysctl net.ipv4.ip_forward=1")
    h4.cmd("iptables -t nat -I POSTROUTING -o h4-eth1 -j MASQUERADE")
    h1.cmd("route add default gw 10.0.0.4")
    h2.cmd("route add default gw 10.0.0.4")
    h3.cmd("route add default gw 10.0.0.4")
    
    #info( '*** Starting iperf3 servers on h2 and h4 and h6\n' )
    #h4.cmd("iperf3 -s -i 5 --logfile /tmp/saida-iperf-server-h4-%s.dat &" % (when))
    #sleep(2)
    
    info( '*** Running CLI\n' )
    CLI( net )
    info( '*** Stopping Mininet\n' )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    create_topology()
