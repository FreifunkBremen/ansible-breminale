#!/usr/bin/env python2
#
# Displays reachable nodes
#

from sys import path
path.append("lib")

import signal
import json
import re
import os
import sys

if len(sys.argv) != 2:
  sys.stderr.write("usage: %s interface\n" % sys.argv[0])
  sys.exit(1)


device = sys.argv[1]


def signal_handler(signal, frame):
  print 'Good bye!'
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

recheck = True;

while recheck:
  addresses     = re.findall(r'(fe80::\S*): .* time=([0-9\.]+) ms', os.popen("ping6 -L -I " + device + " ff02::1 -c 2").read())

  found = []
  for (addr,ms) in addresses:
    host = {"ansible_ssh_host": addr}
    host['ms'] = float(ms)
    found.append(host)

  # Clear screen
  os.system("clear")

  print("%i Hosts found\n" % len(found))

  for host in found:
    print("%-27s %0.3f" % (host['ansible_ssh_host'], host['ms']))

  recheck = raw_input("write this json:") != "y"


data = {}
hostvars = {}

def hostname(addr):
  return addr.replace(":","")

my_list = [hostname(addr) for (addr,ms) in addresses]
data["nodes"] = [ e for i, e in enumerate(my_list) if my_list.index(e) == i]


for (addr,ms) in addresses:
  hostvars[hostname(addr)] = {"ansible_ssh_host": addr+"%"+device}
  
data["_meta"] = {"hostvars": hostvars}

obj = open('nodes.json', 'wb')
obj.write(json.dumps(data,indent=4))
obj.close()
