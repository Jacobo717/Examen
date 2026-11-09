#!/usr/bin/env python3
import sys

current = None
total = 0.0
count = 0

def emit(key, amount, rows):
    if key is not None and rows:
        print(f"{key}\t{amount / rows:.2f}\t{rows}")

for line in sys.stdin:
    try:
        key, amount, rows = line.rstrip("\n").split("\t")
        amount, rows = float(amount), int(rows)
    except ValueError:
        continue
    if current != key:
        emit(current, total, count)
        current, total, count = key, 0.0, 0
    total += amount
    count += rows
emit(current, total, count)

