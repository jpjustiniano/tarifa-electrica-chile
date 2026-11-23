# Calculadora CLI de Tarifas Eléctricas en Baja Tensión y NetBilling (Chile)

Herramienta de línea de comandos para calcular el **gasto mensual en electricidad** y la **liquidación de inyección de excedentes** (NetBilling - Ley 20.571) para clientes regulados en **Baja Tensión**.

---

## 1. Características Principales

* **Autocompletado Interactivo en Tiempo Real**: Al seleccionar la comuna, el usuario puede comenzar a escribir letras y presionar la tecla **`TAB`** para autocompletar automáticamente el nombre o alternar entre sugerencias coincidentes en vivo en la consola.
* **Actualización Automática por Internet**: Si en el mes en que se ejecuta no se cuenta con los precios vigentes de ese mes o posteriores, el programa se conecta a la web de CGE/CNE, rastrea el pliego oficial más reciente publicado, descarga el PDF y actualiza automáticamente la base de datos de precios.
* **Base de datos real integrada**: Incluye las **171 comunas/zonas** del pliego oficial de CGE (incluyendo sus filiales CONAFE, EMELAT, ELECDA, ELIQSA y EMELARI, desde Arica hasta La Araucanía), además de referencias para Enel RM y Chilquinta (173 zonas en total).
* **Cobertura completa de opciones en Baja Tensión ($\le 400\text{ V}$)**:
  * **BT1**: Residencial y pequeños comercios (medición solo energía kWh, con cálculo de recargo por límite de invierno).
  * **BT2**: Comercial y alumbrado público (energía + potencia contratada fija).
  * **BT3**: Pymes y comercios (energía + demanda máxima leída en el mes).
  * **BT4.1**: Horaria (energía + potencia contratada en punta + contratada fuera de punta).
  * **BT4.2**: Horaria (energía + demanda máxima leída en punta + contratada fuera de punta).
  * **BT4.3**: Horaria (energía + demanda máxima leída en punta + demanda suministrada general).
* **Cálculo de Inyección / NetBilling**: Valora los excedentes inyectados a la red al precio de nudo de la energía fijado por ley para la comuna (sin IVA), calculando el abono y el saldo final neto.

---

## 2. Instrucciones de Uso

### Modo Interactivo (Paso a paso)
Simplemente ejecuta:
```bash
python calculadora_tarifas_bt.py
```
o en Windows:
```powershell
py calculadora_tarifas_bt.py
```
El asistente te guiará preguntando:
1. Comuna o zona (con opción de búsqueda en lista de 120+ comunas o personalización).
2. Opción tarifaria (BT1 a BT4.3).
3. Variables específicas según la tarifa seleccionada (Consumo en kWh, potencias en kW, mes/invierno si es BT1 e inyección en kWh).

---

### Modo Rápido / Automatizado (Argumentos de Línea de Comandos)

Puedes pasar los parámetros directamente como flags:

#### Ejemplo 1: Cliente Residencial BT1 en Buin con autogeneración solar
```powershell
py calculadora_tarifas_bt.py --zona Buin --tarifa BT1 --consumo 280 --inyeccion 60 --mes 10
```

#### Ejemplo 2: Comercio BT3 en Santiago Centro (Enel RM) con demanda máxima leída
```powershell
py calculadora_tarifas_bt.py --zona "Santiago (Enel RM)" --tarifa BT3 --consumo 750 --potencia 12 --inyeccion 150
```

#### Ejemplo 3: Industria pequeña en BT4.3 con control de horario punta
```powershell
py calculadora_tarifas_bt.py --zona Concepcion --tarifa BT4.3 --consumo 1800 --potencia-punta 8.5 --potencia-fuera 18.0 --inyeccion 400
```

---

## 3. Parámetros Disponibles

| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `--zona` | Texto | Nombre de la comuna o zona (ej. `Buin`, `Santiago (Enel RM)`, `Concepcion`). |
| `--tarifa` | Código | Opción tarifaria: `BT1`, `BT2`, `BT3`, `BT4.1`, `BT4.2`, `BT4.3`. |
| `--consumo` | Número | Consumo total del mes en kWh. |
| `--inyeccion` | Número | Excedentes inyectados a la red en kWh (NetBilling). Default: 0. |
| `--mes` | 1 - 12 | Mes de facturación (para calcular límite de invierno en BT1). Default: 10. |
| `--limite-invierno` | Número | Límite de invierno en kWh para BT1 (si aplica). |
| `--potencia` | Número | Potencia contratada o demanda máxima en kW (para BT2 y BT3). |
| `--potencia-punta` | Número | Potencia registrada/contratada en horas punta en kW (para BT4). |
| `--potencia-fuera` | Número | Potencia registrada/contratada fuera de punta o suministrada en kW (para BT4). |
| `--actualizar` | Flag | Fuerza la conexión a internet para verificar y descargar el último pliego oficial disponible. |
