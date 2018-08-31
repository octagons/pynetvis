# pynetvis
A super simple network visualization toolkit using D3 and Python
# Introduction
pynetvis is a tool to create visual node graphs of network connections based on the output of a host's "netstat -ano" command. Currently only tested on output from Windows hosts. This project is very immature and unlikely to work correctly in all cases.
# Usage
When vis.py is run, it will look for a folder containing files named by the host's IP address with a .txt filetype. The default location is "~/.network_vis/" but this can be changed by exporting NETWORKVIS.
Output will be a "test.json" file, which is automatically loaded. Double click "index.html" to view the output.
