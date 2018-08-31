#!/usr/bin/env python
import json, os, glob, re, networkx as nx, matplotlib.pyplot as plt
from networkx.readwrite import json_graph

DEBUG = False

def getFilesList():
	if os.getenv("NETWORK_VIS"):
		files_list = glob.glob(os.getenv("NETWORKVIS") + "*.txt")
	elif os.getenv("HOME"):
		files_list = glob.glob(os.getenv("HOME") + "/.network_vis/*.txt")

	if len(files_list):
		return files_list
	else:
		print("Error: cannot find any files! Did you export NETWORKVIS?")
		os.sys.exit(1)

def convertLine(connection):
	# Convert the connection into a dictionary for easier reference to the elements of each connection line
	# TODO This is pretty hackish and probably could be done in a better way.
	connection_keys = ["protocol",  "local_ip",  "local_port",  "remote_ip",  "remote_port",  "state",  "PID"]
	connection = (re.sub("^ ", "", re.sub("  +", " ", connection))).strip()
	try:
		connection = connection.split(" ")
		(local_ip, local_port) = connection[1].split(":")
		(remote_ip, remote_port) = connection[2].split(":")
	except ValueError:
		print("Error in following line!\r\n%s" % connection)
	return dict(zip(connection_keys, [ connection[0], local_ip, local_port, remote_ip, remote_port, connection[3], connection[4] ])) or None

def processConnections(all_connections):

	established_connections = []
	service_ports = []
	local_ips = []

	for connection in all_connections:

		# Keep the whole (formatted) line for established_connections, we'll assume the direction of the connection based on listening ports later
		if re.search("TCP", connection) and re.search("ESTABLISHED", connection) and not re.search("127.0.0.1", connection) and not re.search("\[\:\:1\]", connection):
			if DEBUG: print("Adding connection: %s" % connection)
			established_connections.append(convertLine(connection))

		# Only keep the port # for listening services, we'll check agianst this for direction of connection
		if re.search("TCP", connection) and re.search("LISTENING", connection) and not re.search("\[\:\:\]", connection) and not re.search("\[\:\:1\]", connection):
			temp_service_port = convertLine(connection)['local_port']
			if temp_service_port not in set(service_ports):
				service_ports.append(temp_service_port)
				if DEBUG: print("Found local service port: %s" % connection)

		# Process the local IP addresses
		if re.search("TCP", connection) and not re.search("0.0.0.0", connection) and not re.search("127.0.0.1", connection) and not re.search("\[\:\:\]", connection) and not re.search("\[\:\:1\]", connection):
			temp_local_ip = convertLine(connection)['local_ip']
			if temp_local_ip not in set(local_ips):
				local_ips.append(temp_local_ip)
				if DEBUG: print("Found unique IP: %s" % connection)
		else:
			if DEBUG: print("Skipping : %s" % connection)

	return (established_connections, service_ports, local_ips)

def connectionBuilder(graph, established_connections, service_ports, local_ips):
	
	# Build the nodes in the graph
	nodes = []

	# A hackish way of representing a multi-homed host.
	# TODO: Add analysis of "local" nodes and update if new local IP addresses are found or removed
	node_local_ip = '\n'.join(local_ips)

	# Each IP is considered a potential node. If the local address is not already known, add it to the list of local listening addresses which will eventually comprise a single local node.
	# Otherwise, add it as a remote node.
	for connection in established_connections:
		if node_local_ip not in nodes:
			nodes.append(node_local_ip)
		if connection['remote_ip'] not in nodes:
			nodes.append(connection['remote_ip'])
	graph.add_nodes_from(nodes)

	for connection in established_connections:
		if connection['local_port'] in service_ports:
			graph.add_path([connection['remote_ip'], node_local_ip], port=connection['local_port'])
		else:
			graph.add_path([node_local_ip, connection['remote_ip']], port=connection['remote_port'])
	

def main():
	all_connections = []
	graph = nx.DiGraph()
	# using command netstat -ano
	files_list = getFilesList()
	if DEBUG: print(files_list)
	for vis_file in files_list:
		all_connections = []
		try:
			with open(vis_file) as file:
				for line in file:
					all_connections.append(line.upper().strip())
			(established_connections, service_ports, local_ips) = processConnections(all_connections)
			if DEBUG: print(established_connections)
			if DEBUG: print(service_ports)
			if DEBUG: print(local_ips)
			connectionBuilder(graph, established_connections, service_ports, local_ips)
		except IOError as err:
			exit("Error opening file: %s" % err)
	for n in graph:
		graph.node[n]['name'] = n
	if DEBUG: print(graph.nodes())
	if DEBUG: print(graph.edges())
	d = json_graph.node_link_data(graph)
	json.dump(d, open("test.json", "w"))
	
if __name__ == '__main__':
	main()
