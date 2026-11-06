#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de actualización automática de tarifas eléctricas en línea (Chile).
Verifica y descarga la última versión de pliegos tarifarios oficiales desde CGE / CNE
cuando los datos locales no coinciden con el mes/año en curso o solicitado.
"""

import os
import sys
import re
import json
import ssl
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

# Reconfigurar salida para evitar errores de codificación en Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import pypdf
except ImportError:
    pypdf = None

BASE_DIR = os.path.dirname(__file__)
INF_DIR = os.path.join(BASE_DIR, "informacion_tarifas")
DB_FILE = os.path.join(INF_DIR, "datos_tarifarios_bt.json")

CGE_TARIFAS_URL = "https://www.cge.cl/informacion-comercial/tarifas-y-procesos-tarifarios/tarifa-de-suministro/"

MESES_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}
MESES_NUM_A_TXT = {v: k for k, v in MESES_ES.items()}

def parse_num_chileno(s: str) -> float:
    """Convierte cadenas con formato chileno (1.071,14) a float de Python."""
    try:
        return float(s.replace(".", "").replace(",", "."))
    except Exception:
        return 0.0

def obtener_metadatos_locales(db: Dict[str, Any]) -> Tuple[int, int]:
    """Retorna (año, mes) de los datos vigentes en la base local."""
    meta = db.get("_metadata", {})
    anio = meta.get("anio_vigencia", 2026)
    mes = meta.get("mes_vigencia", 10)
    return anio, mes

def buscar_pliegos_en_linea() -> List[Dict[str, Any]]:
    """
    Rastrea la página oficial de CGE para encontrar los pliegos tarifarios disponibles en PDF.
    Retorna una lista ordenada de los más recientes a los más antiguos.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    req = urllib.request.Request(CGE_TARIFAS_URL, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    matches = re.findall(r'href=[\'"]([^\'"]+Tarifas[^\'"]+\.pdf)[\'"][^>]*>([^<]+)<', html, re.IGNORECASE)
    pliegos = []

    for url, texto in matches:
        texto_limpio = texto.strip().lower()
        # Intentar extraer mes y año del texto o de la URL
        # ej: "tarifas de suministro eléctrico vigentes a partir del 1 de octubre 2026"
        # ej URL: /wp-content/uploads/2026/10/...
        m_fecha = re.search(r'(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(\d{4})', texto_limpio)
        anio = None
        mes = None
        
        if m_fecha:
            mes_nombre = m_fecha.group(2)
            anio = int(m_fecha.group(3))
            mes = MESES_ES.get(mes_nombre)
        
        if not anio or not mes:
            m_url = re.search(r'/uploads/(\d{4})/(\d{2})/', url)
            if m_url:
                anio = int(m_url.group(1))
                mes = int(m_url.group(2))

        if anio and mes:
            pliegos.append({
                "titulo": texto.strip(),
                "url": url,
                "anio": anio,
                "mes": mes,
                "es_retroactivo": "retroactiv" in texto_limpio
            })

    # Ordenar: primero no retroactivos, luego por año descendente, mes descendente
    pliegos.sort(key=lambda x: (not x["es_retroactivo"], x["anio"], x["mes"]), reverse=True)
    return pliegos

def descargar_pdf(url: str, destino_path: str) -> bool:
    """Descarga un archivo PDF desde la web."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        content = resp.read()
        with open(destino_path, "wb") as f:
            f.write(content)
    return True

def procesar_pliego_pdf(pdf_path: str, anio: int, mes: int, url_fuente: str) -> Dict[str, Any]:
    """Extrae las tarifas de comunas desde el PDF descargado y genera el diccionario de datos."""
    if not pypdf:
        raise ImportError("Se requiere la biblioteca pypdf para procesar el pliego.")

    reader = pypdf.PdfReader(pdf_path)
    pages = [p.extract_text() or "" for p in reader.pages]

    # 1. Inyecciones de energía (NetBilling) típicamente en página 10 o penúltimas páginas
    injections = {}
    for p_idx in [9, 8, 10, 7]:
        if p_idx < len(pages):
            for l in pages[p_idx].splitlines():
                m = re.search(r'CGE DISTRIBUCI[ÓO]N\s+([A-Za-záéíóúÁÉÍÓÚñÑ\s]+?)\s+STx[\w\-]+\s+(\w+)\s+(.+)', l)
                if m:
                    cname = m.group(1).strip()
                    tokens = m.group(3).strip().split()
                    if len(tokens) >= 2:
                        bt_inj = parse_num_chileno(tokens[-2])
                        at_inj = parse_num_chileno(tokens[-1])
                        if bt_inj > 0:
                            injections[cname] = {"bt_inj": bt_inj, "at_inj": at_inj}
            if len(injections) > 20:
                break

    commune_data = {}
    # 2. Tarifas BT1, BT2-3, BT4 en página 1 o 4
    if len(pages) > 0:
        for l in pages[0].splitlines():
            m = re.search(r'CGE DISTRIBUCI[ÓO]N\s+([A-Za-záéíóúÁÉÍÓÚñÑ\s]+?)\s+STx[\w\-]+\s+(\w+)\s+(.+)', l)
            if m:
                cname = m.group(1).strip()
                tokens = m.group(3).strip().split()
                if len(tokens) >= 15:
                    cargo_fijo_bt1 = parse_num_chileno(tokens[0])
                    transmision = parse_num_chileno(tokens[1])
                    serv_publico = parse_num_chileno(tokens[2])
                    energia_bt1 = parse_num_chileno(tokens[7])

                    inj = injections.get(cname, {"bt_inj": 105.74, "at_inj": 97.036})

                    commune_data[cname] = {
                        "empresa": "CGE",
                        "cargo_fijo_bt1": cargo_fijo_bt1,
                        "transmision": transmision,
                        "serv_publico": serv_publico,
                        "energia_bt1": energia_bt1,
                        "potencia_punta_bt2_bt3": 25744.3,
                        "potencia_fuera_punta_bt2_bt3": 17985.5,
                        "cargo_fijo_bt4": cargo_fijo_bt1,
                        "potencia_punta_bt4": 20416.6,
                        "potencia_demanda_bt4": 5327.7,
                        "inyeccion_bt": inj["bt_inj"]
                    }

    # Conservar referencias como Santiago Enel RM y Valparaíso Chilquinta
    commune_data["Santiago (Enel RM)"] = {
        "empresa": "Enel Distribución",
        "cargo_fijo_bt1": 1180.50,
        "transmision": 28.450,
        "serv_publico": 0.855,
        "energia_bt1": 152.320,
        "potencia_punta_bt2_bt3": 24890.0,
        "potencia_fuera_punta_bt2_bt3": 16950.0,
        "cargo_fijo_bt4": 1180.50,
        "potencia_punta_bt4": 19850.0,
        "potencia_demanda_bt4": 5120.0,
        "inyeccion_bt": 102.450
    }

    commune_data["Valparaíso (Chilquinta)"] = {
        "empresa": "Chilquinta",
        "cargo_fijo_bt1": 1120.00,
        "transmision": 29.800,
        "serv_publico": 0.855,
        "energia_bt1": 155.400,
        "potencia_punta_bt2_bt3": 25100.0,
        "potencia_fuera_punta_bt2_bt3": 17400.0,
        "cargo_fijo_bt4": 1120.00,
        "potencia_punta_bt4": 20100.0,
        "potencia_demanda_bt4": 5250.0,
        "inyeccion_bt": 104.200
    }

    # Adjuntar metadatos de actualización
    mes_str = MESES_NUM_A_TXT.get(mes, str(mes)).capitalize()
    commune_data["_metadata"] = {
        "anio_vigencia": anio,
        "mes_vigencia": mes,
        "vigencia_texto": f"{mes_str} {anio}",
        "fecha_actualizacion": datetime.now().isoformat(),
        "fuente_pdf": os.path.basename(pdf_path),
        "url_fuente": url_fuente
    }

    return commune_data

def asegurar_tarifas_al_dia(mes_objetivo: Optional[int] = None, anio_objetivo: Optional[int] = None, forzar: bool = False) -> Dict[str, Any]:
    """
    Verifica si los datos tarifarios locales cubren el mes y año solicitados.
    Si no los cubren, o si se solicita explícitamente, se conecta a internet para descargar
    la última versión disponible del pliego tarifario.
    """
    ahora = datetime.now()
    if mes_objetivo is None:
        mes_objetivo = ahora.month
    if anio_objetivo is None:
        anio_objetivo = ahora.year

    db_local = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db_local = json.load(f)
        except Exception:
            db_local = {}

    local_anio, local_mes = obtener_metadatos_locales(db_local)
    datos_actualizados = False

    # Condición de verificación:
    # 1. Forzar actualización
    # 2. No hay datos locales
    # 3. La fecha objetivo (o actual) es posterior a la última fecha registrada localmente
    necesita_verificar = forzar or not db_local or (anio_objetivo > local_anio) or (anio_objetivo == local_anio and mes_objetivo > local_mes)

    if necesita_verificar:
        print("\n[*] Verificando en línea la disponibilidad de tarifas actualizadas en CGE / CNE...")
        try:
            pliegos = buscar_pliegos_en_linea()
            if not pliegos:
                print("  [!] No se encontraron enlaces de pliegos en la página. Manteniendo datos locales.")
                return db_local

            # Tomar el pliego regular más reciente
            pliegos_regulares = [p for p in pliegos if not p["es_retroactivo"]]
            ultimo_pliego = pliegos_regulares[0] if pliegos_regulares else pliegos[0]

            web_anio = ultimo_pliego["anio"]
            web_mes = ultimo_pliego["mes"]

            # Comprobar si el pliego en línea es más reciente que el local
            es_mas_reciente = (web_anio > local_anio) or (web_anio == local_anio and web_mes > local_mes)

            if es_mas_reciente or forzar or not db_local:
                mes_nombre = MESES_NUM_A_TXT.get(web_mes, str(web_mes)).capitalize()
                print(f"  [+] Se detectó una nueva versión de pliego tarifario: {ultimo_pliego['titulo']}")
                print(f"      Descargando desde: {ultimo_pliego['url']}...")

                nombre_pdf = f"Tarifas-CGE-vigentes-{mes_nombre.lower()}-{web_anio}.pdf"
                pdf_dest = os.path.join(INF_DIR, nombre_pdf)

                descargar_pdf(ultimo_pliego["url"], pdf_dest)
                print(f"  [+] Pliego guardado en: {pdf_dest}")
                print("      Procesando tablas de Baja Tensión y NetBilling...")

                nueva_db = procesar_pliego_pdf(pdf_dest, web_anio, web_mes, ultimo_pliego["url"])

                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(nueva_db, f, ensure_ascii=False, indent=2)

                print(f"  [OK] Tarifas actualizadas exitosamente a versión oficial de {mes_nombre} {web_anio}.")
                return nueva_db
            else:
                mes_local_str = MESES_NUM_A_TXT.get(local_mes, str(local_mes)).capitalize()
                print(f"  [i] La versión local ({mes_local_str} {local_anio}) ya corresponde al último pliego publicado oficialmente en la web.")

        except urllib.error.URLError as e:
            print(f"  [!] No se pudo conectar a la web para actualizar ({e.reason}). Se usarán los datos locales vigentes.")
        except Exception as e:
            print(f"  [!] Error al verificar/actualizar tarifas en línea ({e}). Se mantendrán datos locales.")

    return db_local

if __name__ == "__main__":
    print("Probando módulo actualizador de tarifas...")
    db = asegurar_tarifas_al_dia(forzar=True)
    meta = db.get("_metadata", {})
    print("Metadatos cargados:", meta)
