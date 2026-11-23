#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script generador de la base de datos local datos_tarifarios_bt.json
a partir del pliego tarifario PDF de CGE / CONAFE / EMELAT / ELECDA / ELIQSA / EMELARI.
"""

import os
import json
from actualizador_tarifas import procesar_pliego_pdf, DB_FILE, INF_DIR

def main():
    pdf_nov = os.path.join(INF_DIR, "Tarifas-CGE-vigentes-noviembre-2026.pdf")
    if os.path.exists(pdf_nov):
        pdf_path = pdf_nov
        url_fuente = "https://www.cge.cl/wp-content/uploads/2026/11/Tarifas-de-Suministro-Electrico-vigentes-a-partir-del-1-de-noviembre-2026.pdf"
        mes = 11
    else:
        pdf_path = os.path.join(INF_DIR, "Tarifas-CGE-vigentes-octubre-2026.pdf")
        url_fuente = "https://www.cge.cl/wp-content/uploads/2026/10/Tarifas-de-Suministro-Electrico-vigentes-a-partir-del-1-de-octubre-2026.pdf"
        mes = 10

    commune_data = procesar_pliego_pdf(pdf_path, 2026, mes, url_fuente)
    total_comunas = len([k for k in commune_data.keys() if k != "_metadata"])
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(commune_data, f, ensure_ascii=False, indent=2)

    print(f"Total de comunas/zonas procesadas y guardadas: {total_comunas}")
    print(f"Archivo actualizado: {DB_FILE}")

if __name__ == "__main__":
    main()
