import json
import networkx as nx
import grpc
import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.error_utils import printGrpcError
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

class SwitchTopo:
    def __init__(self, topo_file):
        with open(topo_file, 'r') as f:
            topo = json.load(f)
        self.hosts = topo['hosts']
        self.switches = topo['switches']
        self.links = self.parse_links(topo['links'])
    
    def get_networkx_topo(self):
        topo = nx.Graph()
        edge_num = 0
        for sw, params in self.switches.iteritems():
            topo.add_node(sw)
        
        #assumes host always comes first for host<--->switch links
        for link in self.links:
            if not link['node1'][0] == 'h':
                edge_name = 'edge_' + str(edge_num)
                sw1_name, sw1_port = self.parse_switch_node(link['node1'])
                sw2_name, sw2_port = self.parse_switch_node(link['node2'])

                topo.add_edge(sw1_name, sw2_name, name=edge_name)
                topo.nodes[sw1_name][edge_name] = sw1_port
                topo.nodes[sw2_name][edge_name] = sw2_port

                edge_num += 1
        
        return topo



    def parse_switch_node(self, node):
        assert(len(node.split('-')) == 2)
        sw_name, sw_port = node.split('-')
        try:
            sw_port = int(sw_port[1])
        except:
            raise Exception('Invalid switch node in topology file: {}'.format(node))
        return sw_name, sw_port

    def format_latency(self, l):
        """ Helper method for parsing link latencies from the topology json. """
        if isinstance(l, (str, unicode)):
            return l
        else:
            return str(l) + "ms"

    def parse_links(self, unparsed_links):
        """ Given a list of links descriptions of the form [node1, node2, latency, bandwidth]
            with the latency and bandwidth being optional, parses these descriptions
            into dictionaries and store them as self.links
        """
        links = []
        for link in unparsed_links:
            # make sure each link's endpoints are ordered alphabetically
            s, t, = link[0], link[1]
            if s > t:
                s,t = t,s

            link_dict = {'node1':s,
                        'node2':t,
                        'latency':'0ms',
                        'bandwidth':None
                        }
            if len(link) > 2:
                link_dict['latency'] = self.format_latency(link[2])
            if len(link) > 3:
                link_dict['bandwidth'] = link[3]

            if link_dict['node1'][0] == 'h':
                assert link_dict['node2'][0] == 's', 'Hosts should be connected to switches, not ' + str(link_dict['node2'])
            links.append(link_dict)
        return links

def dfs_backup(topo, s, d):
    stack = [[("",s)]]
    visited = [s]
    while stack:
        cur_state = stack.pop()
        edge, node = cur_state[-1]
        adj_nodes = topo.adj[node]
        for cur_node in adj_nodes:
            if cur_node in visited:
                continue
            if cur_node == d:
                if node != s:
                    cur_state.append((topo[node][cur_node]['name'], cur_node))
                    return cur_state
                else:
                    continue    
            stack.append(cur_state)
            new_state = cur_state[:]
            new_state.append((topo[node][cur_node]['name'], cur_node))
            stack.append(new_state)
            break
    return [("", None)]

def backup_path_to_bmv2_config(topo, path):
    bmv2_config = []
    edge,src_node = path[0]
    for i in range(1,len(path)):
        edge, dst_node = path[i]
        bmv2_config.append((src_node, edge, topo.nodes[src_node][edge]))
        src_node = dst_node
    return bmv2_config

def calculate_backup_path(topo):
    for link in topo.edges:
        backup_path = dfs_backup(topo, link[0], link[1])
        print(backup_path)
        backup_path_config = backup_path_to_bmv2_config(topo, backup_path)
        print(backup_path_config)
        backup_path = dfs_backup(topo, link[1], link[0])
        print(backup_path)
        backup_path_config = backup_path_to_bmv2_config(topo, backup_path)
        print(backup_path_config)


def write_failover_config(p4info_helper, sw):
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.edge_to_port",
        match_fields={
            "meta.out_edge": (2)
        },
        action_name="MyIngress.recovery_forward",
        action_params={
            "port": 3,
        }
    )
    sw.WriteTableEntry(table_entry)
    print "Installed edge to port rule on %s" % sw.name

def setup_connection(p4info_file_path, bmv2_file_path):
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    try:
        # s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
        #     name='s1',
        #     address='127.0.0.1:50051',
        #     device_id=0,
        #     # proto_dump_file='logs/s1-p4runtime-requests.txt'
        #     )
        s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
            # proto_dump_file='logs/s3-p4runtime-requests.txt'
            )

        # Send master arbitration update message to establish this controller as
        # master (required by P4Runtime before performing any other write operation)
        # s1.MasterArbitrationUpdate()
        s3.MasterArbitrationUpdate()

        # Install the P4 program on the switches
        # s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
        #                                bmv2_json_file_path=bmv2_file_path)
        # print "Installed P4 Program using SetForwardingPipelineConfig on s1"
        # s2.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
        #                                bmv2_json_file_path=bmv2_file_path)
        # print "Installed P4 Program using SetForwardingPipelineConfig on s3"

        write_failover_config(p4info_helper, s3)

    except KeyboardInterrupt:
        print " Shutting down."
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

if __name__ == '__main__':
    # topo_file = "topo/topology.json"
    # topo = SwitchTopo(topo_file)
    # switch_only_topo = topo.get_networkx_topo()
    # calculate_backup_path(switch_only_topo)
    setup_connection('./build/simple_recovery.p4.p4info.txt', './build/simple_recovery.json')





    #     {
    #   "table": "MyIngress.edge_to_port",
    #   "match": {
    #     "meta.out_edge": [2]
    #   },
    #   "action_name": "MyIngress.recovery_forward",
    #   "action_params": {
    #     "port": 3
    #   }
    # }