from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.vcs import Gitlab
from diagrams.onprem.ci import Gitlabci
from diagrams.onprem.container import Docker
from diagrams.onprem.database import Mysql, Mongodb
from diagrams.programming.language import Php
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.onprem.monitoring import Grafana
from diagrams.onprem.security import Vault

# 1. Atributos del lienzo (orientación vertical y espaciado amplio)
graph_attr = {
    "fontsize": "24",      # Letra más grande para los títulos de las fases
    "nodesep": "1.2",      # Mayor separación horizontal entre íconos
    "ranksep": "1.5",      # Mayor separación vertical entre líneas de flujo
    "pad": "0.5",          # Márgenes del lienzo
    "splines": "spline",   # Con "ortho" (default) las etiquetas de flecha quedan lejos de su línea
    "bgcolor": "transparent"
}

# 2. Atributos de los íconos (texto más legible)
node_attr = {
    "fontsize": "18",
    "imagepos": "tc",      # Ícono arriba del nodo, texto abajo (evita que se encimen)
}

# Títulos de las fases (el default de 12 se ve diminuto junto a los íconos)
cluster_attr = {
    "fontsize": "16",
    "margin": "20",
}

# 3. Atributos de las flechas (texto más grande)
edge_attr = {
    "fontsize": "16",
    "fontcolor": "#2c3e50"
}

# outformat="pdf" generará un archivo vectorial ideal para LaTeX
# direction="TB" (Top to Bottom) lo hace amigable para hojas en vertical
with Diagram("", filename="metodologia_cicd", show=False, direction="TB", outformat="pdf", 
             graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr):
    
    dev = Users("Desarrollador")

    with Cluster("Fases 1 y 6: Línea Base y Evaluación", graph_attr=cluster_attr):
        metrics = Grafana("Métricas DORA")

    with Cluster("Fases 2 y 3: Construcción y Compuertas", graph_attr=cluster_attr):
        repo = Gitlab("Repositorio\nGitLab")
        ci = Gitlabci("Pipeline CI")
        build = Docker("Contenedorización\nApp Web")
        qa_static = Php("Análisis Estático")
        qa_sec = Vault("Escaneo de\nSeguridad")

    with Cluster("Fase 4: Entornos de Prueba", graph_attr=cluster_attr):
        test_server = Server("Servidor de\nPrueba")
        test_app = Docker("Contenedor\nEfímero")
        test_db_scripts = Php("Migraciones y\nSeeders")

    with Cluster("Fase 5: Entrega Continua", graph_attr=cluster_attr):
        approval = Users("Aprobación\nManual")
        prod_server = Server("Servidor de\nProducción")
        prod_migrations = Php("Migraciones\nCoordinadas")
        prod_app = Docker("Nueva Versión\nApp")

    with Cluster("Bases de Datos Existentes (Legacy)", graph_attr=cluster_attr):
        db_mysql = Mysql("MySQL\n(Autenticación)")
        db_mongo = Mongodb("MongoDB\n(Negocio)")

    # --- Trazado del Flujo ---

    dev >> Edge(label="Push a rama", **edge_attr) >> repo
    repo >> ci >> build >> qa_static >> qa_sec

    # Flujo de Prueba
    qa_sec >> Edge(label="Despliegue bajo demanda", style="dashed", color="blue", **edge_attr) >> test_server
    test_server - test_app - test_db_scripts
    test_db_scripts >> Edge(label="Datos prueba", color="blue", **edge_attr) >> db_mysql
    test_db_scripts >> Edge(label="Datos prueba", color="blue", **edge_attr) >> db_mongo

    # Flujo de Producción
    qa_sec >> Edge(label="Merge a Release", color="darkgreen", **edge_attr) >> approval
    approval >> prod_server
    prod_server - prod_migrations
    prod_migrations >> Edge(label="Actualiza esquema", color="darkgreen", **edge_attr) >> db_mysql
    prod_migrations >> Edge(label="Actualiza esquema", color="darkgreen", **edge_attr) >> db_mongo
    prod_migrations >> Edge(label="Enruta tráfico", color="darkgreen", **edge_attr) >> prod_app

    # Flujo de Evaluación
    repo >> Edge(label="Línea Base", style="dotted", color="red", **edge_attr) >> metrics
    prod_app >> Edge(label="Medición Final", style="dotted", color="red", **edge_attr) >> metrics