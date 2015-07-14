#!/usr/bin/env python
#
# Aktualisiert die SSH-Host-Keys der Nodes in der ~/.ssh/known_hosts
#

import urllib
import os
import json

from threading import Thread
from Queue import Queue

known_hosts = os.path.expanduser("~") + "/.ssh/known_hosts"
network     = "2a00:c380:dead::"
response    = urllib.urlopen("http://monitoring.breminale.digineo.de/json/ansible")
result      = json.loads(response.read())
queue       = Queue(10)
num_threads = 10

def worker():
    while True:
        host = queue.get()
        os.system("ssh-keygen -f " + known_hosts + " -R " + host + " 2> /dev/null > /dev/null")
        os.system("ssh -o StrictHostKeyChecking=no -o HashKnownHosts=no root@" + host + " true")
        queue.task_done()
        print(host)

# Start worker threads
q = Queue()
for i in range(num_threads):
     t = Thread(target=worker)
     t.daemon = True
     t.start()

# Fill queue
for value in result['_meta']['hostvars'].itervalues():
    queue.put(value['ansible_ssh_host'].replace("fe80::",network))

queue.join() # block until all tasks are done
