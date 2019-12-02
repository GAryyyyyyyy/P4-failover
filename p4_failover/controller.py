import json
import networkx as nx

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


if __name__ == '__main__':
    topo_file = "topo/topology.json"
    topo = SwitchTopo(topo_file)
    switch_only_topo = topo.get_networkx_topo()