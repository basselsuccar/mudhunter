#!/usr/bin/env python3

import argparse
import datetime
import ipaddress
import random
import os
import statistics
from collections import defaultdict
from scamper import ScamperCtrl,ScamperFile
import re
from datetime import timedelta, datetime
import sys
import time
import csv
import logging
from process_file import process_scamper_file,load_resolver_vp_mappings, analyze_results

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,                         # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S',                 # Date format
    filename='app.log',                          # Optional: Log to a file
    filemode='a'                                 # Overwrite the log file each run ('w') or append ('a')
)

# Create a logger
logger = logging.getLogger(__name__)

def normalize_loc(loc):
    loc = loc.lower().strip()
    # Check if the location matches the pattern qABC1 (or qABC123, etc.)
    m = re.match(r'^q([a-z]{3})\d+$', loc)
    if m:
        return m.group(1)
    # Otherwise, remove any digits if they're not significant
    norm = re.sub(r'\d+', '', loc)
    return norm.strip()


def filter_similar_vps(data):
    """Keep VP with lowest average RTT per airport code"""
    filtered_data = {}
    filtered_vp_names = []
    # Group VPs by airport code
    airport_groups = defaultdict(list)
    for vp, recs in data.items():
        # Get the first valid location code for this VP
        for resolver in ('8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.220.220'):
            if resolver in recs and 'loc' in recs[resolver]:
                airport = normalize_loc(recs[resolver]['loc'])
                
                # Calculate average RTT across all resolvers
                rtts = []
                for r in ('8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.220.220'):
                    if r in recs and 'rtt' in recs[r] and recs[r]['rtt'] is not None:
                        try:
                            rtts.append(recs[r]['rtt'].total_seconds() * 1000)
                        except AttributeError:
                            continue
                avg_rtt = sum(rtts) / len(rtts) if rtts else float('inf')
                
                airport_groups[airport].append((vp, recs, avg_rtt))
                break
    
    # Keep VP with lowest average RTT for each airport
    for airport, vp_list in airport_groups.items():
        # Sort by average RTT and take the first (lowest) one
        vp_list.sort(key=lambda x: x[2])  # Sort by avg_rtt
        vp, recs, _ = vp_list[0]
        filtered_data[vp] = recs
        filtered_vp_names.append(vp)
    
    return filtered_data,filtered_vp_names

def filter_similar_vps_2(data):
    """Keep VP with the lowest RTT to the airport (from the resolver that reported the location)"""
    filtered_data = {}
    filtered_vp_names = []
    airport_groups = defaultdict(list)
    print(len(data))
    for vp, recs in data.items():
        # For each VP, find the first resolver with a location and use its RTT as the metric
        for resolver in ('8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.220.220'):
            if resolver in recs and 'loc' in recs[resolver]:
                airport = normalize_loc(recs[resolver]['loc'])
                # Use the RTT from this resolver as the metric
                try:
                    rtt = recs[resolver]['rtt'].total_seconds() * 1000
                except (AttributeError, KeyError):
                    rtt = float('inf')
                
                airport_groups[airport].append((vp, rtt))
    
    # For each airport, choose the VP with the lowest RTT (fastest reach)
    filtered_data = {}
    filtered_vp_names = []
    for airport, entries in airport_groups.items():
        best_vp, best_rtt = min(entries, key=lambda x: x[1])
        filtered_data[best_vp] = best_vp
        if best_vp not in filtered_vp_names:
            filtered_vp_names.append(best_vp)
        
    
    return filtered_data, filtered_vp_names
