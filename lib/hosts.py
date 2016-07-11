import urllib
import json
import os

network   = "2a00:c380:dead::"
cachedir  = os.path.dirname(os.path.abspath(__file__)) + "/../.cache"
cachefile = cachedir+"/nodes.json"

if not os.path.exists(cachedir):
  os.makedirs(cachedir)


def load():
  response = urllib.urlopen("https://mgmt.ffhb.de/api/aliases/ansible")
  body     = response.read()
  data     = json.loads(body)

  # Save nodes to cache
  with open(cachefile, 'w') as f:
    f.write(body)

  for value in data['_meta']['hostvars'].itervalues():
    value['ansible_ssh_host'] = value['ansible_ssh_host'].replace("fe80::",network)

  return data


def getCached():
  if not os.path.isfile(cachefile):
    # fill cache if empty
    load()

  json_data = open(cachefile).read()
  data      = json.loads(json_data)

  return data
