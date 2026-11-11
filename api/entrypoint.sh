#!/bin/sh
set -eu
mkdir -p /root/.ssh
until [ -f /shared-ssh/id_ed25519 ]; do sleep 1; done
cp /shared-ssh/id_ed25519 /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519
ssh-keyscan -H hadoop >> /root/.ssh/known_hosts 2>/dev/null || true
ssh -o StrictHostKeyChecking=no hadoop@hadoop 'echo API_SSH_OK' || true
if [ -f /data/output/resultado/part-00000 ]; then
  python /app/cargar_resultados.py
else
  echo "Salida Hadoop aun no disponible; la API inicia sin recarga automatica."
fi
exec uvicorn app:app --host 0.0.0.0 --port 8000

