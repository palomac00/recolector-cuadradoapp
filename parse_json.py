#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚌 PARSER JSON CUADRADO LÍNEA 141 → Excel/TXT
GitHub Actions cada 10min
"""
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import sys
from pathlib import Path

def parse_arribos(json_data):
    ba_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(ba_tz)
    
    arrivals = []
    for arrival in json_data['arribos']:
        mins = arrival['tiempo']
        bandera = arrival['bandera']
        prog = arrival['programado']
        eta = now + timedelta(minutes=mins)
        
        arrivals.append({
            'timestamp': now.strftime('%d/%m/%Y %H:%M:%S'),
            'hora_actual': now.strftime('%H:%M'),
            'hora_eta': eta.strftime('%H:%M'),  # ← NUEVA
            'minutos_restantes': mins,
            'bandera': bandera,
            'programado': '📅' if prog else '',
            '215_detectado': '✅' if '215' in bandera else ''
        })
    
    return arrivals

def main():
    # Leer JSON (puede ser archivo o stdin)
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = json.loads(sys.stdin.read())
    
    arrivals = parse_arribos(data)
    
    # TXT legible
    print(f"🚌 LÍNEA 141 - {arrivals[0]['timestamp']}")
    print(f"📊 {len(arrivals)} arribos")
    print("="*60)
    for i, a in enumerate(arrivals, 1):
        print(f"{i:2d}. {a['eta']} - {a['bandera']:<20} ({a['minutos_restantes']}min){a['programado']}{a['215_detectado']}")
    
    # Guardar TXT
    Path("data").mkdir(exist_ok=True)
    with open("data/horarios-141.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - {arrivals[0]['timestamp']}\n")
        f.write(f"📊 {len(arrivals)} arribos\n\n")
        for i, a in enumerate(arrivals, 1):
            f.write(f"{i:2d}. {a['eta']} - {a['bandera']:<20} ({a['minutos_restantes']}min){a['programado']}{a['215_detectado']}\n")
    
    # Excel
    df = pd.DataFrame(arrivals)
    df.to_excel("data/arribos-141.xlsx", index=False)
    print("✅ Guardado: data/arribos-141.xlsx + data/horarios-141.txt")

if __name__ == "__main__":
    main()
