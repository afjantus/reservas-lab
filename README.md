

# Especificación

# Problema

La coordinación de un laboratorio registra las reservas mediante mensajes y una planilla. Esto puede generar confusiones, como reservar la misma unidad en horarios que se superponen o que una reserva cancelada siga ocupando un horario. Se necesita un sistema sencillo que permita consultar la disponibilidad, crear y cancelar reservas sin perder el historial.

# Alcance

El sistema permitirá:

- Consultar la disponibilidad de una unidad para un día y horario determinados.
- Crear reservas indicando la unidad, el nombre del solicitante, la fecha y hora de inicio y la fecha y hora de fin.
- Cancelar reservas sin eliminar sus datos, dejando el horario disponible para una nueva reserva.
- Guardar las reservas y sus estados para recuperarlos al cerrar y volver a iniciar la aplicación.

El inventario de unidades ya está definido y se cargará inicialmente. No será necesario agregar, modificar ni eliminar unidades desde el sistema.

# Reglas

- Cada reserva tendrá un identificador propio y un estado que indique si está activa o cancelada.
- Una reserva activa ocupa el horario indicado. Una reserva cancelada deja de bloquearlo.
- No se podrán crear dos reservas activas de la misma unidad si sus horarios se superponen.
- Se permitirán reservas consecutivas. Por ejemplo, si una reserva termina a las 11:00, otra podrá comenzar a esa misma hora.
- Se podrán reservar unidades distintas en el mismo horario.
- Para crear una reserva, la unidad debe existir, el nombre del solicitante no puede estar vacío ni contener solamente espacios y las fechas y horas deben ser válidas.
- La fecha y hora de inicio deben ser anteriores a las de finalización.
- La consulta de disponibilidad deberá respetar las mismas reglas que la creación de reservas, para evitar que se informe como disponible un horario que no se puede reservar.
- Al cancelar una reserva, se conservarán su identificador y sus datos originales, y solo cambiará su estado.

# Supuestos

- Se utilizará la zona horaria de Argentina (America/Argentina/Buenos_Aires).
- Las fechas y horas se ingresarán en el formato `YYYY-MM-DD HH:MM`, por ejemplo, `2026-10-26 10:00`.
- No se establecerán restricciones adicionales para las reservas con fechas pasadas ni para su duración, siempre que se cumplan las demás reglas.
- El sistema utilizará las siguientes unidades precargadas: MIC-01, MIC-02, OSC-01, MUL-01 y FUE-01.
- Los datos se guardarán en un almacenamiento local que permita recuperarlos al reiniciar la aplicación.

# Criterios de aceptación

- CA1 - Rechazar horarios superpuestos: si MIC-01 tiene una reserva activa de 10:00 a 11:00, el sistema debe rechazar otra reserva de 10:30 a 11:30 para esa misma unidad.
- CA2 - Permitir reservas consecutivas: si MIC-01 tiene una reserva activa de 10:00 a 11:00, el sistema debe permitir otra de 11:00 a 12:00.
- CA3 - Permitir unidades distintas: si MIC-01 está reservada de 10:00 a 11:00, el sistema debe permitir una reserva de MIC-02 en ese mismo horario.
- CA4 - Cancelar sin perder el historial: al cancelar una reserva, el sistema debe conservar su identificador y sus datos, cambiar su estado a cancelada y liberar el horario.
- CA5 - Conservar los datos al reiniciar: después de cerrar y volver a iniciar la aplicación, las reservas activas y canceladas deben seguir disponibles.
- CA6 - Validar los datos ingresados: el sistema debe rechazar reservas con unidades inexistentes, nombres vacíos, fechas u horas inválidas o una fecha de inicio igual o posterior a la de finalización, mostrando un mensaje claro sobre el error.
- CA7 - Consultar disponibilidad correctamente: el sistema debe informar si una unidad está disponible para el horario solicitado, teniendo en cuenta las reservas activas y las reglas de superposición.