Breminale-Ansible
=================

## Kommandos

### ~/.ssh/known_hosts aktualisieren (legacy)

```bash
./update-hostkeys.py
```

### Edit Nodes
#### Node-Settings aktualisieren (All around Radio)

```bash
ansible-playbook playbooks/nodes-settings.yml -i nodes
```

#### Node-Info aktualisieren (Name, Geolocation)

```bash
ansible-playbook playbooks/nodes-settings.yml -i nodes
```

### Node-Upgrade/Flash

#### From Nodes(-Cache/Monitoring)

```bash
ansible-playbook -i nodes playbooks/nodes-upgrade.yml
```

#### Link-Local Discovery

```bash
 ./scripts/discovery-write
 ansible-playbook -i nodes_discovery playbooks/nodes-upgrade.yml
```
or
for complete automatic
```bash
 ansible-playbook -i nodes-link-local playbooks/nodes-upgrade.yml
```
