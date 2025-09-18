from scamper import ScamperFile, ScamperHost
from core.scamper_dns_lib_v2 import ParseScamperOutput
from collections import defaultdict
from core.compare_results import estimateFilledCaches
import csv
from datetime import datetime
import sys
import os


def load_resolver_vp_mappings(out_dir):
    """
    Load VP-to-airport mappings for each resolver from their respective CSV files.
    Each CSV file is expected to have columns: "VP", "Location", "RTT(ms)", "Marker".
    The resolver-to-file mapping is hardcoded based on IP.
    Returns a dictionary mapping resolver IP to a dictionary mapping VP name to airport.
    """
    today = datetime.now().strftime('%Y-%m-%d')

    resolver_files = {
        '8.8.8.8': f'Google_output_{today}.csv',
        '1.1.1.1': f'Cloudflare_output_{today}.csv',
        '9.9.9.9': f'Quad9_output_{today}.csv',
        '208.67.220.220': f'OpenDNS_output_{today}.csv'
    }
    resolver_mappings = {}
    for resolver, filename in resolver_files.items():
        mapping = {}
        file_path = os.path.join(out_dir, filename)
        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Expecting columns: VP, Location, RTT(ms), Marker
                    vp = row.get('VP')
                    location = row.get('Location')
                    if vp and location:
                        mapping[vp.split('.')[0]] = location
        except FileNotFoundError:
            print(f"Warning: Mapping file {filename} for resolver {resolver} not found.")
        resolver_mappings[resolver] = mapping
    print(resolver_mappings)
    return resolver_mappings

def process_scamper_file(filename):
    """
    Process the scamper file and parse each DNS response.
    """
    file = ScamperFile(filename, filter_types=[ScamperHost])
    search_results = []
    for host in file:
        search_result = ParseScamperOutput(host)
        search_results.append(search_result)
    return search_results

def analyze_results(search_results, resolver_vp_mappings,output_dir):
    """
    Process search results, group them by domain and VP, and then
    for each resolver, write the output to a separate CSV file.
    
    For the pop_location field, this version uses the resolver-specific CSV mapping:
    it opens the corresponding CSV file for the resolver (preloaded in resolver_vp_mappings)
    and uses the "Location" value for the VP.
    """
    # Predefined resolvers with friendly names.
    resolvers = {
        '8.8.8.8': {'name': 'Google'},
        '1.1.1.1': {'name': 'Cloudflare'},
        '9.9.9.9': {'name': 'Quad9'},
        '208.67.220.220': {'name': 'OpenDNS'}
    }

    # Open one CSV file per resolver for output.
    files = {}
    writers = {}
    fieldnames = ['timestamp', 'domain', 'vantage_point', 'resolver', 'pop_location',
                  'cache_count', 'last_probe', 'ttls', 'rtt']
    for ip, info in resolvers.items():
        today_date = datetime.now().strftime('%Y-%m-%d')
        out_filename = f"{info['name']}_analysis_{today_date}.csv"
        out_filepath = os.path.join(output_dir, out_filename)
        f = open(out_filepath, 'w', newline='')
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        files[ip] = f
        writers[ip] = writer

    # Group results by domain and VP.
    domain_results = defaultdict(lambda: defaultdict(list))
    for r in search_results:
        domain = r.requested_domain.strip(".").strip("\r\n")
        domain_results[domain][r.vp_name].append(r)

    # Process each domain and each VP.
    for domain, vp_results in domain_results.items():
        for vp_name, vp_search_results in vp_results.items():
            # For the current domain and VP, group results by resolver.
            domain_to_data = defaultdict(lambda: defaultdict(list))
            # Initialize keys for each encountered resolver.
            for r in vp_search_results:
                domain_to_data[r.resolver]["scamper_ts"]
                domain_to_data[r.resolver]["ttl"]
                domain_to_data[r.resolver]["pop_location"]
                domain_to_data[r.resolver]["rtt"]

            # Collect data for each resolver.
            for r in vp_search_results:
                resolver = r.resolver
                domain_to_data[resolver]["scamper_ts"].append(r.scamper_ts)
                domain_to_data[resolver]["ttl"].append(r.ttl)
                # Lookup the airport using the resolver-specific mapping.
                vp_mapping = resolver_vp_mappings.get(resolver, {})
                # If VP not found in the mapping, fall back to the VP name.
                airport = vp_mapping.get(r.vp_name.split('.')[0], r.vp_name)
                domain_to_data[resolver]["pop_location"].append(airport)
                domain_to_data[resolver]["rtt"].append(r.rtt)

            # Write a row for each resolver.
            for resolver, data in domain_to_data.items():
                # Skip if this resolver isn't in our predefined list.
                if resolver not in writers:
                    continue

                # Prepare the row.
                if len(data["ttl"]) == 0:
                    row = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'domain': domain,
                        'vantage_point': vp_name,
                        'resolver': resolver,
                        'pop_location': '',
                        'cache_count': 'ERROR_NO_DATA',
                        'last_probe': '',
                        'ttls': '',
                        'rtt': ''
                    }
                else:
                    count = estimateFilledCaches(data, resolver)
                    last_probe = max(data["scamper_ts"])
                    # Join unique airport values if there are multiple.
                    pop_airports = ','.join(sorted(set(data["pop_location"])))
                    row = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'domain': domain,
                        'vantage_point': vp_name,
                        'resolver': resolver,
                        'pop_location': pop_airports,
                        'cache_count': count,
                        'last_probe': last_probe,
                        'ttls': ','.join(map(str, data["ttl"])),
                        'rtt': ','.join(map(str, data["rtt"]))
                    }
                writers[resolver].writerow(row)

    # Close all CSV files.
    for f in files.values():
        f.close()

    print("Analysis CSV files created for each resolver:")
    for ip, info in resolvers.items():
        print(f"{info['name']}_analysis.csv")

if __name__ == "__main__":
    input_file = sys.argv[1]   # Scamper file name
    search_results = process_scamper_file(input_file)
    #resolver_vp_mappings = load_resolver_vp_mappings('banking_phishing_domains_results_2025-04-10')
    #analyze_results(search_results, resolver_vp_mappings,'banking_phishing_domains_results_2025-04-10')
