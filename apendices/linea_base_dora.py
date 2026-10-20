"""Reproduce la linea base DORA a partir del historial de Git.

Uso: python3 linea_base_dora.py REPO COMMIT DESDE HASTA
Ej.: python3 linea_base_dora.py app 0f272d1 2026-04-12 2026-10-13
"""
import re
import statistics
import subprocess
import sys

repo, commit, desde, hasta = sys.argv[1:5]


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], check=True,
                          capture_output=True, text=True).stdout


# Cada merge a la rama principal se toma como un lote listo para produccion.
merges = git("log", "--first-parent", commit, "--merges",
             f"--since={desde}", f"--until={hasta}",
             "--format=%H %ct %s").splitlines()

CORRECCION = re.compile(r"hotfix|fix|bug|patch|correcci", re.I)
correcciones = 0
lead_times = []  # en dias
for linea in merges:
    h, fecha_merge, asunto = linea.split(" ", 2)
    if CORRECCION.search(asunto):  # el asunto trae el nombre de la rama
        correcciones += 1
    # Commits nuevos que trajo el merge: M^1..M^2
    fechas = git("log", "--format=%at", f"{h}^1..{h}^2").split()
    if fechas:
        inicio = min(int(f) for f in fechas)
        lead_times.append((int(fecha_merge) - inicio) / 86400)

n = len(merges)
print(f"Merges a la rama principal: {n}")
print(f"Ramas de correccion: {correcciones} ({correcciones / n:.1%})")
print(f"Lead time mediano: {statistics.median(lead_times) * 1440:.0f} min")
print(f"Lead time promedio: {statistics.mean(lead_times):.1f} dias")
print(f"Lead time maximo: {max(lead_times):.1f} dias")
