#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Tarifas Eléctricas en Baja Tensión (BT) y NetBilling (Inyección de Energía) - Chile
Permite calcular el gasto mensual en suministro y el abono por inyección solar o autogeneración
para clientes regulados en Baja Tensión (BT1, BT2, BT3, BT4.1, BT4.2, BT4.3).
"""

import sys
import os

# Auto-despacho al entorno virtual .venv si existe y no está activo
_VENV_PY = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
if os.path.exists(_VENV_PY):
    _curr_py = os.path.abspath(sys.executable).lower()
    _target_py = os.path.abspath(_VENV_PY).lower()
    if _curr_py != _target_py and not os.environ.get("_ANTIGRAVITY_VENV_ACTIVE"):
        import subprocess
        _env = os.environ.copy()
        _env["_ANTIGRAVITY_VENV_ACTIVE"] = "1"
        sys.exit(subprocess.call([_VENV_PY] + sys.argv, env=_env))

import json
import argparse
from typing import Dict, Any, Optional, List

# Configurar salida UTF-8 para consola en Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Importar prompt_toolkit para autocompletado profesional de terminal y captura de tecla Esc
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style as PtStyle
    PT_DISPONIBLE = True
except ImportError:
    PT_DISPONIBLE = False

class SalidaSolicitada(Exception):
    """Excepción interna para cerrar el programa limpiamente al presionar Esc o escribir salir."""
    pass

def cerrar_programa():
    """Muestra mensaje de despedida y termina la ejecución con código 0."""
    print("\n" + "="*70)
    print(" [!] Programa finalizado por el usuario (Esc / Salir). ¡Hasta pronto!")
    print("="*70 + "\n")
    sys.exit(0)

COMANDOS_SALIDA = {"salir", "exit", "quit", "q", "esc"}

from datetime import datetime
from actualizador_tarifas import asegurar_tarifas_al_dia, obtener_metadatos_locales

DB_FILE = os.path.join(os.path.dirname(__file__), "informacion_tarifas", "datos_tarifarios_bt.json")

# Valores promedio de referencia por defecto si no se encuentra la comuna
DEFAULT_TARIFAS = {
    "empresa": "Referencia Nacional (CNE / Regulado)",
    "cargo_fijo_bt1": 1150.0,
    "transmision": 29.50,
    "serv_publico": 0.855,
    "energia_bt1": 155.00,
    "potencia_punta_bt2_bt3": 25500.0,
    "potencia_fuera_punta_bt2_bt3": 17500.0,
    "cargo_fijo_bt4": 1150.0,
    "potencia_punta_bt4": 20200.0,
    "potencia_demanda_bt4": 5250.0,
    "inyeccion_bt": 103.50
}

def cargar_base_datos(mes_objetivo: Optional[int] = None, anio_objetivo: Optional[int] = None, forzar: bool = False) -> Dict[str, Any]:
    """Carga los datos locales o se conecta a internet para descargar la última versión si hace falta."""
    try:
        return asegurar_tarifas_al_dia(mes_objetivo=mes_objetivo, anio_objetivo=anio_objetivo, forzar=forzar)
    except Exception as e:
        print(f"[!] Advertencia al verificar tarifas ({e}).")
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

def formatear_clp(monto: float) -> str:
    """Formatea un número decimal a formato moneda chilena ($ X.XXX)."""
    return f"${round(monto):,}".replace(",", ".")

def leer_entrada_usuario(prompt_text: str, default: str = "", completer=None) -> str:
    """
    Lee una entrada de texto en consola.
    - Al presionar la tecla 'Esc' (o Ctrl+Q / Ctrl+C), cierra inmediatamente el programa.
    - Al escribir 'salir', 'exit', 'q' o 'esc', cierra inmediatamente el programa.
    """
    if sys.stdin.isatty() and PT_DISPONIBLE:
        try:
            kb = KeyBindings()

            @kb.add('escape')
            def _salir_esc(event):
                event.app.exit(exception=SalidaSolicitada())

            @kb.add('c-q')
            def _salir_ctrl_q(event):
                event.app.exit(exception=SalidaSolicitada())

            estilo = PtStyle.from_dict({
                'completion-menu.completion': 'bg:#2c3e50 #ecf0f1',
                'completion-menu.completion.current': 'bg:#2980b9 #ffffff bold',
                'scrollbar.background': 'bg:#7f8c8d',
                'scrollbar.button': 'bg:#34495e',
                'prompt': '#27ae60 bold',
            })

            session = PromptSession(key_bindings=kb)
            session.app.ttimeoutlen = 0.05  # Respuesta inmediata al presionar Esc (50 ms)

            texto = session.prompt(
                prompt_text,
                completer=completer,
                complete_while_typing=bool(completer),
                style=estilo,
                default=default
            ).strip()

            if texto.lower() in COMANDOS_SALIDA:
                cerrar_programa()
            return texto if texto else default

        except (SalidaSolicitada, KeyboardInterrupt, EOFError):
            cerrar_programa()
        except Exception:
            # Si el entorno no soporta búfer de consola Win32, continúa al modo estándar
            pass

    # Modo estándar / Pipe
    try:
        texto = input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        cerrar_programa()

    if texto.lower() in COMANDOS_SALIDA:
        cerrar_programa()
    return texto if texto else default

def pedir_float(mensaje: str, default: Optional[float] = None, minimo: float = 0.0) -> float:
    while True:
        prompt = f"{mensaje} "
        default_str = str(default) if default is not None else ""
        if default is not None:
            prompt += f"[{default}]: "
        else:
            prompt += ": "
        try:
            val_str = leer_entrada_usuario(prompt, default="")
            if not val_str and default is not None:
                return default
            val = float(val_str.replace(",", "."))
            if val < minimo:
                print(f"  [!] El valor debe ser mayor o igual a {minimo}.")
                continue
            return val
        except ValueError:
            print("  [!] Por favor ingrese un número válido (o presione 'Esc' / escriba 'salir' para cerrar).")

def pedir_int(mensaje: str, default: Optional[int] = None, minimo: int = 1, maximo: int = 12, permitir_cero_salir: bool = False) -> int:
    while True:
        prompt = f"{mensaje} "
        if default is not None:
            prompt += f"[{default}]: "
        else:
            prompt += ": "
        try:
            val_str = leer_entrada_usuario(prompt, default="")
            if not val_str and default is not None:
                return default
            val = int(val_str)
            if permitir_cero_salir and val == 0:
                cerrar_programa()
            if val < minimo or val > maximo:
                print(f"  [!] El valor debe estar entre {minimo} y {maximo}.")
                continue
            return val
        except ValueError:
            print("  [!] Por favor ingrese un número entero válido (o presione 'Esc' / escriba 'salir' para cerrar).")

def input_con_autocompletado(opciones: List[str], prompt_text: str = "Comuna: ", default: str = "") -> str:
    """
    Solicita entrada de texto con autocompletado profesional interactivo en tiempo real (TAB y menú desplegable)
    y salida rápida con la tecla 'Esc' o escribiendo 'salir'/'q'.
    """
    completer = None
    if PT_DISPONIBLE and sys.stdin.isatty():
        completer = FuzzyCompleter(WordCompleter(opciones, ignore_case=True, match_middle=True))
        print("\n  [Tip: Escriba letras para autocompletar con TAB/Flechas | Presione 'Esc' o escriba 'salir' para cerrar]")

    resp = leer_entrada_usuario(prompt_text, default=default, completer=completer)
    if not resp and default:
        return default
    for opc in opciones:
        if opc.lower() == resp.lower():
            return opc
    inician = [o for o in opciones if o.lower().startswith(resp.lower())]
    if inician:
        return inician[0]
    contienen = [o for o in opciones if resp.lower() in o.lower()]
    if contienen:
        return contienen[0]
    return resp or default

def seleccionar_zona(db: Dict[str, Any], zona_arg: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    vigencia = db.get("_metadata", {}).get("vigencia_texto", "Octubre 2026")
    def enriquecer(p: Dict[str, Any]) -> Dict[str, Any]:
        res = dict(p)
        res["vigencia_texto"] = vigencia
        return res

    if zona_arg:
        # Búsqueda insensible a mayúsculas
        for k, v in db.items():
            if k == "_metadata": continue
            if k.lower() == zona_arg.lower():
                return k, enriquecer(v)
        # Búsqueda parcial
        for k, v in db.items():
            if k == "_metadata": continue
            if zona_arg.lower() in k.lower():
                return k, enriquecer(v)
        print(f"[!] Zona '{zona_arg}' no encontrada en la base de datos. Se usarán valores de referencia nacional.")
        return zona_arg, enriquecer(DEFAULT_TARIFAS)

    print("\n" + "="*70)
    print(" 1. SELECCIÓN DE ZONA / COMUNA")
    print("="*70)
    print("Escriba el nombre de su comuna (con autocompletado presione TAB) o elija una opción:")
    comunas_destacadas = [
        "Santiago (Enel RM)",
        "Buin",
        "Calera de Tango",
        "Valparaíso (Chilquinta)",
        "Rancagua",
        "Talca",
        "Chillán",
        "Concepción",
        "Temuco",
        "La Serena",
        "Buscar otra comuna con autocompletado en vivo (TAB)",
        "Ingresar zona personalizada"
    ]
    
    for idx, c in enumerate(comunas_destacadas, 1):
        print(f"  [{idx:2d}] {c}")
    print("  [ 0] Salir del programa (o presione 'Esc' / escriba 'salir')")

    todas_las_comunas = [k for k in sorted(db.keys()) if k != "_metadata"]
    # Poner las opciones destacadas al inicio de la lista de autocompletado
    lista_autocompletado = comunas_destacadas[:10] + [c for c in todas_las_comunas if c not in comunas_destacadas[:10]]

    entrada = input_con_autocompletado(
        lista_autocompletado,
        prompt_text="\nComuna o N° [1]: ",
        default="1"
    ).strip()

    # Si el usuario ingresó un número del menú
    if entrada.isdigit():
        num = int(entrada)
        if num == 0:
            cerrar_programa()
        elif 1 <= num <= 10:
            c_sel = comunas_destacadas[num - 1]
            if c_sel in db:
                return c_sel, enriquecer(db[c_sel])
            for k, v in db.items():
                if k == "_metadata": continue
                if c_sel.split()[0].lower() in k.lower():
                    return k, enriquecer(v)
            return c_sel, enriquecer(DEFAULT_TARIFAS)
        elif num == 11:
            print("\n  [Modo Autocompletado Activo - Escriba letras y presione TAB para autocompletar]")
            c_sel = input_con_autocompletado(todas_las_comunas, prompt_text="Comuna (TAB para autocompletar): ", default="Santiago (Enel RM)")
            if c_sel in db:
                return c_sel, enriquecer(db[c_sel])
            for k, v in db.items():
                if k == "_metadata": continue
                if c_sel.lower() in k.lower():
                    return k, enriquecer(v)
            return c_sel, enriquecer(DEFAULT_TARIFAS)
        elif num == 12:
            nombre = leer_entrada_usuario("Ingrese el nombre de su zona/comuna: ", default="Zona Personalizada")
            return nombre, enriquecer(DEFAULT_TARIFAS)

    # Si el usuario escribió directamente el nombre (o usó TAB)
    for k, v in db.items():
        if k == "_metadata": continue
        if k.lower() == entrada.lower():
            return k, enriquecer(v)
    for k, v in db.items():
        if k == "_metadata": continue
        if entrada.lower() in k.lower():
            return k, enriquecer(v)

    return entrada, enriquecer(DEFAULT_TARIFAS)

def seleccionar_tarifa(tarifa_arg: Optional[str] = None) -> str:
    tarifas_disponibles = {
        "1": ("BT1", "Residencial y pequeño comercio simple (potencia <= 10 kW, solo mide kWh)"),
        "2": ("BT2", "Comercial / Alumbrado (potencia contratada fija en kW)"),
        "3": ("BT3", "Pymes y comercios (demanda máxima de potencia leída en el mes)"),
        "4": ("BT4.1", "Horaria - Potencia contratada en horas punta y contratada fuera de punta"),
        "5": ("BT4.2", "Horaria - Demanda máxima leída en horas punta y contratada fuera de punta"),
        "6": ("BT4.3", "Horaria - Demanda máxima leída en horas punta y suministrada general")
    }

    if tarifa_arg:
        t_norm = tarifa_arg.upper().replace("-", "").replace(" ", "")
        for _, (cod, _) in tarifas_disponibles.items():
            if cod.upper() == t_norm or cod.upper().replace(".", "") == t_norm:
                return cod
        print(f"[!] Tarifa '{tarifa_arg}' no reconocida. Elija de la lista.")

    print("\n" + "="*70)
    print(" 2. SELECCIÓN DE OPCIÓN TARIFARIA EN BAJA TENSIÓN (BT)")
    print("="*70)
    for k, (cod, desc) in tarifas_disponibles.items():
        print(f"  [{k}] {cod:6s} : {desc}")
    print("  [0] Salir del programa (o presione 'Esc' / escriba 'salir')")
    
    opc = str(pedir_int("Seleccione la opción tarifaria", default=1, minimo=1, maximo=6, permitir_cero_salir=True))
    return tarifas_disponibles[opc][0]

def mostrar_precios_tarifa(zona_nombre: str, parametros: Dict[str, Any], tarifa: str):
    """Muestra en pantalla los precios unitarios de consumo e inyección para la comuna y tarifa elegidas."""
    empresa = parametros.get("empresa", "Distribuidora")
    sector = parametros.get("sector_tarifario", "")
    vigencia = parametros.get("vigencia_texto", "Octubre 2026")

    if tarifa == "BT1":
        cargo_fijo = parametros.get("cargo_fijo_bt1", 1150.0)
        energia_unit = parametros.get("energia_bt1", 155.00)
    elif tarifa == "BT2":
        cargo_fijo = parametros.get("cargo_fijo_bt2", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt2_bt3", parametros.get("energia_bt1", 155.00))
    elif tarifa == "BT3":
        cargo_fijo = parametros.get("cargo_fijo_bt3", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt2_bt3", parametros.get("energia_bt1", 155.00))
    else:
        cargo_fijo = parametros.get("cargo_fijo_bt4", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt4", parametros.get("energia_bt1", 155.00))

    transmision_unit = parametros.get("transmision", 29.50)
    serv_publico_unit = parametros.get("serv_publico", 0.855)
    inyeccion_base_sin_iva = parametros.get("inyeccion_bt", 103.50)
    inyeccion_unit_con_iva = inyeccion_base_sin_iva * 1.19
    total_kwh_variable = energia_unit + transmision_unit + serv_publico_unit

    sector_str = f" | Sector: {sector}" if sector else ""
    print("\n" + "-"*70)
    print(f" PRECIOS VIGENTES PARA: {zona_nombre.upper()} ({empresa}{sector_str})")
    print(f" Tarifa: {tarifa} | Vigencia: {vigencia} (Valores con IVA 19% incluido)")
    print("-"*70)
    print(" [A] Precios de Compra / Consumo de Energía (con IVA 19%):")
    print(f"   * Cargo Fijo Mensual                        : ${cargo_fijo:,.2f} /mes")
    print(f"   * Precio Compra de Energía (con IVA)        : ${energia_unit:,.3f} /kWh")
    print(f"   * Cargo por Uso del Sistema de Transmisión  : ${transmision_unit:,.3f} /kWh")
    print(f"   * Cargo por Servicio Público                : ${serv_publico_unit:,.3f} /kWh")
    print(f"   -> Costo Variable Total por kWh Consumido   : ${total_kwh_variable:,.3f} /kWh")

    if tarifa == "BT2":
        pot_fuera = parametros.get("potencia_fuera_punta_bt2_bt3", 17985.5)
        print(f"   * Cargo por Potencia Contratada (con IVA)   : ${pot_fuera:,.1f} /kW/mes")
    elif tarifa == "BT3":
        pot_punta = parametros.get("potencia_punta_bt2_bt3", 25744.3)
        print(f"   * Cargo por Demanda Máxima Leída (con IVA)  : ${pot_punta:,.1f} /kW/mes")
    elif tarifa in ["BT4.1", "BT4.2"]:
        pot_punta = parametros.get("potencia_punta_bt4", 20416.6)
        pot_fuera = parametros.get("potencia_demanda_bt4", 5327.7)
        print(f"   * Cargo por Potencia en Horas Punta (IVA)   : ${pot_punta:,.1f} /kW/mes")
        print(f"   * Cargo por Potencia Fuera de Punta (IVA)   : ${pot_fuera:,.1f} /kW/mes")
    elif tarifa == "BT4.3":
        pot_punta = parametros.get("potencia_punta_bt4", 20416.6)
        pot_sum = parametros.get("potencia_demanda_bt4", 5327.7)
        print(f"   * Cargo Demanda Leída Horas Punta (con IVA) : ${pot_punta:,.1f} /kW/mes")
        print(f"   * Cargo Demanda Máx. Suministrada (con IVA) : ${pot_sum:,.1f} /kW/mes")

    print("\n [B] Precio de Venta / Inyección de Energía (con IVA 19%):")
    print(f"   * Precio Venta / Inyección en BT (con IVA)  : ${inyeccion_unit_con_iva:,.3f} /kWh")
    print(f"     (Valor base pliego sin IVA: ${inyeccion_base_sin_iva:,.3f} /kWh)")
    print("-"*70)

def solicitar_variables(tarifa: str) -> Dict[str, float]:
    print("\n" + "="*70)
    print(f" 3. VARIABLES DE CONSUMO E INYECCIÓN - TARIFA {tarifa}")
    print("="*70)
    datos = {}
    
    # 1. Consumo de energía
    datos["consumo_kwh"] = pedir_float("Consumo total de energía del mes (kWh)", default=220.0, minimo=0.0)
    
    # Variables específicas por tarifa
    if tarifa == "BT1":
        print("\n  [Configuración de Invierno - Límite de Invierno]")
        mes_actual = datetime.now().month
        mes = pedir_int("Mes de facturación (1=Enero, ..., 12=Diciembre)", default=mes_actual, minimo=1, maximo=12)
        datos["mes"] = mes
        es_invierno = mes in [5, 6, 7, 8, 9] # Mayo a Septiembre
        datos["es_invierno"] = es_invierno
        
        if es_invierno and datos["consumo_kwh"] > 350.0:
            print("  -> El mes consultado corresponde al periodo de punta/invierno y el consumo supera 350 kWh.")
            limite = pedir_float("Límite de invierno asignado en su boleta (kWh)", default=350.0, minimo=350.0)
            datos["limite_invierno"] = limite
        else:
            datos["limite_invierno"] = 0.0

    elif tarifa == "BT2":
        datos["potencia_contratada_kw"] = pedir_float("Potencia contratada mensual (kW)", default=15.0, minimo=0.0)

    elif tarifa == "BT3":
        datos["demanda_maxima_kw"] = pedir_float("Demanda máxima leída registrada en el mes (kW)", default=12.0, minimo=0.0)

    elif tarifa == "BT4.1":
        datos["potencia_punta_kw"] = pedir_float("Potencia contratada en horas de punta (kW)", default=8.0, minimo=0.0)
        datos["potencia_fuera_punta_kw"] = pedir_float("Potencia contratada fuera de punta / total (kW)", default=15.0, minimo=0.0)

    elif tarifa == "BT4.2":
        datos["potencia_punta_kw"] = pedir_float("Demanda máxima leída en horas de punta (kW)", default=7.5, minimo=0.0)
        datos["potencia_fuera_punta_kw"] = pedir_float("Potencia contratada fuera de punta / total (kW)", default=15.0, minimo=0.0)

    elif tarifa == "BT4.3":
        datos["potencia_punta_kw"] = pedir_float("Demanda máxima leída en horas de punta (kW)", default=7.0, minimo=0.0)
        datos["potencia_suministrada_kw"] = pedir_float("Demanda máxima suministrada general (kW)", default=14.0, minimo=0.0)

    # Inyección de energía (NetBilling - Ley 20.571)
    print("\n  [Inyección de Energía / NetBilling - Autogeneración Solar]")
    datos["inyeccion_kwh"] = pedir_float("Energía inyectada a la red en el mes (kWh excedentes)", default=0.0, minimo=0.0)
    
    return datos

def calcular_facturacion(zona_nombre: str, parametros: Dict[str, Any], tarifa: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    consumo_kwh = variables.get("consumo_kwh", 0.0)
    inyeccion_kwh = variables.get("inyeccion_kwh", 0.0)
    
    # Parámetros tarifarios (con IVA 19% incluido)
    if tarifa == "BT1":
        cargo_fijo = parametros.get("cargo_fijo_bt1", 1150.0)
        energia_unit = parametros.get("energia_bt1", 155.00)
    elif tarifa == "BT2":
        cargo_fijo = parametros.get("cargo_fijo_bt2", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt2_bt3", parametros.get("energia_bt1", 155.00))
    elif tarifa == "BT3":
        cargo_fijo = parametros.get("cargo_fijo_bt3", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt2_bt3", parametros.get("energia_bt1", 155.00))
    else:
        cargo_fijo = parametros.get("cargo_fijo_bt4", parametros.get("cargo_fijo_bt1", 1150.0))
        energia_unit = parametros.get("energia_bt4", parametros.get("energia_bt1", 155.00))

    transmision_unit = parametros.get("transmision", 29.50)
    serv_publico_unit = parametros.get("serv_publico", 0.855)
    # Precio de venta / inyección de energía incluyendo IVA (19%)
    inyeccion_base_sin_iva = parametros.get("inyeccion_bt", 103.50)
    inyeccion_unit = inyeccion_base_sin_iva * 1.19
    
    # 1. Cargos de Energía y Transmisión
    costo_transmision = consumo_kwh * transmision_unit
    costo_serv_publico = consumo_kwh * serv_publico_unit
    
    costo_energia_base = 0.0
    costo_sobreconsumo_invierno = 0.0
    costo_potencia = 0.0
    detalle_potencia = ""
    
    if tarifa == "BT1":
        limite = variables.get("limite_invierno", 0.0)
        if variables.get("es_invierno", False) and limite > 0 and consumo_kwh > limite:
            kwh_base = limite
            kwh_exceso = consumo_kwh - limite
            costo_energia_base = kwh_base * energia_unit
            # El sobreconsumo de invierno tiene un recargo por potencia de punta implícita (~60% adicional)
            costo_sobreconsumo_invierno = kwh_exceso * (energia_unit * 1.55)
        else:
            costo_energia_base = consumo_kwh * energia_unit

    elif tarifa == "BT2":
        costo_energia_base = consumo_kwh * energia_unit
        p_contratada = variables.get("potencia_contratada_kw", 0.0)
        precio_pot = parametros.get("potencia_fuera_punta_bt2_bt3", 17985.5)
        costo_potencia = p_contratada * precio_pot
        detalle_potencia = f"Potencia contratada: {p_contratada:.2f} kW × {formatear_clp(precio_pot)}/kW"

    elif tarifa == "BT3":
        costo_energia_base = consumo_kwh * energia_unit
        p_leida = variables.get("demanda_maxima_kw", 0.0)
        precio_pot = parametros.get("potencia_punta_bt2_bt3", 25744.3)
        costo_potencia = p_leida * precio_pot
        detalle_potencia = f"Demanda máxima leída: {p_leida:.2f} kW × {formatear_clp(precio_pot)}/kW"

    elif tarifa in ["BT4.1", "BT4.2"]:
        cargo_fijo = parametros.get("cargo_fijo_bt4", cargo_fijo)
        costo_energia_base = consumo_kwh * energia_unit
        p_punta = variables.get("potencia_punta_kw", 0.0)
        p_fuera = variables.get("potencia_fuera_punta_kw", 0.0)
        precio_punta = parametros.get("potencia_punta_bt4", 20416.6)
        precio_fuera = parametros.get("potencia_demanda_bt4", 5327.7)
        costo_pot_punta = p_punta * precio_punta
        costo_pot_fuera = p_fuera * precio_fuera
        costo_potencia = costo_pot_punta + costo_pot_fuera
        detalle_potencia = (f"Punta ({p_punta:.2f} kW × {formatear_clp(precio_punta)}) + "
                            f"Fuera Punta ({p_fuera:.2f} kW × {formatear_clp(precio_fuera)})")

    elif tarifa == "BT4.3":
        cargo_fijo = parametros.get("cargo_fijo_bt4", cargo_fijo)
        costo_energia_base = consumo_kwh * energia_unit
        p_punta = variables.get("potencia_punta_kw", 0.0)
        p_sum = variables.get("potencia_suministrada_kw", 0.0)
        precio_punta = parametros.get("potencia_punta_bt4", 20416.6)
        precio_sum = parametros.get("potencia_demanda_bt4", 5327.7)
        costo_pot_punta = p_punta * precio_punta
        costo_pot_sum = p_sum * precio_sum
        costo_potencia = costo_pot_punta + costo_pot_sum
        detalle_potencia = (f"Punta ({p_punta:.2f} kW × {formatear_clp(precio_punta)}) + "
                            f"Suministrada ({p_sum:.2f} kW × {formatear_clp(precio_sum)})")

    # En los pliegos de tarifas chilenos los precios ya incluyen el 19% de IVA excepto el Cargo por Servicio Público
    # Total de gasto en suministro
    total_consumo = (cargo_fijo + costo_transmision + costo_serv_publico + 
                     costo_energia_base + costo_sobreconsumo_invierno + costo_potencia)

    # 2. Inyección / Venta de Energía (incluyendo IVA 19%)
    total_inyeccion = inyeccion_kwh * inyeccion_unit

    # 3. Balance Neto
    balance_neto = total_consumo - total_inyeccion

    # Metadatos de vigencia
    vigencia_texto = parametros.get("vigencia_texto")
    if not vigencia_texto:
        # Buscar en metadata general si está disponible
        meta = parametros.get("_metadata", {})
        vigencia_texto = meta.get("vigencia_texto", "Octubre 2026")

    return {
        "zona": zona_nombre,
        "empresa": parametros.get("empresa", "Distribuidora"),
        "vigencia_texto": vigencia_texto,
        "tarifa": tarifa,
        "consumo_kwh": consumo_kwh,
        "cargo_fijo": cargo_fijo,
        "costo_transmision": costo_transmision,
        "costo_serv_publico": costo_serv_publico,
        "costo_energia_base": costo_energia_base,
        "costo_sobreconsumo_invierno": costo_sobreconsumo_invierno,
        "costo_potencia": costo_potencia,
        "detalle_potencia": detalle_potencia,
        "total_consumo": total_consumo,
        "inyeccion_kwh": inyeccion_kwh,
        "precio_inyeccion_unit": inyeccion_unit,
        "precio_inyeccion_sin_iva": inyeccion_base_sin_iva,
        "total_inyeccion": total_inyeccion,
        "balance_neto": balance_neto
    }

def imprimir_reporte(res: Dict[str, Any]):
    print("\n" + "="*70)
    print("                RESULTADOS DEL BALANCE ELÉCTRICO MENSUAL")
    print("="*70)
    print(f" Zona / Comuna     : {res['zona']} ({res['empresa']})")
    print(f" Opción Tarifaria  : {res['tarifa']} (Baja Tensión)")
    if res.get('vigencia_texto'):
        print(f" Vigencia Precios  : {res['vigencia_texto']} (Pliego oficial CGE / CNE)")
    print(f" Consumo Facturado : {res['consumo_kwh']:.2f} kWh")
    if res['inyeccion_kwh'] > 0:
        print(f" Inyección Solar   : {res['inyeccion_kwh']:.2f} kWh (NetBilling)")
    print("-" * 70)
    print(" 1. DESGLOSE DEL GASTO EN COMPRA / CONSUMO DE ENERGÍA (con IVA 19%)")
    print("-" * 70)
    print(f"  * Cargo Fijo Mensual                       : {formatear_clp(res['cargo_fijo'])}")
    print(f"  * Cargo por Transmisión                    : {formatear_clp(res['costo_transmision'])}")
    print(f"  * Cargo por Servicio Público               : {formatear_clp(res['costo_serv_publico'])}")
    print(f"  * Cargo por Compra de Energía (con IVA)    : {formatear_clp(res['costo_energia_base'])}")
    if res['costo_sobreconsumo_invierno'] > 0:
        print(f"  * Recargo Límite de Invierno (Sobreconsumo): {formatear_clp(res['costo_sobreconsumo_invierno'])}")
    if res['costo_potencia'] > 0:
        print(f"  * Cargo por Demanda de Potencia            : {formatear_clp(res['costo_potencia'])}")
        print(f"    ({res['detalle_potencia']})")
    print("    " + "-"*40)
    print(f"  >> TOTAL A PAGAR POR CONSUMO (con IVA)    : {formatear_clp(res['total_consumo'])}")

    print("\n" + "-" * 70)
    print(" 2. LIQUIDACIÓN POR VENTA / INYECCIÓN DE ENERGÍA (con IVA 19%)")
    print("-" * 70)
    if res['inyeccion_kwh'] > 0:
        print(f"  * Energía Inyectada a la Red               : {res['inyeccion_kwh']:.2f} kWh")
        print(f"  * Precio Venta / Inyección (con IVA 19%)   : ${res['precio_inyeccion_unit']:.3f} /kWh")
        print(f"  >> TOTAL ABONADO POR DISTRIBUIDORA (IVA)  : {formatear_clp(res['total_inyeccion'])}")
    else:
        print("  * No se registraron inyecciones a la red en el periodo (0 kWh).")
        print("  >> TOTAL ABONADO                           : $0")

    print("\n" + "=" * 70)
    print(" 3. BALANCE FINAL A PAGAR EN LA BOLETA")
    print("=" * 70)
    balance = res['balance_neto']
    if balance > 0:
        print(f"  TOTAL NETO A PAGAR POR EL CLIENTE         : {formatear_clp(balance)}")
        if res['total_inyeccion'] > 0:
            ahorro_pct = (res['total_inyeccion'] / res['total_consumo']) * 100
            print(f"  [Ahorro obtenido gracias a inyección solar: {ahorro_pct:.1f}% de la cuenta]")
    elif balance < 0:
        print(f"  SALDO A FAVOR DEL CLIENTE (REMANENTE)     : {formatear_clp(abs(balance))}")
        print("  [Este saldo a favor se descontará en la siguiente boleta o se devolverá según contrato]")
    else:
        print("  TOTAL NETO A PAGAR                        : $0 (Consumo completamente compensado)")
    print("=" * 70 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Calculadora de Tarifas Eléctricas en Baja Tensión y NetBilling (Chile)"
    )
    parser.add_argument("--zona", type=str, help="Nombre de la comuna o zona (ej: Buin, Santiago, Concepción)")
    parser.add_argument("--tarifa", type=str, choices=["BT1", "BT2", "BT3", "BT4.1", "BT4.2", "BT4.3"], help="Opción tarifaria")
    parser.add_argument("--consumo", type=float, help="Consumo de energía mensual en kWh")
    parser.add_argument("--inyeccion", type=float, default=0.0, help="Inyección de energía a la red en kWh")
    parser.add_argument("--mes", type=int, default=None, help="Mes de facturación (1-12) para evaluar invierno en BT1")
    parser.add_argument("--limite-invierno", type=float, default=0.0, help="Límite de invierno en kWh si aplica")
    parser.add_argument("--potencia", type=float, help="Potencia contratada o leída en kW para BT2/BT3")
    parser.add_argument("--potencia-punta", type=float, help="Potencia en horas punta para BT4 (kW)")
    parser.add_argument("--potencia-fuera", type=float, help="Potencia fuera de punta para BT4 (kW)")
    parser.add_argument("--actualizar", action="store_true", help="Fuerza la conexión a internet para descargar el último pliego publicado")

    args = parser.parse_args()
    
    # Cargar o actualizar automáticamente según el mes actual en ejecución
    db = cargar_base_datos(mes_objetivo=args.mes, forzar=args.actualizar)

    # Si se especificaron los argumentos mínimos requeridos, corre en modo silencioso/directo
    if args.zona and args.tarifa and (args.consumo is not None):
        zona_nombre, params = seleccionar_zona(db, args.zona)
        mostrar_precios_tarifa(zona_nombre, params, args.tarifa)
        mes_calculo = args.mes if args.mes is not None else datetime.now().month
        variables = {
            "consumo_kwh": args.consumo,
            "inyeccion_kwh": args.inyeccion,
            "mes": mes_calculo,
            "es_invierno": mes_calculo in [5, 6, 7, 8, 9],
            "limite_invierno": args.limite_invierno
        }
        if args.tarifa == "BT2":
            variables["potencia_contratada_kw"] = args.potencia or 10.0
        elif args.tarifa == "BT3":
            variables["demanda_maxima_kw"] = args.potencia or 10.0
        elif args.tarifa in ["BT4.1", "BT4.2", "BT4.3"]:
            variables["potencia_punta_kw"] = args.potencia_punta or 5.0
            variables["potencia_fuera_punta_kw"] = args.potencia_fuera or 10.0
            variables["potencia_suministrada_kw"] = args.potencia_fuera or 10.0

        res = calcular_facturacion(zona_nombre, params, args.tarifa, variables)
        imprimir_reporte(res)
        return

    # Modo Interactivo
    print("\n" + "#"*70)
    print("   CALCULADORA DE TARIFAS ELÉCTRICAS EN BAJA TENSIÓN Y NETBILLING")
    print("                 Sector Regulado de Distribución - Chile")
    print("   [Salir en cualquier momento: Presione 'Esc', 'Ctrl+Q' o escriba 'salir']")
    print("#"*70)

    try:
        zona_nombre, params = seleccionar_zona(db)
        tarifa = seleccionar_tarifa()
        mostrar_precios_tarifa(zona_nombre, params, tarifa)
        variables = solicitar_variables(tarifa)

        res = calcular_facturacion(zona_nombre, params, tarifa, variables)
        imprimir_reporte(res)
    except (SalidaSolicitada, KeyboardInterrupt, EOFError):
        cerrar_programa()

if __name__ == "__main__":
    main()
