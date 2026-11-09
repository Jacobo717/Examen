import csv
import os
import sys
import time

import psycopg

url = os.environ["DATABASE_URL"]
path = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado/part-00000"
for attempt in range(30):
    try:
        with psycopg.connect(url) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS resultados (clave TEXT PRIMARY KEY, ticket_promedio NUMERIC(14,2) NOT NULL, registros INTEGER NOT NULL)")
            with open(path, encoding="utf-8") as source:
                rows = [(r[0], float(r[1]), int(r[2])) for r in csv.reader(source, delimiter="\t") if len(r) == 3]
            conn.cursor().executemany("INSERT INTO resultados (clave,ticket_promedio,registros) VALUES (%s,%s,%s) ON CONFLICT (clave) DO UPDATE SET ticket_promedio=EXCLUDED.ticket_promedio, registros=EXCLUDED.registros", rows)
            conn.commit()
        print(f"Cargados {len(rows)} resultados desde {path}")
        break
    except psycopg.OperationalError:
        if attempt == 29:
            raise
        time.sleep(2)

