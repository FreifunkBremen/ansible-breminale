#!/usr/bin/env python
#
# Aktualisiert die SSH-Host-Keys der Nodes in der ~/.ssh/known_hosts
#

import urllib
import os
import json

known_hosts = os.path.expanduser("~") + "/.ssh/known_hosts"
network     = "2a00:c380:dead:0:"
response    = urllib.urlopen("http://monitoring.breminale.digineo.de/json/ansible")
result      = json.loads(response.read())

for value in result['_meta']['hostvars'].itervalues():
  host = value['ansible_ssh_host'].replace("fe80::",network)

  os.system("ssh-keygen -f " + known_hosts + " -R " + host + " 2> /dev/null > /dev/null")
  os.system("ssh -o StrictHostKeyChecking=no -o HashKnownHosts=no root@" + host + " true")
