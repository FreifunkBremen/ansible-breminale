import urllib
import json
import os

network   = "2a00:c380:dead::"
cachedir  = os.path.dirname(os.path.abspath(__file__)) + "/../.cache"
device    = os.environ.get('DEV', "1")
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

  for id, value in data['_meta']['hostvars'].iteritems():
    # calculate link local address
    m = hex((int(id.translate(' .:-'),16) ^ 0x020000000000) - 2 )[2:]
    value['ansible_ssh_host'] = 'fe80::%s:%sff:fe%s:%s%%%s' %(m[:4],m[4:6],m[6:8],m[8:12], device)

  return data


def getCached():
  if not os.path.isfile(cachefile):
    # fill cache if empty
    load()

  json_data = open(cachefile).read()
  data      = json.loads(json_data)

  return data
