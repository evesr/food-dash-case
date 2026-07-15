
El agente ejecuta una matriz de enrutamiento basada en la clasificación previa del ticket. El objetivo de esta matriz es maximizar la resolución automática en casos de bajo impacto técnico y asegurar un escalamiento rápido y con contexto en incidentes críticos.

## 1. Bugs Técnicos (Prioridad Alta)

* **Condición:** El log del sistema confirma un fallo de infraestructura, excepción de código o error lógico transaccional (ej. cobros duplicados).
* **Acción del Agente:** * Escalar directamente al equipo de Ingeniería o Soporte Técnico Nivel 2.
* Ejecutar herramienta: `crear_ticket_jira()`, adjuntando el ID del pedido, el log del error y el *stacktrace* si existe.
* Respuesta al usuario: "Hemos detectado un inconveniente técnico con tu solicitud. Nuestro equipo de ingeniería ya fue notificado y está trabajando en una solución urgente."



## 2. Problemas de Operación / Efectividad (Prioridad Alta)

* **Condición:** El sistema operó correctamente, pero la logística en terreno falló (ej. discrepancia de GPS, saturación de repartidores, pedidos incompletos).
* **Acción del Agente:**
* Derivar a la cola del equipo de Servicio al Cliente / Operaciones.
* Ejecutar herramienta: `etiquetar_ticket(categoría="Logística/Reembolsos")`.
* Respuesta al usuario: "Lamentamos el inconveniente con tu pedido. Hemos derivado tu caso a un especialista de operaciones que te contactará a la brevedad para gestionar una solución o reembolso."



## 3. Errores de Configuración / Capa 8 (Prioridad Media-Baja)

* **Condición:** El log demuestra que la plataforma funciona, pero expone parámetros mal configurados por el usuario o bloqueos por políticas de negocio (ej. cupones expirados, notificaciones apagadas).
* **Acción del Agente:**
* Resolución automática (Deflexión de Nivel 1). No escalar a humanos.
* Respuesta al usuario: Explicar la causa raíz directamente (ej. "Tu cupón expiró el día de ayer" o "Tienes las notificaciones de la tablet en silencio") y proveer los pasos para corregirlo.
* Cerrar el ticket automáticamente.



## 4. Falta de Información (Prioridad Baja - Bloqueado)

* **Condición:** El usuario reporta un problema transaccional u operativo, pero el ticket carece de identificadores clave (como el `order_id`) y el campo de logs está vacío, impidiendo el diagnóstico.
* **Acción del Agente:**
* Suspender la clasificación temporalmente. No escalar.
* Respuesta al usuario: "Para poder investigar tu caso y darte una solución rápida, necesitamos que nos indiques el número de pedido (ORD-XXXX) asociado a este inconveniente."
* Estado del ticket: Pendiente de respuesta del cliente.



## 5. Casos de Borde (Ruido y Reiteraciones)

* **Reiteraciones (Duplicados):** Si el agente extrae un `order_id` y detecta mediante la herramienta `buscar_tickets_abiertos()` que ya existe un reclamo en curso para ese pedido.
* Acción: Ejecutar herramienta `merge_tickets()`. Responder al usuario confirmando que su nueva información fue añadida al caso original y cerrar el ticket nuevo.


* **Spam / Ruido:** Cadenas de texto sin sentido, pruebas o mensajes vacíos sin logs asociados.
* Acción: Etiquetar como "Inválido" y cerrar automáticamente sin respuesta al usuario.