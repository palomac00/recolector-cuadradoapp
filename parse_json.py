#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚌 PARSER JSON CUADRADO LÍNEA 141 → Excel/TXT
Manejo errores + JSON vacío
"""
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import sys
from pathlib import Path

def parse_arribos(json_data):
    """Parsea JSON con manejo de errores"""
    ba_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(ba_tz)
    
    if 'arribos' not in json_data or not json_data['arribos']:
        return [{
            'timestamp': now.strftime('%d/%m/%Y %H:%M:%S'),
            'mensaje': 'Sin datos de arribos',
            'hora_actual': now.strftime('%H:%M')
        }]
    
    arrivals = []
    for arrival in json_data['arribos']:
        mins = arrival.get('tiempo', 0)
        bandera = arrival.get('bandera', 'SIN DATOS')
        prog = arrival.get('programado', False)
        eta = now + timedelta(minutes=mins)
        
        arrivals.append({
            'timestamp': now.strftime('%d/%m/%Y %H:%M:%S'),
            'hora_actual': now.strftime('%H:%M'),
            'hora_eta': eta.strftime('%H:%M'),
            'minutos_restantes': mins,
            'bandera': bandera,
            'programado': '📅' if prog else '',
            '215_detectado': '✅' if '215' in str(bandera) else ''
        })
    
    return arrivals

def main():
    try:
        # Leer JSON (archivo o stdin)
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r') as f:
                raw = f.read().strip()
        else:
            raw = sys.stdin.read().strip()
        
        if not raw:
            print("❌ JSON vacío")
            sys.exit(1)
        
        data = json.loads(raw)
        arrivals = parse_arribos(data)
        
        # TXT legible
        print(f"🚌 LÍNEA 141 - {arrivals[0]['timestamp']}")
        if len(arrivals) == 1 and 'Sin datos' in str(arrivals[0]):
            print("📭 Sin arribos disponibles")
        else:
            print(f"📊 {len(arrivals)} arribos")
        print("="*70)
        
        for i, a in enumerate(arrivals, 1):
            if 'Sin datos' in str(a):
                print(f"{i}. {a.get('mensaje', 'Error')}")
            else:
                print(f"{i:2d}. {a['hora_eta']:>5s} - {a['bandera']:<22} ({a['minutos_restantes']:>3}min){a['programado']}{a['215_detectado']}")
        
        # Crear data/
        Path("data").mkdir(exist_ok=True)
        
        # TXT
        with open("data/horarios-141.txt", "w", encoding="utf-8") as f:
            f.write(f"🚌 LÍNEA 141 - {arrivals[0]['timestamp']}\n")
            if len(arrivals) == 1 and 'Sin datos' in str(arrivals[0]):
                f.write("📭 Sin arribos disponibles\n")
            else:
                f.write(f"📊 {len(arrivals)} arribos\n\n")
                for i, a in enumerate(arrivals, 1):
                    if 'Sin datos' in str(a):
                        f.write(f"{i}. {a.get('mensaje', 'Error')}\n")
                    else:
                        f.write(f"{i:2d}. {a['hora_eta']:>5s} - {a['bandera']:<22} ({a['minutos_restantes']:>3}min){a['programado']}{a['215_detectado']}\n")
        
        # Excel (solo si hay datos reales)
        if len(arrivals) > 0 and 'Sin datos' not in str(arrivals[0]):
            df = pd.DataFrame(arrivals)
            df.to_excel("data/arribos-141.xlsx", index=False)
            print("✅ Excel: data/arribos-141.xlsx")
        
        print("✅ TXT: data/horarios-141.txt")
        
    except json.JSONDecodeError:
        print("❌ JSON inválido")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Archivo no encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
