
Para demostrar cómo la arquitectura toma decisiones en la práctica, a continuación se detalla la traza de ejecución de tres escenarios reales del set de datos. El objetivo es mostrar el recorrido del flujo de información capa por capa, detallando cómo interactúan el filtro determinista de Python, el motor de inteligencia artificial y la orquestación de herramientas finales.


Caso de Estudio 1: El Bug Técnico (TCK-1004) 

* **Asunto:** "La app se cierra sola al abrir el carrito"
* **Logs adjuntos:** `crash order_draft=ORD-77201 screen=cart app_version=5.2.8 os=Android_9 stacktrace=NullPointerException at CartRenderer.line88`
* **ID de Pedido:** `ORD-77201`

#### Paso 1: Capa de Comprensión (Filtro Determinista)

El ticket ingresa al sistema y es procesado primero por un script de Python. El sistema realiza dos validaciones deterministas antes de invocar la API del LLM:

1. **Completitud de datos:** El script verifica que no existan variables nulas críticas. Al encontrar el identificador de pedido (`ORD-77201`) y el string del log técnico, el ticket supera la regla de "Falta de Información".
2. **Control de duplicados:** Se simula una consulta rápida a la base de datos de soporte utilizando el identificador del pedido. En este momento no hay reclamos previos activos para esta orden, por lo que el ticket se registra como nuevo.

**Decisión en Capa 1:** El ticket es válido y requiere análisis. Se aprueba la llamada a la API y se envía el payload completo a la Capa 2.

#### Paso 2: Capa de Diagnóstico (Análisis del LLM)

El LLM recibe el asunto del usuario, la queja del chat y los logs del sistema como contexto de entrada. El agente evalúa la información utilizando las directrices del sistema:

* **Contraste de hipótesis:** El cliente reporta que la aplicación se cierra al abrir el carrito de compras. Al escanear el log técnico, el modelo no encuentra bloqueos lógicos ni problemas operativos del repartidor; en su lugar, localiza la palabra clave `stacktrace` y la excepción nativa `NullPointerException` en el módulo de renderizado.
* **Aplicación de prioridad:** Siguiendo las reglas de la arquitectura, la existencia de una excepción de código no controlada o una caída del sistema se clasifica inmediatamente por encima de cualquier otra queja o regla operativa.

**Decisión en Capa 2:** El modelo genera un JSON estructurado con la clasificación `Bug`  y la justificación técnica de la excepción, retornándolo al orquestador.

#### Paso 3: Capa de Orquestación y Acción

El script intercepta la respuesta de la API, limpia el formato mediante expresiones regulares (extrayendo únicamente el bloque de llaves del JSON) y ejecuta el mapeo de la decisión:

* El orquestador lee la clasificación `Bug` y asume una severidad alta debido al impacto del crash en el flujo de compra.
* Selecciona la herramienta correspondiente para esta categoría en el árbol de decisiones.

**Acción final:** El sistema ejecuta el comando `crear_incidencia_jira(BUG-1004)`, enviando de forma automática el log de error y el stacktrace al backlog del equipo de desarrollo, evitando que el ticket consuma tiempo del equipo de soporte de primer nivel.

---

Caso de Estudio 2: La Reiteración o Duplicado (TCK-1017) 

* **Asunto:** "sigo sin poder usar el carrito"
* **Cuerpo:** "hola, es sobre lo mismo del carrito que se cierra, sigue pasando en mi samsung"
* **ID de Pedido:** `ORD-77201`

#### Paso 1: Capa de Comprensión (Filtro Determinista)

El ticket es recibido inmediatamente después de que el usuario del caso anterior volviera a escribir por el chat. El pipeline de entrada procesa la información en Python puro:

1. **Extracción de parámetros:** El script identifica el ID del pedido (`ORD-77201`).
2. **Detección de duplicados:** Se ejecuta la herramienta `buscar_tickets_abiertos(order_id="ORD-77201")`. El sistema detecta inmediatamente que ya existe un caso abierto para esta orden (`TCK-1004`).



**Decisión en Capa 1 (Retorno Temprano):** Al confirmar una coincidencia exacta, el sistema activa un atajo lógico. Para optimizar los costos de la API del LLM y evitar la creación de duplicados innecesarios, se bloquea el paso del ticket a la Capa 2.

#### Paso 2: Capa de Diagnóstico (Análisis del LLM)

* **Omitida por diseño:** El sistema no consume recursos de inteligencia artificial en esta interacción.

#### Paso 3: Capa de Orquestación y Acción

La Capa 1 entrega la etiqueta determinista de `Duplicado` de forma directa al orquestador de salida.

* El sistema selecciona la regla para duplicados en el árbol de decisiones.
* Se activa la herramienta encargada de unificar la información del cliente.

**Acción final:** El sistema ejecuta la función `merge_tickets(TCK-1017 -> TCK-1004)`. El nuevo mensaje del usuario se adjunta como actualización de contexto dentro de la incidencia original y se notifica automáticamente al usuario de que su reporte ya está siendo atendido, cerrando el ticket duplicado de inmediato.

---

Caso de Estudio 3: El Error de Configuración (TCK-1010) 

* **Asunto:** "No funciona el cupón"
* **Logs adjuntos:** `promo_code=VERANO26 result=BLOCKED reason=expired_date`
* **ID de Pedido:** `ORD-77255`

#### Paso 1: Capa de Comprensión (Filtro Determinista)

El ticket ingresa al flujo de soporte para su evaluación inicial:

1. **Completitud de datos:** El sistema valida la presencia de un código de descuento y logs técnicos de negocio. Al superar el filtro, se descarta el estado de "Falta de Información".
2. **Control de duplicados:** Se busca el ID del pedido en la base de datos simulada de soporte. Al no existir coincidencias previas, el ticket se considera un caso único de ingreso.

**Decisión en Capa 1:** El caso es apto para un diagnóstico detallado. El payload es empaquetado y transferido al modelo.

#### Paso 2: Capa de Diagnóstico (Análisis del LLM)

El LLM procesa la queja del usuario (el cupón "no funciona") frente a los parámetros internos registrados en el log del sistema:

* **Contraste de hipótesis:** El modelo detecta que la infraestructura funciona sin problemas. El log expone explícitamente que el backend aplicó la validación comercial correspondiente y bloqueó la transacción bajo el parámetro `result=BLOCKED` debido a que el periodo de vigencia de la promoción caducó (`reason=expired_date`).


* **Aplicación de prioridad:** Al tratarse de un bloqueo lógico preventivo programado en las reglas de negocio, el agente concluye que no hay fallas operativas ni errores de código en la plataforma. Clasifica la raíz del problema como una mala configuración del usuario al intentar usar un descuento inactivo.



**Decisión en Capa 2:** El modelo clasifica el ticket como `Configuracion` y redacta una explicación precisa basada en el log del sistema para que el usuario entienda el motivo real del error.

#### Paso 3: Capa de Orquestación y Acción

El orquestador de Python recibe e interpreta el JSON generado por el modelo:

* Al identificar la etiqueta `Configuracion`, el sistema asume una severidad baja.


* Dado que la resolución no requiere escalarse a un equipo especializado, se decide gatillar una acción de resolución en primer nivel.

**Acción final:** El sistema invoca la herramienta `enviar_resolucion_automatica()`. Se emite una respuesta clara informándole al cliente que el código de descuento ya no está vigente y se procede a cerrar el ticket automáticamente, resolviendo el caso sin costo operativo para el equipo de soporte humano.