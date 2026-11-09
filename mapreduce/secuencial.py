#!/usr/bin/env python3
import csv
import sys
from collections import defaultdict

if len(sys.argv) != 2:
    raise SystemExit("Uso: python secuencial.py ruta.csv")
totals = defaultdict(lambda: [0.0, 0])
with open(sys.argv[1], newline="", encoding="utf-8") as source:
    reader = csv.DictReader(source)
    for row in reader:
        try:
            if not row or (row.get("id") or "").strip().lower() == "id":
                continue
            if None in row or any(row.get(field) is None for field in reader.fieldnames or []):
                continue
            tienda = row["tienda"].strip()
            cantidad = int(row["cantidad"])
            precio = float(row["precio_unitario"])
            if not tienda or cantidad < 0 or precio < 0:
                continue
            ingreso = cantidad * precio
            totals[tienda][0] += ingreso
            totals[tienda][1] += 1
        except (KeyError, TypeError, ValueError):
            continue
for tienda in sorted(totals):
    total, count = totals[tienda]
    print(f"{tienda}\t{total / count:.2f}\t{count}")