'''
def format_output(data):
    """Format output to show VPs grouped by resolver locations"""
    # Group by resolver first
    resolver_groups = {
        '8.8.8.8': {'name': 'Google', 'def filter_similar_vps(data):
    """Keep VP with lowest average RTT per airport code"""
    filtered_data = {}
    filtered_vp_names = []
    # Group VPs by airport code
    airport_groups = defaultdict(list)
    for vp, recs in data.items():
        # Get the first valid location code for this VP
        for resolver in ('8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.220.220'):
            if resolver in recs and 'loc' in recs[resolver]:
                airport = normalize_loc(recs[resolver]['loc'])
                print(airport)
                # Calculate average RTT across all resolvers
                rtts = []
                for r in ('8.8.8.8', '1.1.1.1', '9.9.9.9', '208.67.220.220'):
                    if r in recs and 'rtt' in recs[r] and recs[r]['rtt'] is not None:
                        try:
                            rtts.append(recs[r]['rtt'].total_seconds() * 1000)
                        except AttributeError:
                            continue
                avg_rtt = sum(rtts) / len(rtts) if rtts else float('inf')

                airport_groups[airport].append((vp, recs, avg_rtt))
                break

    # Keep VP with lowest average RTT for each airport
    for airport, vp_list in airport_groups.items():
        # Sort by average RTT and take the first (lowest) one
        vp_list.sort(key=lambda x: x[2])  # Sort by avg_rtt
        vp, recs, _ = vp_list[0]
        filtered_data[vp] = recs
        filtered_vp_names.append(vp)

    return filtered_data,filtered_vp_namesdata': {}},
        '1.1.1.1': {'name': 'Cloudflare', 'data': {}},
        '9.9.9.9': {'name': 'Quad9', 'data': {}},
        '208.67.220.220': {'name': 'OpenDNS', 'data': {}}
    }
    
    # Group VPs by resolver location
    for vp, recs in sorted(data.items()):
        for resolver in resolver_groups:
            if resolver in recs and 'loc' in recs[resolver]:
                loc = recs[resolver]['loc']
                rtt = recs[resolver]['rtt'].total_seconds() * 1000
                if loc not in resolver_groups[resolver]['data']:
                    resolver_groups[resolver]['data'][loc] = []
                resolver_groups[resolver]['data'][loc].append((vp, rtt))
    
    # Print results grouped by resolver
    for resolver, info in resolver_groups.items():
        print(f"\n=== {info['name']} ===")
        print(f"{'VP':15} {'Location':>8} {'RTT(ms)':>8}")
        print("-" * 35)
        
        for loc in sorted(info['data'].keys()):
            # Sort VPs by RTT for each location
            vps = sorted(info['data'][loc], key=lambda x: x[1])
            for i, (vp, rtt) in enumerate(vps):
                # Mark potential duplicates (similar RTTs to same location)
                marker = " *" if i > 0 else "  "
                print(f"{vp:15} {loc:>8} {rtt:8.1f}{marker}")
        print()
    '''
def format_output_2(data, filtered_vp_names,output_folder):
    """
    Format output to show filtered VPs grouped by resolver locations and save a CSV file
    for each resolver with the VPs that are in contact with it.

    Each CSV file will have the following columns:
        VP, Location, RTT(ms), Marker
    The marker "*" is added for potential duplicate entries (multiple VPs for the same location).

    Args:
        data (dict): The original data dictionary mapping VP names to their resolver records.
                     Each resolver record should include a 'loc' field and an 'rtt' field (a timedelta).
        filtered_vp_names (list): A list of VP names that were selected (e.g., by filter_similar_vps_2).

    Returns:
        None
    """
    # Define the resolver groups with a friendly name and an empty dictionary to hold VP data.
    resolver_groups = {
        '8.8.8.8': {'name': 'Google', 'data': {}},
        '1.1.1.1': {'name': 'Cloudflare', 'data': {}},
        '9.9.9.9': {'name': 'Quad9', 'data': {}},
        '208.67.220.220': {'name': 'OpenDNS', 'data': {}}
    }

    # Group only the filtered VPs by resolver location.
    for vp in sorted(filtered_vp_names):
        # Use the original data record for this VP.
        if vp in data:
            recs = data[vp]
            for resolver in resolver_groups:
                if resolver in recs and 'loc' in recs[resolver]:
                    loc = normalize_loc(recs[resolver]['loc'])
                    # Convert RTT to milliseconds.
                    rtt = recs[resolver]['rtt'].total_seconds() * 1000
                    # Group the (vp, rtt) pair by location.
                    resolver_groups[resolver]['data'].setdefault(loc, []).append((vp, rtt))

    # For each resolver, sort the VPs by RTT and write the output to a CSV file.
    for resolver, info in resolver_groups.items():
        today_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"{info['name']}_output_{today_date}.csv"
        file_path = os.path.join(output_folder, filename)
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header.
            writer.writerow(['VP', 'Location', 'RTT(ms)', 'Marker'])
            # Process each location group.
            for loc in sorted(info['data'].keys()):
                # Sort VPs by RTT within this location.
                vps = sorted(info['data'][loc], key=lambda x: x[1])
                for i, (vp, rtt) in enumerate(vps):
                    marker = "*" if i > 0 else ""
                    writer.writerow([vp, loc, f"{rtt:.1f}", marker])
        logger.info(f"Saved results for {info['name']} to {filename}")

