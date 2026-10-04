"""Genera Imagenes/diagramas/arquitectura_cicd.png para secciones/03-propuesta.tex.

Flujo de izquierda a derecha en dos carriles que parten del repositorio:
  carril superior (revisión):   Build -> Compuertas -> Registro -> Instancia de prueba
  carril inferior (liberación): Verificaciones -> Aprobación manual -> Producción
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge, Node
from diagrams.generic.storage import Storage
from diagrams.onprem.client import Client, User
from diagrams.onprem.container import Docker
from diagrams.onprem.database import MongoDB, MySQL
from diagrams.onprem.vcs import Gitlab
from diagrams.programming.flowchart import Decision  # Ícono neutro: las compuertas aún no están definidas

OUT = Path(__file__).resolve().parent.parent / "Imagenes" / "diagramas" / "arquitectura_cicd"

INK = "#2F3B4A"
Node._height = 2.4  # La altura por defecto (1.9) está pensada para fuente de 13 pt; con 20 pt la etiqueta tapa el ícono
graph_attr = {
    "fontname": "Sans-Serif", "splines": "spline", "newrank": "true",
    "nodesep": "0.8", "ranksep": "1.0", "pad": "0.4",
}
node_attr = {"fontsize": "20"}
onprem_attr = {"labelloc": "t", "labeljust": "l", "margin": "28", "fontsize": "24", "bgcolor": "#F5F7FA", "pencolor": "#9AA5B1", "style": "rounded"}
stage_attr = {"labelloc": "t", "labeljust": "l", "margin": "20", "fontsize": "21", "bgcolor": "#E4EEF8", "pencolor": "#7FA3C7", "style": "rounded"}
data_attr = {"labelloc": "t", "labeljust": "l", "margin": "12", "fontsize": "17", "bgcolor": "#FFFFFF", "pencolor": "#8896A5", "style": "dashed,rounded"}


def link(a, b, label="", **kw):
    """Arista con la etiqueta sobre la línea (no flotante) para que no se encime."""
    a.connect(b, Edge(label=label, color=INK, fontcolor=INK, fontsize="19", penwidth="1.4", forward=True, **kw))


def environment(title, data_label):
    """Clúster con la aplicación y sus dos bases de datos; devuelve el nodo de la aplicación."""
    with Cluster(title, graph_attr=stage_attr):
        app = Docker("App")
        with Cluster(data_label, graph_attr=data_attr):
            dbs = (MySQL("MySQL"), MongoDB("MongoDB"))
        for db in dbs:
            app.connect(db, Edge(color=INK, dir="none"))
    return app


with Diagram(
    "", filename=str(OUT), outformat="png", direction="LR",
    graph_attr=graph_attr, node_attr=node_attr, show=False,
):
    dev = Client("Desarrollador")

    with Cluster("Infraestructura autoalojada (on-premise)", graph_attr=onprem_attr):
        repo = Gitlab("Repositorio\n(GitLab)")

        # Graphviz (LR) coloca abajo el primer carril declarado: liberación va primero para quedar abajo.
        with Cluster("Pipeline de despliegue (rama de liberación)", graph_attr=stage_attr):
            checks = Decision("Verificaciones")
            approval = User("Aprobación manual\n(rol autorizado)")

        prod_app = environment("Producción", "Datos de producción")

        with Cluster("Pipeline de revisión (cada rama)", graph_attr=stage_attr):
            build = Docker("Build de imagen\nversionada")
            gate = Decision("Compuertas\nde calidad")

        registry = Storage("Registro de contenedores")
        test_app = environment("Instancia de prueba (persistente, validación manual)", "Datos de prueba (seeders)")

    link(dev, repo, "1. push")

    # Carril superior: revisión y despliegue de prueba bajo demanda
    link(repo, build, "2. cada rama")
    link(build, gate)
    link(gate, registry, "3. imagen")
    link(registry, test_app, "4. bajo demanda")

    # Carril inferior: liberación a producción
    link(repo, checks, "5. rama de\nliberación")
    link(checks, approval)
    link(approval, prod_app, "6. migraciones\n+ verificación", minlen="2")
