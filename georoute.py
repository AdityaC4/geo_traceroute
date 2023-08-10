#!/usr/bin/env python3

import subprocess
import platform
import itertools
import sys
import time
import re
import requests
import argparse
from tabulate import tabulate
import json
import folium
import webbrowser



def run_traceroute(host):
    system = platform.system()
    
    if system == "Windows":
        command = ["tracert", host]
    else:
        command = ["traceroute", "-I", host]

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    
    spinner = itertools.cycle(['-', '/', '|', '\\'])  # Loading spinner characters
    
    while process.poll() is None:
        sys.stdout.write('\rRunning traceroute... ' + next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
    
    sys.stdout.write('\rRunning traceroute... Done!\n')
    
    return process.stdout.read()


def filter_ips(trace):
    pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    ip_addresses = re.findall(pattern, trace)[2:]
    return ip_addresses


def fetch_geo_info(ip_addresses):
    response = requests.post("http://ip-api.com/batch", json=ip_addresses).json()
    return response


def print_verbose_output(response):
    table = []
    headers = []
    for item in response:
        row = []
        if item['status'] == 'success':
            for key, value in item.items():
                if key not in ['countryCode', 'region']:
                    row.append(value)
                    if key not in headers:
                        headers.append(key)
        else:
            row = [item['status'], item['message']] + ['N/A'] * (len(headers) - 2)
        table.append(row)
    
    print(tabulate(table, headers=headers, tablefmt='outline'))


def print_summary_output(response):
    table = []
    for item in response:
        if item['status'] == 'success':
            table.append([item['status'], item['query'], item['country'], item['city']])
        else:
            table.append([item['status'], item['query'], item['message'], 'N/A'])
    print(tabulate(table, headers=['Status', 'IP Address', 'Country', 'City'], tablefmt='outline'))

def print_json_output(response):
    return json.dumps(response, indent=4)

def filter_lat_lon(response):
    return [(item["lat"], item["lon"]) for item in response if "lat" in item and "lon" in item]

def create_map(response):
    coordinates = filter_lat_lon(response)

    # Create a map centered around the first coordinate
    map_center = coordinates[0]
    map = folium.Map(location=map_center, zoom_start=4)

    # Add markers for each coordinate
    for i, coord in enumerate(coordinates):
        folium.Marker(location=coord, popup=f'Point {i+1}').add_to(map)

    # Add connections between the coordinates
    for i in range(len(coordinates) - 1):
        coord1 = coordinates[i]
        coord2 = coordinates[i + 1]
        folium.PolyLine([coord1, coord2], color="blue").add_to(map)

    # Save the map as an HTML file in the current directory
    map_file = "map.html"
    map.save(map_file)

    # Open the generated file with the default web browser
    browser = webbrowser.get()
    browser.open(map_file)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Hostname or IP address to trace')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose traceroute output mode')
    parser.add_argument('-j', '--jsonOutput', action='store_true', help='Enable JSON formatted output mode')
    parser.add_argument('-s', '--summary', action='store_true', help='Enable traceroute summary output mode')
    parser.add_argument('-m', '--mapGen', action='store_true', help='generate map for the traceroute')
    args = parser.parse_args()

    if args.host:
        host = args.host
    else:
        parser.print_help()
        sys.exit(1)

    trace = run_traceroute(host)
    ip_addresses = filter_ips(trace)
    response = fetch_geo_info(ip_addresses)

    if args.summary:
        print("Trace Summary")
        print_summary_output(response)

    if args.verbose:
        print("Verbose")
        print_verbose_output(response)

    if args.jsonOutput:
        print("JSON output")
        print(print_json_output(response))

    if args.mapGen:
        print("Map was generated in the current folder, and should open automatically in the default browser")
        create_map(response)
    


if __name__ == "__main__":
    main()
