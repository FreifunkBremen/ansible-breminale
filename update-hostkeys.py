#!/usr/bin/env python
#
# Aktualisiert die SSH-Host-Keys der Nodes in der ~/.ssh/known_hosts
#

from sys import path
path.append("lib")

import hosts
import os

from threading import Thread
from Queue import Queue

known_hosts = os.path.expanduser("~") + "/.ssh/known_hosts"
queue       = Queue(10)
num_threads = 10

def worker():
    while True:
        host = queue.get()

        # Add to known_hosts
        os.system("ssh -o StrictHostKeyChecking=no -o HashKnownHosts=no root@" + host + " true")

        queue.task_done()

# Start worker threads
q = Queue()
for i in range(num_threads):
     t = Thread(target=worker)
     t.daemon = True
     t.start()

# Fill queue
for value in hosts.load()['_meta']['hostvars'].itervalues():
    host = value['ansible_ssh_host']

    # Remove from known_hosts
    for addr in [host, host.replace("::",":0:")]:
        os.system("ssh-keygen -f " + known_hosts + " -R " + addr + " 2> /dev/null > /dev/null")

    queue.put(host)

# block until all tasks are done
queue.join()
