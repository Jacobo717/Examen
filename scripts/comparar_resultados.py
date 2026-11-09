import csv
import sys


def leer(path: str) -> dict[str, tuple[float, int]]:
    with open(path, newline="", encoding="utf-8-sig") as archivo:
        filas = csv.reader(archivo, delimiter="\t")
        resultados = {}
        for fila in filas:
            if len(fila) != 3:
                raise ValueError(f"Fila inválida en {path}: {fila!r}")
            clave, promedio, registros = fila
            resultados[clave] = (round(float(promedio), 2), int(registros))
        return resultados


if len(sys.argv) != 3:
    raise SystemExit("Uso: python comparar_resultados.py salida_secuencial.tsv part-00000")

secuencial, hadoop = map(leer, sys.argv[1:])
if secuencial != hadoop:
    claves = sorted(set(secuencial) | set(hadoop))
    diferencias = [
        f"{clave}: secuencial={secuencial.get(clave)}, hadoop={hadoop.get(clave)}"
        for clave in claves
        if secuencial.get(clave) != hadoop.get(clave)
    ]
    raise SystemExit("Diferencias encontradas:\n" + "\n".join(diferencias))

print(f"COINCIDEN: {len(hadoop)} tiendas; promedio y registros iguales.")
