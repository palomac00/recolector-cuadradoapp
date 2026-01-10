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
    return f"data/horarios-141-{datetime.now(TZ_AR).strftime('%Y-%m-%d')}.xlsx"

def parse_arrivals(json_file):
    """Parse Cuadrado API JSON → lista de arrivals"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("🔍 DEBUG JSON entrada:")
    print(f"Total arribos: {len(data['arribos'])}")
    
    arrivals = []
    now = datetime.now(TZ_AR)
    hora_scraping = now.strftime("%H:%M:%S")
    
    # DEBUG: Verificar campo 'parada'
    for i, arrival in enumerate(data['arribos'][:5]):  # Primeros 5
        parada = arrival.get('parada', 'SIN_PARADA')
        bandera = arrival.get('bandera', 'SIN_BANDE')
        print(f"  Arribo {i}: parada='{parada}' bandera='{bandera}'")
    
    for arrival in data['arribos']:
        minutos = arrival['tiempo']
        bandera = arrival['bandera']
        parada_raw = arrival.get('parada')  # ← VERIFICAMOS AQUÍ
        
        # DEBUG: Contar 215 por parada
        if '215' in str(bandera):
            print(f"🚐 215 detectado: parada='{parada_raw}' bandera='{bandera}'")
        
        # SI NO tiene parada, usar nombre del archivo como fallback
        if parada_raw is None:
            print("❌ ERROR: input.json sin campo 'parada'!")
            parada = 'UNKNOWN'
        else:
            parada = parada_raw
        
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
    """FILTRADO estrictamente por parada"""
    archivo_hoy = get_fecha_excel()
    Path("data").mkdir(exist_ok=True)
    
    # DEBUG: Contar por parada y línea
    print("\n🔍 DEBUG FILTRADO:")
    lp1912_total = [h for h in horarios_nuevos if h['Parada'] == 'LP1912']
    lp1912_215 = [h for h in horarios_nuevos if h['Parada'] == 'LP1912' and '215' in str(h['Linea'])]
    todas_paradas = set(h['Parada'] for h in horarios_nuevos)
    
    print(f"Paradas encontradas: {todas_paradas}")
    print(f"LP1912 total: {len(lp1912_total)} buses")
    print(f"LP1912 SOLO 215: {len(lp1912_215)} buses")
    
    # FILTRADO FINAL
    df_lp1912 = pd.DataFrame(lp1912_total).drop_duplicates(subset=['Hora_Llegada', 'Linea'])
    df_215 = pd.DataFrame(lp1912_215).drop_duplicates(subset=['Hora_Llegada', 'Linea'])
    df_otras = pd.DataFrame([h for h in horarios_nuevos if h['Parada'] in ['L6173', 'L6203']])
    
    print(f"FINAL - LP1912-215: {len(df_215)} filas")
    
    ahora = datetime.now(TZ_AR)
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, sheet_name='LP1912', index=False, startrow=4)
        df_215.to_excel(writer, sheet_name='LP1912-215', index=False, startrow=4)
        df_otras.to_excel(writer, sheet_name='6203-6173', index=False, startrow=4)
        
        for sheet_name, df, titulo in [
            ('LP1912', df_lp1912, 'LP1912'),
            ('LP1912-215', df_215, 'LP1912-215'), 
            ('6203-6173', df_otras, '6203-6173')
        ]:
            ws = writer.sheets[sheet_name]
            ws['A1'] = f'LÍNEA 141 - {titulo}'
            ws['A2'] = f'{ahora.strftime("%d/%m %H:%M:%S")}'
            ws['A3'] = f'Filas: {len(df)}'
            for cell in ['A1', 'A2', 'A3']: 
                ws[cell].font = Font(bold=True)

def main():
    json_file = sys.argv[1]
    arrivals = parse_arrivals(json_file)
    
    print(f"\n📊 {len(arrivals)} total parseados")
    guardar_excel_dia(arrivals)
    print("🎉 COMPLETO")

if __name__ == "__main__":
    main()
