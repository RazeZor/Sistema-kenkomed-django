# Manual de Usuario: Módulo de Pagos y Packs KenkoMed

El módulo de pagos de KenkoMed está diseñado con una premisa fundamental: **separar y mantener totalmente independientes el trabajo médico y el administrativo**. 

El profesional clínico (kinesiólogo, médico) **NUNCA** es bloqueado por el módulo de pagos. El clínico atiende al paciente en su box, completa su Ficha Clínica y avanza en el tratamiento con total libertad. El módulo de Pagos, de manera invisible y silenciosa, se encarga de rastrear contablemente esas sesiones y asistir a recepción (o a la administración de la clínica/consulta independiente) calculando la deuda en tiempo real. **Es una herramienta de ayuda financiera, no un bloqueador clínico.**

---

## 1. El Concepto Principal: El Motor de Cruce Automático

La magia del sistema radica en cómo calcula la deuda de manera pasiva. El sistema actúa como un contador invisible que cruza dos mundos independientes:
> *"¿Cuántas sesiones clínicas tiene registradas el paciente en su ficha médica vs. Cuánto dinero ha entrado a la caja a nombre de este paciente?"*

El estado financiero del paciente se clasifica en tres posibles escenarios:
1. **Deuda Pendiente (Rojo):** Si hay más sesiones clínicas registradas que dinero pagado (Ej: 5 atenciones médicas, pero solo 3 pagos registrados).
2. **Saldo a Favor (Verde):** Si hay más dinero ingresado a la caja que sesiones médicas (Ej: El paciente hizo un abono extra, o pagó algo por adelantado sin comprar un pack).
3. **Al Día (Verde):** Si el dinero ingresado cuadra perfectamente con las sesiones realizadas.

---

## 2. Los 3 Escenarios de Cobro (Cómo usar el sistema)

### Escenario A: El paciente abona parcialmente o paga sesión a sesión (Día a Día)
El paciente llega a la clínica, se atiende, y al salir pasa por la caja a pagar. A veces paga la sesión completa, a veces deja un "abono parcial".
1. El clínico hace la atención médica. El sistema registra internamente el valor de esa sesión (basado en el Precio Default de la clínica).
2. En la sección de Pagos, aparecerá la deuda total acumulada.
3. El administrativo hace clic en **Saldar Deuda**.
4. **Novedad - Abonos Parciales:** Se abre un modal donde el sistema sugiere pagar el total de la deuda, pero **este monto es editable**. Si el paciente solo puede pagar la mitad, se escribe ese monto parcial.
5. El sistema registra el "Abono", rebaja la deuda total matemáticamente y mantiene la alerta de deuda por el remanente. Todo automáticamente.

### Escenario B: El paciente paga todo al FINAL (Pago Masivo / Saldar Deuda)
El paciente se atiende durante 2 semanas (ej: 5 sesiones) sin pagar nada. Al final del tratamiento, quiere pagar todo junto.
1. El clínico hace las 5 atenciones en distintos días. La alerta contable indicará la suma total de las 5 atenciones como deuda.
2. El último día, el administrativo entra al perfil del paciente y hace clic en el botón verde **Saldar deuda ($ Monto Total)**.
3. Se abre el modal con el total sugerido (ej: $100.000). Elige si pagó con Tarjeta o Efectivo, y confirma.
4. **Inteligencia de Abonos Libres:** Si por alguna razón el usuario ingresa un pago superior a la deuda (ej: pagó $120.000), el sistema saldará todas las sesiones y dejará los $20.000 restantes como un **Saldo a favor**. Cuando el paciente vuelva a atenderse, su próxima sesión se cobrará automáticamente de ese saldo a favor sin intervención humana.

### Escenario C: El paciente paga por ADELANTADO (Packs de Atención Flexibles)
El paciente llega el primer día y quiere comprar una promoción de "10 sesiones por $200.000". Aquí destaca la flexibilidad del sistema para descontar sesiones "en el aire".
1. **La Venta:** Antes de que el paciente siquiera vea al médico, se entra a **Nuevo Pack**. Se pone nombre "Pack 10", se ingresa el precio y se **elige el Medio de Pago**. El dinero entra a la caja inmediatamente y queda contablemente justificado.
2. **El Descuento por Adelantado:** Como el paciente se atiende hoy con el pack, la secretaria le da al botón **Descontar 1** *inmediatamente*, sin necesidad de esperar a que el clínico escriba la ficha médica. El pack baja a 9 sesiones y queda un "crédito" a favor.
3. **El Cruce Mágico:** Horas o días después, cuando el clínico registre su evolución médica, el sistema verá que se creó una sesión clínica nueva, pero como detecta el descuento hecho previamente por la secretaria, **no generará deuda**. Se enlazan automáticamente.

---

## 3. Corrección de Errores y Trazabilidad

En el trabajo diario de la clínica, ocurren errores. El sistema está preparado para no perder el rastro del dinero:

- **Editar un Pago (✏️):** Si se registró un pago como Efectivo pero en realidad era Tarjeta, se puede usar el botón de editar. Cambiará el registro sin afectar la deuda.
- **Anular un Pago (Soft Delete):** Si hubo una boleta mal emitida y requiere anulación, se puede "Anular" el pago. El pago seguirá apareciendo en el historial (tachado por transparencia contable), pero el dinero se restará de la caja y **la deuda del paciente volverá a subir automáticamente**.
- **Eliminar Físicamente (🗑️ Hard Delete):** Si fue un error de tipeo grave y no debe quedar registro. 
  - *Inteligencia del sistema:* Si se elimina físicamente un pago que se había descontado de un **Pack**, el sistema es inteligente y le devuelve la sesión al saldo disponible del Pack para que el paciente no pierda su sesión.

---

## 4. El Dashboard General (Panel de Control Financiero)

Para el Administrador o Dueño de la clínica (o el profesional independiente que lleva sus números), el **Dashboard de Pagos** ofrece la vista de "Águila":
- **Ingresos del Mes:** Suma de todo el dinero real que ha entrado, limpio de anulaciones.
- **Bonos Pendientes:** Cantidad de pagos que se marcaron como "Bono por llegar" (para saber cuánta plata se le debe cobrar a Fonasa o Isapres).
- **Alerta de Deudores:** Una tabla gigante con todos los pacientes de la clínica que registran Deuda o Sesiones sin pagar. El administrador puede revisar esa tabla una vez por semana y con 1 clic "Saldar Deuda" a cada uno o registrar abonos sin ir perfil por perfil.
