#!/usr/bin/env python3
import sys
import json
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from openpyxl.styles import Font

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

def get_fecha_excel():
    """Nombre del Excel de HOY: horarios-141-YYYY-MM-DD.xlsx"""
    return f"data/horarios-141-{datetime.now(TZ_AR).strftime('%Y-%m-%d')}.xlsx"

def parse_arrivals(json_file):
    """Parse Cuadrado API JSON → lista de arrivals"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    arrivals = []
    now = datetime.now(TZ_AR)
    hora_scraping = now.strftime("%H:%M:%S")
    
    for arrival in data['arribos']:
        minutos = arrival['tiempo']
        bandera = arrival['bandera']
        parada = arrival['parada']  # ← FIX: usar campo real del merge
        
        eta = now + timedelta(minutes=minutos)
        hora_eta = eta.strftime("%H:%M")
        
        arrivals.append({
            'Hora_Scrap': hora_scraping,
            'Hora_Llegada': hora_eta,
            'Linea': bandera,
            'Minutos': minutos,
            'Parada': parada
        })
    
    return arrivals

def guardar_excel_dia(horarios_nuevos):
    """Actualiza SOLO el Excel de HOY - FILTRADO por parada"""
    archivo_hoy = get_fecha_excel()
    Path("data").mkdir(exist_ok=True)
    ahora = datetime.now(TZ_AR)
    
    # FILTRAR NUEVOS DATOS por parada DESDE el principio
    nuevos_lp1912 = [h for h in horarios_nuevos if h['Parada'] == 'LP1912']
    nuevos_215_lp1912 = [h for h in horarios_nuevos if h['Parada'] == 'LP1912' and '215' in str(h['Linea'])]
    nuevos_otras = [h for h in horarios_nuevos if h['Parada'] in ['L6173', 'L6203']]
    
    # DataFrames FILTRADOS (SIN concatenar viejos)
    df_lp1912 = pd.DataFrame(nuevos_lp1912).drop_duplicates(subset=['Hora_Llegada', 'Linea'])
    df_215 = pd.DataFrame(nuevos_215_lp1912).drop_duplicates(subset=['Hora_Llegada', 'Linea'])
    df_otras = pd.DataFrame(nuevos_otras).drop_duplicates(subset=['Hora_Llegada', 'Linea', 'Parada'])
    
    # Ordenar
    for df in [df_lp1912, df_215, df_otras]:
        if not df.empty:
            df.sort_values('Hora_Llegada', inplace=True)
    
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, sheet_name='LP1912', index=False, startrow=4)
        df_215.to_excel(writer, sheet_name='LP1912-215', index=False, startrow=4)
        df_otras.to_excel(writer, sheet_name='6203-6173', index=False, startrow=4)
        
        # Headers
        for sheet_name, df, titulo in [
            ('LP1912', df_lp1912, 'LP1912'),
            ('LP1912-215', df_215, 'LP1912-215'), 
            ('6203-6173', df_otras, '6203-6173')
        ]:
            ws = writer.sheets[sheet_name]
            ws['A1'] = f'LÍNEA 141 - {titulo} - {ahora.strftime("%d/%m/%Y")}'
            ws['A2'] = f'Actualización: {ahora.strftime("%H:%M:%S")}'
            ws['A3'] = f'Filas: {len(df)}'
            ws['A1'].font = Font(bold=True)
            ws['A2'].font = Font(bold=True)
            ws['A3'].font = Font(bold=True)

    print(f"✅ FILTRADO:")
    print(f"   LP1912: {len(df_lp1912)} buses")
    print(f"   LP1912-215 SOLO: {len(df_215)} buses 215")
    print(f"   6203-6173: {len(df_otras)} buses")

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_json.py input.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    arrivals = parse_arrivals(json_file)
    
    print(f"📊 {len(arrivals)} horarios parseados")
    print(f"🚐 {len([a for a in arrivals if '215' in a['Linea']])} buses 215 encontrados")
    
    guardar_excel_dia(arrivals)
    
    print("🎉 Recolector COMPLETO")

if __name__ == "__main__":
    main()