def _main():
    mux = sys.argv[1]
    domains = sys.argv[2]
    outfile = sys.argv[3]
    servers = sys.argv[4:]
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    output_folder = f"{domains.split('.')[0]}_results_{today_date}"
    outfile = os.path.join(output_folder, outfile)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)


    ctrl = ScamperCtrl(mux=sys.argv[1])
    ctrl.add_vps(ctrl.vps())
    #ctrl = ScamperCtrl(unix='/tmp/scamper')

    # pick an ark VP at random to issue the query that gets the mapping
    # of google recursive IP to location
    goog_nets = {}
    obj = ctrl.do_dns('locations.publicdns.goog',
                    inst=random.choice(ctrl.instances()),
                    qtype='txt', tcp=True, sync=True)
    if obj is None or len(obj.ans_txts()) == 0:
        print("could not get google mapping")
        return
    for txts in obj.ans_txts():
        for txt in txts:
            net, loc = txt.split()
            goog_nets[ipaddress.ip_network(net)] = loc

    # issue the magic queries to get the instance that answers the query
    for inst in ctrl.instances():
        ctrl.do_dns('o-o.myaddr.l.google.com', server='8.8.8.8', qtype='txt',
                    attempts=2, wait_timeout=2, inst=inst)
        ctrl.do_dns('id.server', server='1.1.1.1', qclass='ch', qtype='txt',
                    attempts=2, wait_timeout=2, inst=inst)
        ctrl.do_dns('id.server', server='9.9.9.9', qclass='ch', qtype='txt',
                    attempts=2, wait_timeout=2, inst=inst)
        ctrl.do_dns('debug.opendns.com', server='208.67.220.220', qtype='txt',
                    attempts=2, wait_timeout=2, inst=inst)

    # collect the data
    data = {}
    for obj in ctrl.responses(timeout=timedelta(seconds=10)):
        vp = obj.inst.shortname
        if vp not in data:
            data[vp] = {}
        dst = str(obj.dst)
        if dst in data[vp]:
            continue
        data[vp][dst] = {}
        data[vp][dst]['rtt'] = obj.rtt

        for txts in obj.ans_txts():
            for txt in txts:
                if dst == '8.8.8.8':
                    # google reports an IPv4 address that represents
                    # the site that answers the query.  we then map
                    # that address to a location using the mapping
                    # returned by the locations TCP query.
                    try:

                        addr = ipaddress.ip_address(txt)
                    except ValueError:
                        continue
                    for net, loc in goog_nets.items():
                        if addr in net:
                            data[vp][dst]['loc'] = loc
                            break
                elif dst == '1.1.1.1':
                    # Cloudflare replies with a single TXT record
                    # containing an airport code
                    data[vp][dst]['loc'] = txt
                elif dst == '9.9.9.9':
                    # Quad9 reports a hostname with an embedded
                    # airport code.
                    match = re.search("\\.(.+?)\\.rrdns\\.pch\\.net", txt)
                    if match:
                        data[vp][dst]['loc'] = match.group(1)
                elif dst == '208.67.220.220':
                    # opendns reports multiple TXT records; we want the one
                    # that looks like "server r2005.syd"
                    match = re.search("^server .+\\.(.+?)$", txt)
                    if match:
                        data[vp][dst]['loc'] = match.group(1)

    # Filter similar VPs
    filtered_data, filtered_vp_names = filter_similar_vps_2(data)
    # Format and display results
    format_output_2(data,filtered_vp_names,output_folder)
    
    
    

    ctrl = ScamperCtrl(mux=mux,outfile=ScamperFile(outfile, mode='w'))
    vps = ctrl.vps()
    vps = [vp for vp in ctrl.vps() if vp.name.split('.')[0] in filtered_vp_names]
    ctrl.add_vps(vps)
    
    logger.info(f"processing {domains}")

    with open(domains, 'r') as file:
        for line in file:
            domain = line.strip()
            logger.info(domain)
            for i in range(50):
                try:
                    start = datetime.now()

                    for s in servers:
                        ctrl.do_dns(domain, rd=False, server=s, inst=ctrl.instances())

                    # responses will 
                    if i == 49 :
                        until = start + timedelta(seconds=10)
                    else:
                        until = start + timedelta(seconds=1)
                    for obj in ctrl.responses(until=until):
                        continue

                    finish = datetime.now()

                    if finish < until:
                        time.sleep((until - finish).total_seconds())
                except Exception as e:
                    logging.error("Error in iteration %d: %s", i, str(e), exc_info=True)

    search_results = process_scamper_file(outfile)
    resolver_vp_mappings = load_resolver_vp_mappings(output_folder)
    analyze_results(search_results, resolver_vp_mappings,output_folder)

if __name__ == "__main__":
    _main()
