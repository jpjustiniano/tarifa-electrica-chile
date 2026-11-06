# Guía Completa: Fijación de Precios de la Tarifa Eléctrica en Chile (Baja y Alta Tensión)

Este documento sintetiza la normativa legal, los procesos de fijación técnica de la **Comisión Nacional de Energía (CNE)** y la aplicación comercial de empresas distribuidoras como **CGE** y **Enel Distribución Chile**.

---

## 1. Marco Institucional y Legal

En Chile, el sector eléctrico se rige principalmente por:
* **DFL N° 4/2006 (Ley General de Servicios Eléctricos - LGSE):** Establece el principio rector de que las tarifas deben reflejar los **costos reales y eficientes** de generación, transporte y distribución.
* **Comisión Nacional de Energía (CNE):** Organismo técnico encargado de calcular y diseñar las fórmulas tarifarias, precios de nudo, valor agregado de distribución y emitir los informes técnicos.
* **Ministerio de Energía:** Emite formalmente los Decretos Tarifarios (publicados en el Diario Oficial) tras la toma de razón de Contraloría.
* **Superintendencia de Electricidad y Combustibles (SEC):** Fiscaliza el cumplimiento de cobros, calidad y continuidad del suministro.
* **Empresas Distribuidoras (Enel, CGE, Chilquinta, Saesa, etc.):** Concesionarias obligadas a suministrar energía a precios regulados a los usuarios dentro de sus zonas de concesión.

---

## 2. Tipos de Clientes: Regulados vs. Libres

La ley distingue a los consumidores según su potencia conectada:
1. **Clientes Regulados ($\le 5.000\text{ kW}$):**
   * Hogares, comercios, talleres y pequeñas/medianas industrias.
   * Sujetos a precios máximos fijados por ley.
   * Aquellos con potencia entre **500 kW y 5.000 kW** tienen la facultad legal de **elegir** entre régimen regulado o libre (compromiso mínimo por 4 años).
2. **Clientes Libres ($> 5.000\text{ kW}$):**
   * Grandes industrias y mineras.
   * Negocian libremente sus precios y condiciones de suministro con generadores o comercializadores.

---

## 3. Descomposición del Precio a Usuario Final

El precio final que paga un cliente regulado en su boleta o factura se compone de:

$$\text{Precio Final} = \text{Precio de Nudo (Generación)} + \text{Transmisión} + \text{VAD (Distribución)} + \text{Cargos Normativos}$$

### A. Generación (~65% - 70% de la cuenta)
* **Precio de Nudo Promedio (PNP):** Representa el costo eficiente de producir la electricidad en las centrales. Se calcula a partir de las licitaciones públicas de suministro a largo plazo contratadas por las distribuidoras con empresas generadoras.
* Contiene dos elementos: **Precio de la Energía ($/kWh)** y **Precio de la Potencia de Punta ($/kW/mes)**.
* Se actualiza semestralmente (o según decretos tarifarios).

### B. Transmisión (~7% - 10% de la cuenta)
* **Cargo por Uso del Sistema de Transmisión (Troncal y Zonal):** Remunera las líneas de alta tensión que transportan la energía desde las plantas generadoras hasta las subestaciones de distribución.

### C. Valor Agregado de Distribución - VAD (~20% - 25% de la cuenta)
* Costo de transportar la electricidad desde las subestaciones primarias hasta el medidor del cliente a través de postes, transformadores y redes locales.
* Se fija cada 4 años mediante un riguroso estudio de una **empresa modelo eficiente** (procesos cuadrienales como Decreto 11T / Decreto 5T).
* Incluye:
  * Costos de inversión y reposición de instalaciones.
  * Gastos de operación, mantenimiento y pérdidas técnicas y no técnicas eficientes.
  * Costos comerciales: lectura de medidores, emisión de boletas, facturación, reparto y atención a clientes.

### D. Cargos Normativos y Estabilización
* **Cargo por Servicio Público:** Financiamiento de paneles de expertos y organismos del sector.
* **Mecanismos de Estabilización y FET (Leyes 21.185, 21.472 y 21.667):** Mecanismos creados para amortiguar y descongelar gradualmente las variaciones del tipo de cambio y precios internacionales de energía tras 2019, incluyendo el Fondo de Estabilización de Tarifas y subsidios para usuarios vulnerables.

---

## 4. Clasificación por Nivel de Tensión: Baja Tensión (BT) vs. Alta Tensión (AT)

