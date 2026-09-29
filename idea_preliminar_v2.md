## Título tentativo

Automatización del proceso de despliegue de un sistema en producción: entrega
continua y entornos de prueba bajo demanda sobre infraestructura propia.

## Planteamiento del Problema

Una organización opera un sistema de información en producción que integra
múltiples áreas funcionales (recursos humanos, patrimonio, control de unidades,
combustible y almacén) y que, por su alcance y uso intensivo, mantiene una alta
frecuencia de cambios. Su ciclo de despliegue es enteramente manual: no existe
contenedorización de la aplicación, no hay un pipeline de integración o entrega
continua, y no se dispone de entornos de prueba desplegables bajo demanda antes
de llevar un cambio a producción. Esto se traduce en un mayor tiempo de
despliegue por cambio, un mayor riesgo de error humano en el proceso, y un costo
elevado de retrabajo cuando un cambio, una vez en producción, no cumple lo que
el usuario final esperaba.

Este problema es abordable con la infraestructura ya disponible en la
organización, sin depender de proveedores de nube pública: mediante GitLab como
plataforma de integración y entrega continua es posible construir un proceso
completo de contenedorización, despliegue automatizado y generación de entornos
de prueba, siguiendo prácticas ya consolidadas en la industria. Sin embargo,
este tipo de proceso no se ha implementado para el sistema, en parte por su
origen (desarrollado originalmente por un proveedor externo que no concluyó el
proyecto) y por la complejidad adicional de integrar varias áreas funcionales
sobre una base de datos no relacional como fuente principal de información.

## Justificación

**Práctica.** Atiende un problema real y medible dentro de la organización:
miles de despliegues manuales acumulados, sin automatización, sobre un sistema
que sigue siendo el de mayor uso y mayor frecuencia de cambio.

**Técnica.** Permite validar si las prácticas de contenedorización e
integración y entrega continua ya consolidadas en la industria (control de
concurrencia, recuperación ante fallas, entornos de prueba efímeros) son
directamente aplicables a un sistema en producción con restricciones
particulares, o si requieren adaptaciones específicas, y documenta cuáles.

**Metodológica.** A diferencia de una comparación contra un proceso manual
hipotético, este trabajo cuenta con una línea base real y verificable: el
proceso manual actual, con su historial de despliegues, sobre el cual medir el
resultado de forma directa.

## Pregunta de Investigación

¿Cómo puede diseñarse e implementarse, usando GitLab como plataforma de
integración y entrega continua, un proceso de contenedorización e
integración/entrega continua para un sistema de información en producción, de
uso intensivo y alta frecuencia de cambios, y qué mejoras produce frente al
proceso de despliegue manual actual?

### Preguntas derivadas

- ¿Qué dependencias implícitas y particularidades propias del sistema
  condicionan su contenedorización, frente a un sistema pensado desde el inicio
  para operar en contenedores?
- ¿Qué prácticas de CI/CD consolidadas en la industria son directamente
  aplicables al sistema dentro de GitLab, y cuáles requieren adaptación?
- ¿Qué diferencia de tiempo de despliegue y de tiempo de disponibilidad de un
  entorno de prueba se obtiene frente al proceso manual actual?
- ¿Qué reducción, si la hay, se observa en el retrabajo asociado a la
  validación tardía de cambios con el usuario final?

## Objetivo

Diseñar e implementar, usando GitLab como plataforma de integración y entrega
continua, un proceso de contenedorización e integración/entrega continua para
el sistema en producción de la organización, y evaluar su impacto frente al
proceso de despliegue manual actual.

### Objetivos específicos

- Analizar la arquitectura y las dependencias del sistema para identificar los
  requisitos y restricciones de su contenedorización.
- Diseñar la estrategia de contenedorización del sistema, definiendo imágenes
  base, etapas de construcción y configuración de los servicios que lo
  componen.
- Implementar en GitLab un pipeline de integración y entrega continua para el
  sistema, incorporando prácticas de CI/CD consolidadas en la industria.
- Implementar un mecanismo de generación de entornos de prueba desplegables
  bajo demanda, previos al despliegue en producción.
- Evaluar el proceso resultante frente al proceso de despliegue manual actual,
  midiendo tiempo de despliegue, tiempo de disponibilidad de un entorno de
  prueba y frecuencia de retrabajo.

## Propuesta

Se propone construir, de forma incremental y usando GitLab como plataforma de
integración y entrega continua, un proceso de contenedorización e
integración/entrega continua para el sistema, partiendo del análisis de su
arquitectura actual y de sus dependencias implícitas. Las instancias de prueba
serán fijas, con recursos asignados de forma declarativa, y cada una contará
con su propia base de datos poblada únicamente con la estructura necesaria para
operar, sin datos de producción.

El diseño del pipeline seguirá prácticas de CI/CD consolidadas en la industria:
control de concurrencia sobre infraestructura compartida, recuperación ante
fallas del registro de contenedores, disciplina de migraciones y generación de
entornos de prueba bajo demanda, adaptándolas a las restricciones propias del
sistema (integración de varias áreas funcionales, dependencia de una base de
datos no relacional como fuente principal). El proceso resultante se
instrumentará para registrar tiempo de despliegue y tiempo de disponibilidad de
un entorno de prueba, comparándolos contra el historial del proceso manual
actual.

## Alcance

**Se contempla:** el sistema en producción como objeto de estudio; GitLab como
plataforma de integración y entrega continua; contenedorización de la
aplicación; un pipeline de integración y entrega continua; entornos de prueba
fijos, definidos de forma declarativa, con recursos de cómputo configurables
por instancia y base de datos propia (solo estructura, sin datos de
producción); evaluación cuantitativa frente al proceso manual actual.

**No se contempla (por el momento):** migración del motor de base de datos ni
reescritura de la lógica de negocio existente; despliegue sobre proveedores de
nube pública; observabilidad avanzada (monitoreo, alertas) más allá de lo
estrictamente necesario para operar el pipeline; generalización de la
propuesta a otras organizaciones; aprovisionamiento efímero de instancias
(creación y destrucción automática por cambio), que queda como posible
extensión futura.

**Limitaciones:** el trabajo se desarrolla sobre la infraestructura propia de
una única organización y un único sistema; los resultados de tiempo y
retrabajo son específicos a ese contexto y no pretenden generalizarse sin
validación adicional en otros entornos.
