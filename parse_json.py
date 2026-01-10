#!/usr/bin/env python3
import sys
import json
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

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
        programado = "📅" if arrival['programado'] else "🚌"
        
        eta = now + timedelta(minutes=minutos)
        hora_eta = eta.strftime("%H:%M")
        
        arrivals.append({
            'Hora_Scrap': hora_scraping,
            'Hora_Llegada': hora_eta,
            'Bandera': bandera,
            'Minutos': minutos,
            'Estado': programado
        })
    
    return arrivals

def cargar_excel_dia():
    """Carga el Excel de HOY o retorna DataFrames vacíos"""
    archivo_hoy = get_fecha_excel()
    Path("data").mkdir(exist_ok=True)
    
    if not os.path.exists(archivo_hoy):
        return {
            'TODOS': pd.DataFrame(),
            '215': pd.DataFrame(),
            'COMBINADAS': pd.DataFrame()
        }
    
    try:
        excel_file = pd.ExcelFile(archivo_hoy)
        datos = {}
        
        for sheet in ['TODOS', '215', 'COMBINADAS']:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(archivo_hoy, sheet_name=sheet)
                datos[sheet] = df
            else:
                datos[sheet] = pd.DataFrame()
        
        return datos
    except Exception as e:
        print(f"⚠️ Error cargando {archivo_hoy}: {e}")
        return {
            'TODOS': pd.DataFrame(),
            '215': pd.DataFrame(),
            'COMBINADAS': pd.DataFrame()
        }

def guardar_excel_dia(horarios_nuevos):
    """Actualiza SOLO el Excel de HOY - SIN DUPLICADOS"""
    datos_existentes = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo_hoy = get_fecha_excel()
    Path("data").mkdir(exist_ok=True)
    
    # TODOS
    df_nuevos = pd.DataFrame(horarios_nuevos)
    df_todos = pd.concat([datos_existentes['TODOS'], df_nuevos], ignore_index=True)
    df_todos = df_todos.drop_duplicates(subset=['Hora_Llegada', 'Bandera']).reset_index(drop=True)
    df_todos = df_todos.sort_values('Minutos')
    
    # 215
    nuevos_215 = [h for h in horarios_nuevos if '215' in h.get('Bandera', '')]
    df_nuevos_215 = pd.DataFrame(nuevos_215)
    df_215 = pd.concat([datos_existentes['215'], df_nuevos_215], ignore_index=True)
    df_215 = df_215.drop_duplicates(subset=['Hora_Llegada', 'Bandera']).reset_index(drop=True)
    df_215 = df_215.sort_values('Minutos')
    
    # COMBINADAS (todos ordenados por minutos)
    df_combinadas = df_todos.copy()
    
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        # Escribir datos sin startrow (desde fila 1)
        df_todos.to_excel(writer, sheet_name='TODOS', index=False)
        df_215.to_excel(writer, sheet_name='215', index=False)
        df_combinadas.to_excel(writer, sheet_name='COMBINADAS', index=False)

    print(f"💾 Excel actualizado: {archivo_hoy}")
    print(f"   TODOS: {len(df_todos)} filas únicas")
    print(f"   215: {len(df_215)} filas únicas")
    print(f"   COMBINADAS: {len(df_combinadas)} filas únicas")

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_json.py input.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    arrivals = parse_arrivals(json_file)
    
    print(f"📊 {len(arrivals)} horarios parseados")
    print(f"🚐 {len([a for a in arrivals if '215' in a['Bandera']])} buses 215 encontrados")
    
    guardar_excel_dia(arrivals)
    
    print("🎉 Recolector COMPLETO: Excel acumulativo cada 10min")

if __name__ == "__main__":
    main()
