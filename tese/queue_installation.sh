#!/usr/bin/bash
#===========================
#RYU CONTROLLER INSTALLATION
#===========================
#git clone git://github.com/osrg/ryu.git
#time sudo apt-get install python-eventlet python-routes pythonwebob python-paramiko
#sudo killall controller
#cd ryu
#sudo ./setup.py install
#sudo install ryu
#./bin/ryu-manager ryu/app/simple_switch.py
#===========
#SETTING QOS
#===========
#SET SWITCH:
ovs-vsctl set Bridge s1 protocols=OpenFlow13,OpenFlow14
ovs-vsctl set-manager ptcp:6632
#SET CONTROLLER AND ENABLE QOS:
sed '/OFPFlowMod(/,/)/s/)/, table_id=1)/'
ryu/ryu/app/simple_switch_13.py >
ryu/ryu/app/qos_simple_switch_13.py OR
PYTHONPATH=. ./bin/ryu-manager ryu/app/rest_qos
ryu/app/qos_simple_switch_13 ryu/app/rest_conf_switch
ryu/app/ofctl_rest
cd ryu/; python ./setup.py install
ryu-manager ryu.app.rest_qos ryu.app.qos_simple_switch_13
ryu.app.rest_conf_switch ryu.app.ofctl_rest
curl -X PUT -d '"tcp:127.0.0.1:6632"'
http://localhost:8080/v1.0/conf/switches/0000000000000001/ovsdb_add
r
curl -X PUT -d '"tcp:127.0.0.1:6632"'
http://localhost:8080/v1.0/conf/switches/0000000000000002/ovsdb_add
r
#==============
#DISPLAY QUEUES
#==============
curl -X GET http://localhost:8080/qos/rules/0000000000000001
curl -X GET http://localhost:8080/qos/rules/0000000000000002
#=========
#SET QUEUE
#=========
#Q1:
curl -X POST -d '{"port_name": "s1-eth1", "type": "linux-htb",
"max_rate": "2000000", "queues": [{"max_rate": "2000000"},
{"max_rate": "250000"}, {"max_rate": "62500"}, {"max_rate":
"510000"}, {"max_rate": "600000"}, {"max_rate": "100000"},
{"max_rate": "175000"}]}'
http://localhost:8080/qos/queue/0000000000000001
#Q2:
curl -X POST -d '{"port_name": "s1-eth1", "type": "linux-htb",
"max_rate": "2000000", "queues": [{"max_rate": "2000000"},
{"max_rate": "250000"}, {"max_rate": "62500"}, {"max_rate":
"680000"}, {"max_rate": "900000"}, {"max_rate": "100000"}]}'
http://localhost:8080/qos/queue/0000000000000001
#Q3:
curl -X POST -d '{"port_name": "s1-eth1", "type": "linux-htb",
"max_rate": "2000000", "queues": [{"max_rate": "2000000"},
{"max_rate": "500000"}, {"max_rate": "187500"}, {"max_rate":
"680000"}, {"max_rate": "600000"}]}'
http://localhost:8080/qos/queue/0000000000000001
#Q1: Service Proiver:
curl -X POST -d '{"port_name": "s2-eth1", "type": "linux-htb",
"max_rate": "20000000", "queues": [{"max_rate": "20000000"},
{"max_rate": "250000"}, {"max_rate": "500000"}, {"max_rate":
"1000000"}, {"max_rate": "2000000"}, {"max_rate": "3000000"}]}'
http://localhost:8080/qos/queue/0000000000000002
#===========
#APPLY QUEUE
#===========
#OUTBOUND QUEUES
#===============
curl -X POST -d '{"match": {"nw_src": "10.0.0.3"},
"actions":{"queue": "1"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.4"},
"actions":{"queue": "2"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.10"},
"actions":{"queue": "3"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.22"},
"actions":{"queue": "3"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.23"},
"actions":{"queue": "3"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.6"},
"actions":{"queue": "4"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.7"},
"actions":{"queue": "4"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.24"},
"actions":{"queue": "5"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.25"},
"actions":{"queue": "6"}}'
http://localhost:8080/qos/rules/0000000000000001
#=============
#IBOUND QUEUES
#=============
curl -X POST -d '{"match": {"nw_dst": "10.0.0.3"},
"actions":{"queue": "2"}}'
http://localhost:8080/qos/rules/0000000000000002
curl -X POST -d '{"match": {"nw_dst": "10.0.0.4"},
"actions":{"queue": "2"}}'
http://localhost:8080/qos/rules/0000000000000002
#=========================
#CLEAR ALL QUEUES
#=========================
curl -X POST -d '{"match": {"nw_src": "10.0.0.3"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.4"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.10"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.22"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.23"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.6"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.7"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.24"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_src": "10.0.0.25"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000001
curl -X POST -d '{"match": {"nw_dst": "10.0.0.3"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000002
curl -X POST -d '{"match": {"nw_dst": "10.0.0.4"},
"actions":{"queue": "0"}}'
http://localhost:8080/qos/rules/0000000000000002
#OR
#ovs-vsctl --all destroy qos
#ovs-vsctl --all destroy queue
