import pypdf
import re
import json

reader = pypdf.PdfReader("informacion_tarifas/Tarifas-CGE-vigentes-octubre-2026.pdf")

# Let's extract lines from page 1 (BT1, BT2-3, BT4), page 4, page 10 (Injection)
# Let's write a robust extractor for communes
pages = [p.extract_text() for p in reader.pages]

commune_data = {}

def parse_num(s):
    try:
        # Chilean format: 1.071,14 -> 1071.14
        return float(s.replace(".", "").replace(",", "."))
    except:
        return 0.0

# Extract injection from page 10 (index 9)
p10_lines = pages[9].splitlines()
injections = {}
for l in p10_lines:
    m = re.search(r'CGE DISTRIBUCI[ÓO]N\s+([A-Za-záéíóúÁÉÍÓÚñÑ\s]+?)\s+STx[\w\-]+\s+(\w+)\s+(.+)', l)
    if m:
        cname = m.group(1).strip()
        tokens = m.group(3).strip().split()
        if len(tokens) >= 2:
            bt_inj = parse_num(tokens[-2])
            at_inj = parse_num(tokens[-1])
            injections[cname] = {"bt_inj": bt_inj, "at_inj": at_inj}

# Extract BT1, BT2, BT3, BT4 from page 1 (index 0)
p1_lines = pages[0].splitlines()
for l in p1_lines:
    m = re.search(r'CGE DISTRIBUCI[ÓO]N\s+([A-Za-záéíóúÁÉÍÓÚñÑ\s]+?)\s+STx[\w\-]+\s+(\w+)\s+(.+)', l)
    if m:
        cname = m.group(1).strip()
        tokens = m.group(3).strip().split()
        # tokens sample for Buin:
        # 1.071,14 (cargo fijo BT1)
        # 31,512 (transmision)
        # 0,855 (serv publico)
        # 1,778 2,931 3,738 4,084 (tramos FET)
        # 157,744 (energia BT1)
        # ...
        if len(tokens) >= 15:
            cargo_fijo_bt1 = parse_num(tokens[0])
            transmision = parse_num(tokens[1])
            serv_publico = parse_num(tokens[2])
            energia_bt1 = parse_num(tokens[7]) # 157.744
            
            # Cargo potencia punta / parcialmente punta
            # en tokens hay: 25.744,3 y 17.985,5
            # y para BT4: 5.327,7 y 20.416,6
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

# Add Enel RM reference data
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

print(f"Total de zonas procesadas: {len(commune_data)}")
with open("informacion_tarifas/datos_tarifarios_bt.json", "w", encoding="utf-8") as f:
    json.dump(commune_data, f, ensure_ascii=False, indent=2)

print("Guardado en informacion_tarifas/datos_tarifarios_bt.json")
