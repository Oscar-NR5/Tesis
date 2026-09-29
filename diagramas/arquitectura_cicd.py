"""Genera Imagenes/diagramas/arquitectura_cicd.png para secciones/03-propuesta.tex.

Distribución (flujo de izquierda a derecha, luego hacia abajo):
  fila 1 (CI):        Desarrollador -> Repositorio -> Pipeline -> Build -> Compuertas
  fila 2 (entornos):  Producción  <-(validación manual)-  Entorno de prueba efímero
  fila 3 (datos):     bases de datos duales de cada entorno
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.ci import GitlabCI
from diagrams.onprem.client import Client
from diagrams.onprem.container import Docker
from diagrams.onprem.database import MongoDB, MySQL
from diagrams.onprem.security import Trivy  # Sustituir por el ícono de la herramienta real (p. ej. SonarQube)
from diagrams.onprem.vcs import Gitlab

OUT = Path(__file__).resolve().parent.parent / "Imagenes" / "diagramas" / "arquitectura_cicd"

INK = "#2F3B4A"
graph_attr = {
    "fontsize": "22", "fontname": "Sans-Serif", "labelloc": "b",
    "splines": "spline", "newrank": "true",
    "nodesep": "0.9", "ranksep": "1.1", "pad": "0.5",
}
onprem_attr = {"labelloc": "t", "labeljust": "l", "margin": "32", "fontsize": "16", "bgcolor": "#F5F7FA", "pencolor": "#9AA5B1", "style": "rounded"}
stage_attr = {"labelloc": "t", "labeljust": "l", "margin": "24", "fontsize": "15", "bgcolor": "#E4EEF8", "pencolor": "#7FA3C7", "style": "rounded"}
data_attr = {"labelloc": "t", "labeljust": "l", "margin": "16", "fontsize": "12", "bgcolor": "#FFFFFF", "pencolor": "#8896A5", "style": "dashed,rounded"}


def link(a, b, label="", arrow="fwd", **kw):
    """Arista con control explícito de la punta de flecha."""
    a.connect(b, Edge(xlabel=label, color=INK, fontsize="13", penwidth="1.4",
                      forward=arrow == "fwd", reverse=arrow == "back", **kw))


with Diagram(
    "Arquitectura del modelo de entrega continua",
    filename=str(OUT), outformat="png", direction="TB",
    graph_attr=graph_attr, show=False,
) as diag:
    dev = Client("Desarrollador")

    with Cluster("Infraestructura autoalojada (on-premise)", graph_attr=onprem_attr):
        repo = Gitlab("Repositorio Git")

        with Cluster("Runner CI/CD", graph_attr=stage_attr):
            pipe = GitlabCI("Pipeline")
            build = Docker("Build de imagen\ninmutable")
            gate = Trivy("Compuertas de calidad\n(análisis estático)")

        with Cluster("Producción", graph_attr=stage_attr):
            prod_app = Docker("App (contenedor)")
            with Cluster("Datos duales", graph_attr=data_attr):
                prod_mysql = MySQL("MySQL")
                prod_mongo = MongoDB("MongoDB")

        with Cluster("Entorno de prueba efímero", graph_attr=stage_attr):
            test_app = Docker("App (contenedor)")
            with Cluster("Datos duales\n(dump sanitizado)", graph_attr=data_attr):
                test_mysql = MySQL("MySQL")
                test_mongo = MongoDB("MongoDB")

    # Filas: nodos con el mismo rank quedan alineados horizontalmente.
    diag.dot.body.append("\t{rank=same; %s}" % "; ".join('"%s"' % n.nodeid for n in (dev, repo, pipe, build, gate)))
    diag.dot.body.append("\t{rank=same; %s}" % "; ".join('"%s"' % n.nodeid for n in (prod_app, test_app)))

    # Fila 1: integración continua (pesos altos para mantenerla recta)
    link(dev, repo, "1. git push", weight="20")
    link(repo, pipe, "2. trigger", weight="20")
    link(pipe, build, "3. build", weight="20")
    link(build, gate, "4. análisis", weight="20")

    # Paso a la fila 2: aprovisionamiento y promoción
    link(gate, test_app, "5. aprovisiona", weight="20")
    link(prod_app, test_app, "6. validación manual\naprobada\n(misma imagen)", arrow="back")

    # Fila 3: datos de cada entorno
    for db in (prod_mysql, prod_mongo):
        link(prod_app, db, arrow="none")
    for db in (test_mysql, test_mongo):
        link(test_app, db, arrow="none")