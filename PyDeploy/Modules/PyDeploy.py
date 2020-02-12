import xml.etree.ElementTree as ET
from Modules import SystemElements


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


# ********** PARSER **********
class System:
    def __init__(self):
        self.name = ''

        self.constraints = list()
        self.objectives = list()

        self.max_cost = 10000
        self.max_energy = 10000
        self.max_num_devices = 10000
        self.communication_delay = 0

        self.function_blocks = list()
        self.function_blocks_redundancy = list() # Same list as function_blocks, but contains multiple copies of same fb if fb.num_of_copies > 1
        self.connections = list()
        self.coupling = list()
        self.devices = list()
        self.segments = list()
        self.links = list()
        self.hw_skills = list()
        self.fb_types = list()
        self.event_paths = list()
        self.events = list()
    
    def is_segment_available(self, device: SystemElements.Device, segment):
        for link in self.links:
            if link.device == device and link.segment == segment:
                return True
        return False

    def parse_xml(self, filename):
        """Parse XML file
        
        Parse the XML file
        and fill list variables of this object
        """

        # Read XML file
        SystemRoot = ET.parse(filename).getroot()

        if SystemRoot.attrib['Name']:
            self.name = SystemRoot.attrib['Name']

        # ***** MAIN LOOP *****
        # Iterate through the whole XML file and find applications, devices, segments and links
        for SystemChild in SystemRoot:

            # Global constraints for the whole system
            if SystemChild.tag == 'Attribute':
                if SystemChild.attrib['Name'] == 'Constraints':
                    self.constraints = SystemChild.attrib['Value'].split(',')
                elif SystemChild.attrib['Name'] == 'Objectives':
                    self.objectives = SystemChild.attrib['Value'].split(',')
                elif SystemChild.attrib['Name'] == 'Maximum cost':
                    self.max_cost = int(SystemChild.attrib['Value'])
                elif SystemChild.attrib['Name'] == 'Maximum energy':
                    self.max_energy = int(SystemChild.attrib['Value'])
                elif SystemChild.attrib['Name'] == 'Maximum number of devices':
                    self.max_num_devices = int(SystemChild.attrib['Value'])
                elif SystemChild.attrib['Name'] == 'Communication delay':
                    self.communication_delay = int(SystemChild.attrib['Value'])

            # Application
            elif SystemChild.tag == 'Application':
                for ApplicationChild in SystemChild:
                    # SubAppNetwork: Iterate through all function blocks, connections etc.
                    if ApplicationChild.tag == 'SubAppNetwork':
                        for SubAppNetworkChild in ApplicationChild:
                            # Function block
                            if SubAppNetworkChild.tag == 'FB' or SubAppNetworkChild.tag == 'SubApp':
                                if SubAppNetworkChild.attrib['Type']:
                                    tp = SubAppNetworkChild.attrib['Type']
                                else:
                                    tp = ''
                                
                                function_block = SystemElements.Function_Block(SystemChild.attrib['Name'] + '.' + SubAppNetworkChild.attrib['Name'], tp)
                                
                                # Iterate through all resources of the device
                                for FBChild in SubAppNetworkChild:
                                    if FBChild.tag == 'Attribute':
                                        if FBChild.attrib['Name'] == 'Memory':
                                            function_block.memory = int(FBChild.attrib['Value'])
                                        elif FBChild.attrib['Name'] == 'WCET':
                                            function_block.wcet = int(FBChild.attrib['Value'])
                                        elif FBChild.attrib['Name'] == 'SIL':
                                            function_block.SIL = int(FBChild.attrib['Value'])
                                        elif FBChild.attrib['Name'] == 'Number of copies':
                                            function_block.num_of_copies = int(FBChild.attrib['Value'])
                                        elif FBChild.attrib['Name'] == 'Sensitivity':
                                            function_block.sensitive = str2bool(FBChild.attrib['Value'])
                                        elif FBChild.attrib['Name'] == 'Skills':
                                            function_block.hardware = FBChild.attrib['Value'].split(",")
                                self.function_blocks.append(function_block)
                            # Connections (Event/Data/Adapter)
                            elif SubAppNetworkChild.tag == 'EventConnections' or SubAppNetworkChild.tag == 'DataConnections' or SubAppNetworkChild.tag == 'AdapterConnections':
                                for connection in SubAppNetworkChild:
                                    conn = SystemElements.Connection()
                                    conn.source = SystemChild.attrib['Name'] + '.' + connection.attrib['Source'].split('.')[0]
                                    conn.destination = SystemChild.attrib['Name'] + '.' + connection.attrib['Destination'].split('.')[0]
                                    self.connections.append(conn)
                            # Event Paths
                            elif SubAppNetworkChild.tag == 'EventPaths':
                                for path in SubAppNetworkChild:
                                    p = SystemElements.EventPath()
                                    p.application = SystemChild.attrib['Name']
                                    p.deadline = int(path.attrib['Deadline'])
                                    for event in path.attrib['Events'].split(','):
                                        event = event.split('.')
                                        e = SystemElements.Event(event[1])
                                        e.function_block = event[0]
                                        e.application = SystemChild.attrib['Name']
                                        p.events.append(e)
                                    for pair in path:
                                        pr = SystemElements.EventPair()
                                        pr.source = next(e for e in p.events if (e.function_block + '.' + e.name) == pair.attrib['Source'])
                                        pr.destination = next(e for e in p.events if (e.function_block + '.' + e.name) == pair.attrib['Destination'])
                                        p.pairs.append(pr)
                                    self.events += p.events
                                    self.event_paths.append(p)

            # Device
            elif SystemChild.tag == 'Device':
                device = SystemElements.Device(SystemChild.attrib['Name'])

                # Iterate through all resources of the device
                for DeviceChild in SystemChild:
                    if DeviceChild.tag == 'Attribute':
                        if DeviceChild.attrib['Name'] == 'Cost':
                            device.cost = int(DeviceChild.attrib['Value'])
                        elif DeviceChild.attrib['Name'] == 'Energy':
                            device.energy = int(DeviceChild.attrib['Value'])
                        elif DeviceChild.attrib['Name'] == 'Skills':
                            device.skills = DeviceChild.attrib['Value'].split(',')
                        elif DeviceChild.attrib['Name'] == 'RTE Library':
                            device.RTE_lib = DeviceChild.attrib['Value'].split(',')
                        elif DeviceChild.attrib['Name'] == 'Memory':
                            device.memory = int(DeviceChild.attrib['Value'])
                        elif DeviceChild.attrib['Name'] == 'SIL':
                            device.SIL = int(DeviceChild.attrib['Value'])
                        elif DeviceChild.attrib['Name'] == 'Open':
                            device.open = str2bool(DeviceChild.attrib['Value'])
                        elif DeviceChild.attrib['Name'] == 'Maximum number of FB':
                            device.max_num_of_function_blocks = int(DeviceChild.attrib['Value'])

                    elif DeviceChild.tag == 'Resource':
                        res = DeviceChild.attrib['Name']
                        device.resources.append(res)
                
                self.devices.append(device)
            
            # Segment / Network
            elif SystemChild.tag == 'Segment':
                segment = SystemChild.attrib['Name']
                self.segments.append(segment)

            # Link from a device to a segment
            elif SystemChild.tag == 'Link':
                link = SystemElements.Link()
                link.device = SystemChild.attrib['CommResource']
                link.segment = SystemChild.attrib['SegmentName']
                self.links.append(link)

        # calculate coupling intensity
        self.coupling = self.connections[:]
        idx = 0
        while idx < len(self.coupling):
            self.coupling[idx].intensity += 1
            idx_nxt = idx + 1
            while idx_nxt < len(self.coupling):
                if((self.coupling[idx_nxt].destination == self.coupling[idx].destination or self.coupling[idx_nxt].source == self.coupling[idx].destination) and (self.coupling[idx_nxt].destination == self.coupling[idx].source or self.coupling[idx_nxt].source == self.coupling[idx].source)):
                    self.coupling[idx].intensity += 1
                    del self.coupling[idx_nxt]
                else:
                    idx_nxt += 1
            idx += 1

        # Connections between function blocks
        for connection in self.connections:
            connection.source = next(fb for fb in self.function_blocks if fb.name == connection.source)
            connection.destination = next(fb for fb in self.function_blocks if fb.name == connection.destination)
            connection.source.coupling.append(connection.destination)
            connection.destination.coupling.append(connection.source)

        # Link between device and segment
        for link in self.links:
            link.device = next(device for device in self.devices if device.name == link.device)
            link.device.network.add(link.segment)
        
        # Update function block reference of events
        for event in self.events:
            event.function_block = next(fb for fb in self.function_blocks if fb.name == (event.application + '.' + event.function_block))

        # ***** UPDATE HW SKILLS SET *****
        # This set collects all hw skills (unifies all device skills and all fb skills)
        hw_skills_set = set()

        for device in self.devices:
            device.skills = [skill for skill in device.skills if skill != ""] # Remove empty skills ("")
            hw_skills_set.update(device.skills)
        for fb in self.function_blocks:
            fb.hardware = [skill for skill in fb.hardware if skill != ""] # Remove empty skills ("")
            hw_skills_set.update(fb.hardware)

        self.hw_skills = list(hw_skills_set)
        
        # ***** UPDATE FB TYPES SET *****
        # This set collects all fb types (unifies all device RTE libs and all fb types)
        fb_types_set = set()
        
        for device in self.devices:
            device.RTE_lib = [fb_type for fb_type in device.RTE_lib if fb_type != ""] # Remove empty types ("")
            fb_types_set.update(device.RTE_lib)
        for fb in self.function_blocks:
            if fb.type != '':
                fb_types_set.add(fb.type)
        
        self.fb_types = list(fb_types_set)

        # ***** "Flatten" function_blocks list (to simplify Redundancy constraint) *****
        for fb in self.function_blocks:
            for i in range(fb.num_of_copies):
                self.function_blocks_redundancy.append(fb)
