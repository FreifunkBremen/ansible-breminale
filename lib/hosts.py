import urllib
import json

network = "2a00:c380:dead::"

def load():
  response = urllib.urlopen("http://monitoring.breminale.digineo.de/json/ansible")
  data     = json.loads(response.read())

  for value in data['_meta']['hostvars'].itervalues():
      value['ansible_ssh_host'] = value['ansible_ssh_host'].replace("fe80::",network)

  return data
