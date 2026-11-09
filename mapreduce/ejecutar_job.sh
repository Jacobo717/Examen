#!/bin/bash
set -euo pipefail

input="/data/input/ventas_${MATRICULA:-125054263}.csv"
output="/data/output/resultado"

if [ ! -r "$input" ]; then
  echo "No se encontró el dataset esperado: $input" >&2
  exit 1
fi

rm -rf "$output"
echo "Ejecutando Hadoop Streaming sobre $input"
time hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -files /app/mapper.py,/app/reducer.py \
  -input "$input" \
  -output "$output" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"
echo "Job terminado: $output/part-00000"
