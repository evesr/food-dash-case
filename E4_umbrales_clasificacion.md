

Para separar un bug técnico de un error de configuración o un problema operativo, mi enfoque no se basa solo en lo que el usuario declara en el ticket, sino en lo que realmente hizo el sistema según los logs. El objetivo es evaluar si el sistema intentó ejecutar una acción y falló por un problema de código, si bloqueó una acción porque estaba siguiendo una regla de negocio, o si los datos del sistema simplemente no cuadran con lo que pasó en el mundo real.

A continuación detallo las reglas y señales exactas para cada categoría:

#### 1. Bug Técnico

Un problema cae en esta categoría cuando los logs muestran que la aplicación o los servidores sufrieron una caída o un error inesperado.

* **Señal principal:** Encontrar excepciones de código o fallas de servidor en el campo de logs.
* **Reglas y palabras clave:** Busco términos como stacktrace, NullPointerException o js_error para identificar caídas de la aplicación. Para caídas de servidor o conexión, busco palabras como timeout o errores 500. También incluyo fallas lógicas graves, como cuando un log financiero muestra un cobro duplicado indicando que una llave de idempotencia fue reusada.
* **Defensa de este criterio:** Un sistema que bloquea a un usuario por una regla no tiene un bug. Un bug ocurre únicamente cuando el código se rompe, los servicios pierden conexión o la lógica financiera falla.

#### 2. Error de Configuración o de Usuario

Esto ocurre cuando los logs demuestran que el sistema hizo exactamente lo que debía hacer según sus reglas, pero el usuario se queja porque configuró algo mal o intentó algo no permitido.

* **Señal principal:** El sistema deniega la acción mostrando un motivo claro o registra configuraciones que contradicen directamente el reclamo del ticket.
* **Reglas y palabras clave:** Busco resultados como BLOCKED o REJECTED junto a un motivo claro como expired o una política específica de cancelación. También reviso variables de estado del usuario, como un parámetro published marcado como FALSE o un volumen de notificaciones en OFF.
* **Defensa de este criterio:** Si un log dice que algo fue bloqueado por una política de negocio, el software está funcionando a la perfección. Escalar este tipo de tickets a ingeniería no tiene sentido, ya que la solución pasa netamente por guiar al usuario para que cambie su configuración.

#### 3. Problema de Efectividad u Operación

Este caso requiere cruzar lo que dice el cliente con los logs. Aquí el sistema y el código no fallan, lo que falló fue la logística en la calle.

* **Señal principal:** Encontrar métricas operativas en los logs sobre ubicaciones GPS, tiempos o cantidad de repartidores que expliquen por qué el pedido salió mal.
* **Reglas y palabras clave:** Busco anomalías logísticas, como una distancia muy alta al momento de marcar una entrega, o un nivel de confianza bajo al buscar una dirección en el mapa. También reviso si el tiempo real de entrega superó por mucho al tiempo prometido, o si hay muy pocos repartidores activos para la cantidad de pedidos abiertos en una zona.
* **Defensa de este criterio:** En estos casos, la plataforma digital solo actuó como un registro de un problema físico. La solución no es un parche de código, sino que una persona de soporte intervenga de inmediato para gestionar un reembolso o contactar al repartidor.