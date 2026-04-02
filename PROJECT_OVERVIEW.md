# PROJECT OVERVIEW

## Qué estamos construyendo

Estamos construyendo un copilot para ecommerce que ayuda a detectar y explicar problemas de pricing en marketplaces.

La idea central es simple:

- encontrar publicaciones con margen roto
- detectar diferencias de precio entre canales
- priorizar qué problema revisar primero
- sugerir qué acción tomar

No es un bot que decide solo. Es una capa de apoyo para un ecommerce manager que hoy suele revisar esto tarde, a mano, o con información incompleta.

## Por qué importa

En ecommerce marketplace, un error pequeño de precio puede transformarse rápido en una pérdida grande.

Algunos ejemplos comunes:

- una promo deja un producto vendiéndose con pérdida
- un canal tiene un precio muy distinto al resto
- fees y costos logísticos hacen que la venta deje de ser rentable

El problema no es solo detectar que algo está mal. El problema real es saber:

- qué tan grave es
- cuánto dinero podría costar
- qué hay que revisar primero
- y qué acción conviene tomar

Eso es lo que este producto busca resolver.

## Cómo se ve el producto final

El producto final se parece a un cockpit operativo para un equipo ecommerce.

Una persona entra y ve una inbox de alertas priorizadas. Cada alerta muestra:

- qué SKU está en problema
- en qué canal
- qué tipo de problema tiene
- cuánto dinero podría perderse
- qué tan urgente es
- qué acción se recomienda

Cuando entra al detalle de una alerta, ve:

- costo
- precio
- margen
- explicación simple del problema
- por qué esa alerta tiene alta prioridad
- acciones disponibles, como bloquear publicación, marcar revisión o alertar

Además, el sistema suma una capa de copilot que no reemplaza las reglas, sino que traduce el problema a lenguaje simple:

- qué pasó
- cuál es el impacto
- qué haría ahora

## Qué existe hoy

Hoy ya existe un POC funcional de backend.

Ese POC:

- usa datos mock
- detecta anomalías con reglas claras
- calcula pérdida estimada
- asigna prioridad
- expone alertas por API
- permite simular acciones

Eso significa que la base del producto ya está modelada. Ya no estamos en una etapa de idea abstracta. Ya existe una primera versión operable del sistema.

## Qué falta

Faltan varias piezas para que esto se vea como producto y no solo como backend:

- frontend claro para navegar alertas
- vista de detalle bien diseñada
- timeline operativa
- capa copilot con explicaciones en lenguaje simple
- refinamiento de la experiencia de uso

También faltan cosas que no son prioridad todavía:

- integraciones reales con marketplaces
- autenticación
- multiusuario
- monitoreo más serio
- lógica productiva de deployment

## Hacia dónde va esto

La dirección no es construir otro dashboard lleno de métricas.

La dirección es construir una herramienta operativa que ayude a tomar decisiones rápidas sobre pricing y margen en marketplaces.

Si evoluciona bien, esto puede convertirse en un sistema que:

- vigila continuamente publicaciones y promociones
- prioriza automáticamente riesgos comerciales
- explica el problema en lenguaje claro
- propone la mejor acción posible
- y deja trazabilidad de lo que se hizo

En simple: queremos pasar de “revisar problemas tarde y a mano” a “tener una bandeja clara de riesgos comerciales con contexto y siguiente acción”.

## Resumen en una frase

Estamos construyendo un copilot ecommerce para detectar, priorizar y explicar problemas de pricing en marketplaces antes de que se conviertan en pérdida.
