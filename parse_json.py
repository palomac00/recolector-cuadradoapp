#!/usr/bin/env python3
import sys
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import pytz
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def parse_arrivals(json_file):
    """Parse Cuadrado API JSON → lista de arrivals"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    arrivals = []
    tz_ar = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz_ar)
    
    for arrival in data['arribos']:
        minutos = arrival['tiempo']
        bandera = arrival['bandera']
        programado = "📅" if arrival['programado'] else "🚌"
        gps = arrival.get('coordsCoche', None)
        
        eta = now + timedelta(minutes=minutos)
        hora_eta = eta.strftime("%H:%M")
        
        arrivals.append({
            'hora_eta': hora_eta,
            'bandera': bandera,
            'minutos_restantes': minutos,
            'status': programado,
            'gps': gps
        })
    
    return arrivals

def create_excel_3_sheets(arrivals):
    """Crear Excel con 3 hojas"""
    Path("data").mkdir(exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Headers
    headers = ["ETA", "BANDERA", "MIN", "ESTADO"]
    header_fill = PatternFill(start_color="3673A5", end_color="3673A5", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    def format_sheet(ws, dataframe):
        """Write headers and data to worksheet"""
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
        
        for row_idx, row in enumerate(dataframe.itertuples(index=False), 2):
            ws.cell(row=row_idx, column=1, value=row.hora_eta)
            ws.cell(row=row_idx, column=2, value=row.bandera)
            ws.cell(row=row_idx, column=3, value=row.minutos_restantes)
            ws.cell(row=row_idx, column=4, value=row.status)
        
        ws.column_dimensions['A'].width = 8
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 6
        ws.column_dimensions['D'].width = 8
    
    # Sheet 1: TODOS
    ws1 = wb.create_sheet("TODOS")
    df_all = pd.DataFrame(arrivals)
    format_sheet(ws1, df_all)
    
    # Sheet 2: SOLO 215
    ws2 = wb.create_sheet("215")
    df_215 = pd.DataFrame([a for a in arrivals if '215' in a['bandera']])
    if not df_215.empty:
        format_sheet(ws2, df_215)
    else:
        ws2.cell(row=1, column=1, value="SIN DATOS")
    
    # Sheet 3: COMBINADAS (ordenadas por tiempo)
    ws3 = wb.create_sheet("COMBINADAS")
    df_combined = pd.DataFrame(arrivals).sort_values('minutos_restantes')
    format_sheet(ws3, df_combined)
    
    fecha = datetime.now().strftime("%Y-%m-%d")
filename = f"data/horarios-141-{fecha}.xlsx"

    wb.save(filename)
    print(f"✅ Excel guardado: {filename} ({len(arrivals)} buses)")

def create_txt(arrivals):
    """TXT legible para Notion/sync"""
    Path("data").mkdir(exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/horarios-141-{fecha}.txt", "w", encoding="utf-8") as f:
        f.write(f"HORARIOS LÍNEA 141 - {datetime.now().strftime('%d/%m %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        
        # Primero los 215
        buses_215 = [a for a in arrivals if '215' in a['bandera']]
        if buses_215:
            f.write("🚐 215A/B/C (TUS FAVORITOS)\n")
            f.write("-" * 40 + "\n")
            for bus in buses_215:
                f.write(f"{bus['hora_eta']:>6} {bus['bandera']:<25} {bus['status']} {bus['minutos_restantes']:>3}min\n")
            f.write("\n")
        
        # Todos ordenados
        f.write("📋 TODOS LOS BUSES (orden ETA)\n")
        f.write("-" * 40 + "\n")
        for bus in sorted(arrivals, key=lambda x: x['minutos_restantes']):
            f.write(f"{bus['hora_eta']:>6} {bus['bandera']:<25} {bus['status']} {bus['minutos_restantes']:>3}min\n")
    
    print(f"✅ TXT guardado: data/horarios-141-{fecha}.txt")  # ← Línea corregida


def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_json.py input.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    arrivals = parse_arrivals(json_file)
    
    print(f"📊 {len(arrivals)} horarios parseados")
    print(f"🚐 {len([a for a in arrivals if '215' in a['bandera']])} buses 215 encontrados")
    
    create_excel_3_sheets(arrivals)
    create_txt(arrivals)
    
    print("🎉 Recolector COMPLETO: Excel(3 hojas) + TXT cada 10min")

if __name__ == "__main__":
    main()
