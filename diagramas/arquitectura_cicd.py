"""Genera Imagenes/diagramas/arquitectura_cicd.png para secciones/03-propuesta.tex.

Distribución (de arriba hacia abajo):
  fila 1 (revisión):   Desarrollador -> Repositorio -> Build -> Compuertas; Build -> Registro
  fila 2 (entornos):   Instancia de prueba (bajo demanda, validación manual)  |  Producción
  fila 3 (liberación): rama de liberación -> Verificaciones -> Aprobación manual -> Producción
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.generic.storage import Storage
from diagrams.onprem.client import Client, User
from diagrams.onprem.container import Docker
from diagrams.onprem.database import MongoDB, MySQL
from diagrams.onprem.vcs import Gitlab
from diagrams.programming.flowchart import Decision  # Ícono neutro: las compuertas aún no están definidas

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


def app_with_data(data_label):
    """Contenedor de la aplicación con sus dos bases de datos."""
    app = Docker("App (contenedor)")
    with Cluster(data_label, graph_attr=data_attr):
        dbs = (MySQL("MySQL"), MongoDB("MongoDB"))
    for db in dbs:
        link(app, db, arrow="none")
    return app


with Diagram(
    "Arquitectura del modelo de entrega continua",
    filename=str(OUT), outformat="png", direction="TB",
    graph_attr=graph_attr, show=False,
) as diag:
    dev = Client("Desarrollador")

    with Cluster("Infraestructura autoalojada (on-premise)", graph_attr=onprem_attr):
        with Cluster("GitLab", graph_attr=stage_attr):
            repo = Gitlab("Repositorio Git")
            registry = Storage("Registro de\ncontenedores")

        with Cluster("Pipeline de revisión (cada rama)", graph_attr=stage_attr):
            build = Docker("Build de imagen\nversionada")
            gate = Decision("Compuertas\nde calidad")

        with Cluster("Instancia de prueba (persistente, validación manual)", graph_attr=stage_attr):
            test_app = app_with_data("Datos de prueba (seeders)")

        with Cluster("Pipeline de despliegue (rama de liberación)", graph_attr=stage_attr):
            checks = Decision("Verificaciones")
            approval = User("Aprobación manual\n(rol autorizado)")

        with Cluster("Producción", graph_attr=stage_attr):
            prod_app = app_with_data("Datos de producción")

    # Filas: nodos con el mismo rank quedan alineados horizontalmente.
    def same_rank(*nodes):
        diag.dot.body.append("\t{rank=same; %s}" % "; ".join('"%s"' % n.nodeid for n in nodes))

    same_rank(dev, repo, build, gate)
    same_rank(registry, checks, approval)
    same_rank(test_app, prod_app)

    # Fila 1: integración continua (pesos altos para mantenerla recta)
    link(dev, repo, "1. push de rama", weight="20")
    link(repo, build, "2", weight="20")
    link(build, gate, "3", weight="20")
    link(build, registry, "imagen", style="dashed")

    # Despliegue de prueba bajo demanda
    link(registry, test_app, "4. despliegue\nbajo demanda")

    # Liberación a producción
    link(repo, checks, "5. rama de liberación")
    link(checks, approval, "6")
    link(approval, prod_app, "7. migraciones en orden\n+ verificación")
