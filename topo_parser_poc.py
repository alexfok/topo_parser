"""
Author: Alex Fok 
"""

import os 
import re
import time
import redis
import json
from tqdm import tqdm

FILE_NAME = 'open_ai_0305'
#FILE_NAME = 'ibnetdiscover_r-dmz-ufm134'
SCRIPT_DIR = os.path.dirname(__file__)
PATH_TO_OUTPUT = os.path.join(SCRIPT_DIR, './' + FILE_NAME)
REDIS_SRV = '10.210.8.142'
r = redis.Redis(host = REDIS_SRV)

class InfinbandOutputParser():
    def __init__(self):
        self.links = []
        self.systems = []
        self.parser_output = {}
        self.parser_output[FILE_NAME] = []
        self.switches_count = 0
        self.hosts_count = 0
        self.hca_ports_count = 0
        self.links_count = 0
    
    def get_paragraphs_from_file(self):
        with open(PATH_TO_OUTPUT, "r") as input:
            paragraphs = input.read().split("\n\n")
            paragraphs = paragraphs[1:]
            
        return paragraphs
    
    def get_connection_details(self, lines, con_dict):
        for l in lines:
            key, value = l.partition("=")[::2]
            con_dict[key] = value
            
        keys_list = list(con_dict.keys())
        
        if  keys_list[-1] == "switchguid":
            switch_id = con_dict["switchguid"]
            sysimgguid = con_dict["sysimgguid"]
            self.switches_count +=1
#            print(f'self.switches_count: {self.switches_count}')
#            print(f"Switch:")
#            print(f"sysimgguid: {sysimgguid}")
#            print(f"identifier: {switch_id}")
        else:
            sysimgguid = con_dict["sysimgguid"]
            host_id = con_dict["caguid"]
            self.hosts_count +=1
#            print(f'self.hosts_count: {self.hosts_count}')
#            print(f"Host: ")
#            print(f"sysimgguid: {sysimgguid}")
#            print(f"port_id = {host_id}")
        # TODO
        # Add system to self.systems

        return con_dict
            
    def parse_switch_line(self, line, start):
        """
        Args:
            -line: connection line containing info on the device 
            -start: the index location in the line in which device id starts from
        Returns: 
            -switch: parsed switch switchguid 
            -port: connection port value
        """
        end = start + 18 # Id guid is a static 16 letter value  + 2 S-\H- header (16+2) 
        switch = line[start:end]
        port = re.sub('^.*\[(.*?)\][^\(]*$', '\g<1>', line) # Returns the port from square brackets
        return switch, port

    def parse_host_line(self, line, start):
        """
        Args:
            -line: connection line containing info on the device 
            -start: the index location in the line in which device id starts from
        Returns: 
            -host: parsed host identifier 
            -port: connection port value
        """
        end = start + 18 # Id guid is a static 16 letter value  + 2 S-\H- header (16+2) 
        host = line[start:end]
        port  = re.findall('\[(.*?)\]', line)[-1] # Returns the last value out of all string squared brackets 
        return host, port

    def get_connected_devices(self, lines, con_dict):
        connected_devices = []
        for line in lines:
            if "S-" in line:
                switch, port = self.parse_switch_line(line, line.find("S-"))
                connected_devices.append([switch, port])
#                print(f"    Switch device {switch} connected on port {port}")
                self.links_count +=1
#                print(f'self.links_count1: {self.links_count}')
            elif "H-" in line:
                host, port = self.parse_host_line(line, line.find("H-"))
                connected_devices.append([host, port])
#                print(f"    Host device {host} connected on port {port}")
                self.links_count +=1
                self.hca_ports_count +=1
#                print(f'self.links_count: {self.links_count}')
            link = {
                "source_guid": "0c42a103001b7ab6",
                "source_port": "1",
                "destination_guid": "0c42a103009d7af6",
                "destination_port": "19",
                "source_port_dname": "HCA-2/1",
                "destination_port_dname": "19",
                "width": "4x",
                "severity": "Info",
                "source_port_node_description": "luna-0395 mlx5_10",
                "destination_port_node_description": "SLG03-10:19",
                "name": "0c42a103001b7bf6_1:0c42a103009d7af6_19",
                "capabilities": []
            }
            self.links.append(link)
                
        # TODO
        # Add link to self.links
        con_dict["Connected Devices"] = connected_devices
        return con_dict

    def parse_infiniband_output(self):
        paragraphs = self.get_paragraphs_from_file()
        
#        print("Running connection analysis...")
        for paragraph in paragraphs:
#            print()
#            print("Connection:")
            con_dict = {}
            p_list = paragraph.splitlines()
            con_dict = self.get_connection_details(p_list[:4], con_dict)
            con_dict = self.get_connected_devices(p_list[5:], con_dict)
            self.parser_output[FILE_NAME].append(con_dict)
                               
if __name__ == '__main__':
    ib_topo_parser = InfinbandOutputParser()
    # Step 1 - parse topo file
    startTime = time.time()
    print(f"Start parsing file: {FILE_NAME}")
    ib_topo_parser.parse_infiniband_output()
    print(f"Finish parsing file: {FILE_NAME}")
    stopTime = time.time()
    print (f'Parse topo file took {stopTime - startTime:.3f} seconds')
#    print(f'len(parser_output[FILE_NAME]): {len(ib_topo_parser.parser_output[FILE_NAME])}')
    print(f'Topo: switches_count: {ib_topo_parser.switches_count}, hosts_count: {ib_topo_parser.hosts_count}, links_count: {ib_topo_parser.links_count}, hca_ports_count: {ib_topo_parser.hca_ports_count}')
    # Step 2 - Create links and systems dictionaries
    # Step 3 - Push links and systems dictionaries to Redis
    startTime = time.time()
    print(f"Push links bulk to Redis: {REDIS_SRV}")
    r.set('links', str(ib_topo_parser.links))
    stopTime = time.time()
    print (f'Push links bulk to Redis took {stopTime - startTime:.3f} seconds')

    startTime = time.time()
    print(f"Push topo to Redis link by link: {REDIS_SRV}")
    with r.pipeline() as pipe:
        i = 0
        for link in tqdm(ib_topo_parser.links):
            r.set('link:{i}', json.dumps(link))
            i += 1
    stopTime = time.time()
    print (f'Push Redis link by link to Redis took {stopTime - startTime:.3f} seconds')
