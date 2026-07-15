# Entregable 1: Mi Criterio

## Enfoque general y priorización

El abordaje del problema parte de la base de que el cuello de botella actual de la operación no radica en la resolución final del ticket, sino en la etapa de triage o clasificación inicial. Por esto, se optó por diseñar una arquitectura de decisión ágil, basada en un único agente enrutador con instrucciones estrictas. Se priorizó la velocidad de implementación, la eficiencia computacional minimizando llamadas al modelo, y la resolución automática exclusiva para errores de configuración. Estos casos suelen generar un alto volumen operativo, pero no requieren un análisis técnico avanzado ni intervención humana.

## Suposiciones

* Prevalencia de la telemetría: En caso de discrepancia entre la queja del usuario y el registro del sistema (por ejemplo, un reclamo de no entrega frente a un log con coordenadas GPS en el destino), el sistema utilizará la telemetría del log como la fuente de verdad definitiva para realizar la clasificación inicial.
* Estructura de datos estandarizada: Se asume que el campo de logs del sistema mantendrá una estructura base predecible que permita la extracción y evaluación de patrones de error o reglas de negocio, como timeouts, bloqueos operativos o excepciones nativas de código.

## Aspectos no considerados

* Resolución automática transaccional u operativa: Se excluyó de manera deliberada la capacidad del agente para procesar reembolsos financieros o modificar estados logísticos de los pedidos. Un sistema en esta fase de madurez no debe ejecutar acciones sobre pasarelas de pago o sobre la operación física en terreno sin supervisión.
* Arquitectura multi-agente: Aunque el contexto funcional permite la creación de un ecosistema de agentes especialistas, se descartó para esta iteración. Considerando el alcance y la muestra de datos, un sistema centralizado con uso de herramientas externas es suficiente para cumplir el objetivo, además de optimizar costos operativos y minimizar la probabilidad de alucinaciones.