* **Baja Tensión (BT):** Conexión con empalme a redes con tensión nominal **igual o inferior a 400 Volts** (220V monofásico o 380V trifásico).
* **Alta Tensión (AT / Media Tensión en redes de distribución):** Conexión con empalme a redes con tensión nominal **superior a 400 Volts** (típicamente 12 kV, 13.2 kV, 23 kV).
  * *Efecto económico:* Los clientes en AT tienen transformador propio o reciben directamente en media tensión; por ello, **no pagan el componente de VAD asociado a la red de baja tensión**, lo que resulta en costos unitarios por kWh y kW significativamente más bajos.

---

## 5. Catálogo Detallado de Opciones Tarifarias

Los clientes pueden elegir libremente su opción tarifaria según su patrón de consumo, con una permanencia mínima de **12 meses**.

### Opciones en Baja Tensión (BT)

| Tarifa | Tipo de Cliente | Modalidad de Medición | Conceptos Cobrados en Factura |
| :--- | :--- | :--- | :--- |
| **BT1** | Residencial y pequeños comercios ($\le 10\text{ kW}$) | Solo energía (kWh) con medidor simple unidireccional | • Cargo Fijo Mensual ($/mes)<br>• Cargo por Energía ($/kWh, que incluye generación, transmisión y potencia implícita)<br>• Límite de invierno (recargo por sobreconsumo en meses fríos si supera 350-430 kWh y promedio del verano). |
| **BT2** | Comercial, alumbrado público, talleres | Medición de energía + Potencia contratada fija | • Cargo Fijo Mensual<br>• Cargo por Energía ($/kWh)<br>• Cargo por Potencia Contratada ($/kW/mes) que se abona mes a mes todo el año. |
| **BT3** | Pymes, comercios con consumo variable | Medición de energía + Demanda máxima leída | • Cargo Fijo Mensual<br>• Cargo por Energía ($/kWh)<br>• Cargo por Potencia Máxima Leída (kW) registrada por el medidor en el mes. |
| **BT4.1** | Clientes comerciales/industriales con gestión horaria | Medición de energía + Contratación de potencia en punta y horas normales | • Cargo Fijo Mensual<br>• Cargo por Energía ($/kWh)<br>• Cargo por Potencia Contratada en Horas de Punta<br>• Cargo por Potencia Contratada Parcialmente en Punta. |
| **BT4.2** | Clientes medianos con control de horario punta | Medición de energía + Demanda máxima leída en punta + Contratada fuera de punta | • Cargo Fijo Mensual<br>• Cargo por Energía ($/kWh)<br>• Cargo por Potencia Leída en Horas Punta<br>• Cargo por Potencia Contratada Total. |
| **BT4.3** | Industrias/comercios con capacidad de deslastre o acumulación | Medición total horaria (energía, peak en punta y peak total leídos) | • Cargo Fijo Mensual<br>• Cargo por Energía ($/kWh)<br>• Cargo por Potencia Leída en Horas Punta ($/kW/mes)<br>• Cargo por Demanda Máxima Suministrada fuera de punta ($/kW/mes). |

### Opciones en Alta Tensión (AT)

Poseen la misma estructura lógica que las opciones BT, pero aplicadas a clientes conectados sobre 400V:
* **AT2:** Medición de energía y potencia contratada en alta tensión.
* **AT3:** Medición de energía y demanda máxima leída en alta tensión.
* **AT4.1:** Medición de energía y potencias contratadas (punta y fuera de punta).
* **AT4.2:** Medición de potencia en horas punta y potencia contratada fuera de punta.
* **AT4.3:** Medición completa tanto de potencia en horas punta como de potencia máxima suministrada.

*(Nota técnica: No existe opción AT1, dado que los consumos menores sin medición de potencia se canalizan exclusivamente por baja tensión).*

---

## 6. Conceptos Clave de Facturación (Enel y CGE)

1. **Horas de Punta (HP):**
   * Tradicionalmente definidas entre las **18:00 y las 22:00 horas** (o 18:00 a 23:00 según decreto) durante los meses de invierno (mayo a septiembre, con variaciones según la zona geográfica).
   * En este horario el sistema eléctrico nacional se encuentra en su máxima demanda. Por ende, la potencia registrada en este bloque tiene un costo muy superior ($/kW/mes) para incentivar el ahorro o desplazamiento de cargas.
2. **Cargo Fijo Mensual:**
   * Es independiente del consumo. Cubre la lectura, emisión de boletas, cobranza y atención al cliente. Se factura aunque el consumo del mes sea 0 kWh.
3. **Arriendo de Medidor:**
   * Si el equipo de medición pertenece a la distribuidora, se cobra un canon mensual fijado por el Decreto de Servicios No Consistentes en Suministro.
4. **Inyección de Excedentes (NetBilling - Ley 20.571):**
   * Usuarios residenciales o empresas con paneles solares pueden inyectar excedentes a la red, los cuales son valorizados al precio de nudo de la energía y descontados de su facturación mensual.
