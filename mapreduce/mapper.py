#!/usr/bin/env python3
import csv
import sys

for line in sys.stdin:
    try:
        row = next(csv.reader([line]))
        if not row or row[0].strip().lower() == "id" or len(row) != 8:
            continue
        tienda = row[2].strip()
        cantidad = int(row[5])
        precio = float(row[6])
        if not tienda or cantidad < 0 or precio < 0:
            continue
        print(f"{tienda}\t{cantidad * precio:.10f}\t1")
    except (ValueError, IndexError, csv.Error):
        continue

