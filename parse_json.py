#!/usr/bin/env python3
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

def parse_arrivals(json_file):
    """Parse Cuadrado API JSON → lista de arrivals"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    arrivals = []
    now = datetime.now()
    
    for i, arrival in enumerate(data['arribos'], 1):
        minutos = arrival['tiempo']
        bandera = arrival['bandera']
        programado = "📅" if arrival['programado'] else "🚌"
        gps = arrival.get('coordsCoche', None)
        
        eta = now + timedelta(minutes=minutos)
        hora_eta = eta.strftime("%H:%M")
        
        arrivals.append({
            'nro': i,
            'hora_eta': hora_eta,
            'bandera': bandera,
            'minutos_restantes': minutos,
            'status': programado,
            'gps': gps
        })
    
    return arrivals

def create_excel_3_sheets(arrivals):
    """Crear Excel con 3 hojas como tu recolector anterior"""
    Path("data").mkdir(exist_ok=True)
    wb = Workbook()
    
    # Hoja 1: TODOS los buses
    ws1 = wb.active
    ws1.title = "TODOS"
    df_all = pd.DataFrame(arrivals)
    
    for r_idx, row in enumerate(df_all.itertuples(), 1):
        ws1[f'A{r_idx}'] = row.nro
        ws1[f'B{r_idx}'] = row.hora_eta
        ws1[f'C{r_idx}'] = row.bandera
        ws1[f'D{r_idx}'] = row.minutos_restantes
        ws1[f'E{r_idx}'] = row.status
    
    # Hoja 2: SOLO 215 (tus favoritos)
    ws2 = wb.create_sheet("215")
    df_215 = pd.DataFrame([a for a in arrivals if '215' in a['bandera']])
    
    if not df_215.empty:
        for r_idx, row in enumerate(df_215.itertuples(), 1):
            ws2[f'A{r_idx}'] = row.nro
            ws2[f'B{r_idx}'] = row.hora_eta
            ws2[f'C{r_idx}'] = row.bandera
            ws2[f'D{r_idx}'] = row.minutos_restantes
            ws2[f'E{r_idx}'] = row.status
    
    # Hoja 3: COMBINADAS (ordenadas por tiempo)
    ws3 = wb.create_sheet("COMBINADAS")
    df_combined = pd.DataFrame(arrivals).sort_values('minutos_restantes')
    
    for r_idx, row in enumerate(df_combined.itertuples(), 1):
        ws3[f'A{r_idx}'] = row.nro
        ws3[f'B{r_idx}'] = row.hora_eta
        ws3[f'C{r_idx}'] = row.bandera
        ws3[f'D{r_idx}'] = row.minutos_restantes
        ws3[f'E{r_idx}'] = row.status
    
    # Formatting
    for ws in [ws1, ws2, ws3]:
        ws['A1'] = "N°"
        ws['B1'] = "ETA"
        ws['C1'] = "BANDERA"
        ws['D1'] = "MIN"
        ws['E1'] = "ESTADO"
        for col in ['A1', 'B1', 'C1', 'D1', 'E1']:
            ws[col].font = Font(bold=True, color="FFFFFF")
            ws[col].fill = PatternFill(start_color="3673A5", end_color="3673A5", fill_type="solid")
    
    filename = "data/horarios-141.xlsx"
    wb.save(filename)
    print(f"✅ Excel guardado: {filename} ({len(arrivals)} buses)")

def create_txt(arrivals):
    """TXT legible para Notion/sync"""
    Path("data").mkdir(exist_ok=True)
    with open("data/horarios-141.txt", "w", encoding="utf-8") as f:
        f.write(f"HORARIOS LÍNEA 141 - {datetime.now().strftime('%d/%m %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        
        # Primero los 215
        buses_215 = [a for a in arrivals if '215' in a['bandera']]
        if buses_215:
            f.write("🚐 215A/B/C (TUS FAVORITOS)\n")
            f.write("-" * 30 + "\n")
            for bus in buses_215:
                f.write(f"{bus['hora_eta']:>6} {bus['bandera']:<25} {bus['status']} {bus['minutos_restantes']:>3}min\n")
            f.write("\n")
        
        # Todos ordenados
        f.write("📋 TODOS LOS BUSES (orden ETA)\n")
        f.write("-" * 40 + "\n")
        for bus in sorted(arrivals, key=lambda x: x['minutos_restantes']):
            f.write(f"{bus['hora_eta']:>6} {bus['bandera']:<25} {bus['status']} {bus['minutos_restantes']:>3}min\n")
    
    print("✅ TXT guardado: data/horarios-141.txt")

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
