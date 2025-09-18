from datetime import datetime
import subprocess
import re
import time
import logging
from datetime import datetime
'''
Records the relevant pieces of the output of scamper.
'''
class DnsResponse:
    def __init__(self):
        self.status = ''
        self.opcode = ''
        self.flags = []
        self.qtype = ''
        self.rtt = -1
        self.dig_ts = datetime.now()
        self.ts = datetime.now()
        self.requested_domain = ''
        self.domain = ''
        self.ttl = -1
        self.r_type = ''
        self.ip = ''
        self.resolver = ''
        self.rd = True
        self.vp_name = ''
        self.scamper_ts = None
        self.pop_location = 'NO_LOCATION_SPECIFIED'

    def printSerialized(self):
        print('Domain: ' + self.domain)
        print('Status: ' + self.status)
        print('Opcode: ' + self.opcode)
        print('Query type: ' + self.qtype)
        print('RTT: ' + str(self.rtt) + 'ms')
        print('Dig timestamp: ' + str(self.dig_ts))
        print('TTL: ' + str(self.ttl))
        print('Response type: ' + self.r_type)
        print('IP: ' + self.ip)
        print('Timestamp: ' + str(self.ts))
        print('Resolver: ', self.resolver)
        print('VP Name: ' + str(self.vp_name))
        print('Location: ' + str(self.pop_location))

class ScamperParser(DnsResponse):
    def __init__(self, scamper_output, ts, loc='NO_LOCATION_SPECIFIED'):
        super().__init__()
        self.parse(scamper_output, ts, loc)

    def __getitem__(self, index):
        return getattr(self, index)

    def parse(self, scamper_output, ts, pop_location):
        self.pop_location = pop_location
        self.ts = ts
        self.requested_domain = scamper_output.qname
        self.rtt = scamper_output.rtt.total_seconds() * 1000 if scamper_output.rtt is not None else -1
        
        # Handle case where rx timestamp is None
        if scamper_output.rx is not None:
            aware_dt = datetime.fromisoformat(str(scamper_output.rx))
            self.scamper_ts = aware_dt.replace(tzinfo=None, microsecond=0)
        else:
            self.scamper_ts = self.ts  # Use passed timestamp as fallback
            
        self.resolver = str(scamper_output.dst)
        self.rcode = scamper_output.rcode
        self.rx = scamper_output.rx
        answer = scamper_output.an(0)
        self.ip = answer.addr if answer is not None else ''
        self.ttl = answer.ttl if answer is not None else -1
        self.r_type = answer.rtype if answer is not None else ''
        self.domain = answer.name if answer is not None else ''
        # Get VP name from the list's monitor field
        self.vp_name = scamper_output.list.monitor if hasattr(scamper_output, 'list') else ''
    
    def __repr__(self):
        fields = [
            f'Domain: {self.requested_domain}',
            f'RTT: {self.rtt}ms',
            f'Scamper timestamp: {self.rx}',
            f'TTL: {self.ttl}',
            f'Response type: {self.r_type}',
            f'IP: {self.ip}',
            f'Timestamp: {self.ts}',
            f'Resolver: {self.resolver}',
            f'VP Name: {self.vp_name}',
            f'Location: {self.pop_location}',
            f'Rcode: {self.rcode}' 
        ]
        return ', '.join(fields)

def ParseScamperOutput(scamper_output, loc='NO_LOCATION_SPECIFIED'):
    ts = datetime.utcnow()
    return ScamperParser(scamper_output, ts, loc)
