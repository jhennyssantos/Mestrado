#!/usr/bin/python
#"""
#Script created by VND - Visual Network Description (SDN version)
#"""
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, IVSSwitch, UserSwitch
from mininet.link import Link, TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
def topology():
	"Create a network."
	net = Mininet( controller=RemoteController, link=TCLink, switch=OVSKernelSwitch )
	print "*** Creating nodes"
	s1 = net.addSwitch( 's1', listenPort=6673, mac='00:00:00:00:00:01' )
	s2 = net.addSwitch( 's2', listenPort=6674, mac='00:00:00:00:00:02' )
	
	h3 = net.addHost( 'h3', mac='00:00:00:00:00:03', ip='10.0.0.3/8' )
	h4 = net.addHost( 'h4', mac='00:00:00:00:00:04', ip='10.0.0.4/8' )
	h5 = net.addHost( 'h5', mac='00:00:00:00:00:05', ip='10.0.0.5/8' )
	h6 = net.addHost( 'h6', mac='00:00:00:00:00:06', ip='10.0.0.6/8' )
	h7 = net.addHost( 'h7', mac='00:00:00:00:00:07', ip='10.0.0.7/8' )
	h8 = net.addHost( 'h8', mac='00:00:00:00:00:08', ip='10.0.0.8/8' )
	h9 = net.addHost( 'h9', mac='00:00:00:00:00:09', ip='10.0.0.9/8' )
	h10 = net.addHost( 'h10', mac='00:00:00:00:00:10', ip='10.0.0.10/8' )

	c20 = net.addController( 'c20' )

	h22 = net.addHost( 'h22', mac='00:00:00:00:00:22', ip='10.0.0.22/8' )
	h23 = net.addHost( 'h23', mac='00:00:00:00:00:23', ip='10.0.0.23/8' )
	h24 = net.addHost( 'h24', mac='00:00:00:00:00:24', ip='10.0.0.24/8' )
	h25 = net.addHost( 'h25', mac='00:00:00:00:00:25', ip='10.0.0.25/8' )
	print "*** Creating links"

	net.addLink(h25, s1, 0, 13)
	net.addLink(h24, s1, 0, 12)
	net.addLink(s1, h23, 11, 0)
	net.addLink(h22, s1, 0, 10)
	net.addLink(s1, s2, 9, 3)
	net.addLink(s2, h5, 2, 0)
	net.addLink(s1, h10, 8, 0)
	net.addLink(s1, h9, 7, 0)
	net.addLink(s1, h8, 6, 0)
	net.addLink(s1, h7, 5, 0)
	net.addLink(s1, h6, 4, 0)
	net.addLink(s1, h4, 3, 0)
	net.addLink(s1, h3, 2, 0)
	net.addLink(s1, s2, 1, 1)
	
	print "*** Starting network"
	net.start()
	c20.start()
	
	print "*** Running CLI"
	CLI( net )

	print "*** Stopping network"
	net.stop()
if __name__ == '__main__':
	setLogLevel( 'info' )
	topology()
