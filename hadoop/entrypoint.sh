#!/bin/bash
set -eu
mkdir -p /run/sshd /shared-ssh /home/hadoop/.ssh
chown -R hadoop:hadoop /shared-ssh /home/hadoop/.ssh
if [ ! -f /shared-ssh/id_ed25519 ]; then su - hadoop -c 'ssh-keygen -q -t ed25519 -N "" -f /shared-ssh/id_ed25519'; fi
cp /shared-ssh/id_ed25519.pub /home/hadoop/.ssh/authorized_keys
cp /shared-ssh/id_ed25519 /home/hadoop/.ssh/id_ed25519
chown hadoop:hadoop /home/hadoop/.ssh/authorized_keys /home/hadoop/.ssh/id_ed25519
chmod 700 /home/hadoop/.ssh && chmod 600 /home/hadoop/.ssh/authorized_keys /home/hadoop/.ssh/id_ed25519 /shared-ssh/id_ed25519
printf 'Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n' > /home/hadoop/.ssh/config
chown hadoop:hadoop /home/hadoop/.ssh/config
chmod 600 /home/hadoop/.ssh/config
printf 'PasswordAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\n' > /etc/ssh/sshd_config.d/datamart.conf
/usr/sbin/sshd
echo "Hadoop listo: $(hadoop version | head -n 1)"
exec tail -f /dev/null

