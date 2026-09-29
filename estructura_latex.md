# Estructura LaTeX del proyecto

## Árbol de archivos

```text
.
├── main.tex
├── portada.tex
├── misreferencias.bib
├── Imagenes/
└── secciones/
    ├── 01-planteamiento.tex
    ├── 02-marco-teorico.tex
    └── 03-propuesta.tex
```

## Estructura del documento

```text
main.tex
├── Preámbulo
│   ├── Clase: article
│   ├── Idioma: español
│   ├── Configuración de página y tipografía
│   ├── Paquetes para figuras, tablas y utilidades
│   ├── Bibliografía: natbib / ieeetr
│   ├── Ruta de imágenes: Imagenes/
│   └── Metadatos del documento
├── Documento
│   ├── portada.tex
│   ├── secciones/01-planteamiento.tex
│   │   ├── Introducción
│   │   └── Planteamiento del problema
│   │       ├── Antecedentes
│   │       ├── Definición del problema
│   │       ├── Justificación
│   │       ├── Objetivo general
│   │       ├── Objetivos específicos
│   │       ├── Hipótesis
│   │       └── Alcances y limitaciones
│   ├── secciones/02-marco-teorico.tex
│   │   └── Marco teórico
│   │       └── Subtema
│   │           └── Subsubtema
│   ├── secciones/03-propuesta.tex
│   │   ├── Producto propuesto
│   │   ├── Metodología
│   │   ├── Programa de actividades
│   │   └── Resultados esperados
│   ├── Bibliografía
│   │   └── misreferencias.bib
│   └── Apéndice
│       └── Apéndice
└── Fin del documento
```

## Orden de compilación

```text
main.tex
  ├── \input{portada}
  ├── \input{secciones/01-planteamiento}
  ├── \input{secciones/02-marco-teorico}
  ├── \input{secciones/03-propuesta}
  ├── \bibliography{misreferencias}
  └── \appendix
```