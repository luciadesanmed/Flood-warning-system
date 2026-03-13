import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

#COMPARE WITH PRECIPITATION IN CDOOX UPSTREAM YEAH BOIII

# --- TUS RUTAS Y CARGA DE DATOS (Manteniendo tu estructura) ---
hydro_path = Path("/home/desan/hidro-papaloapan/")
hydro_dat = hydro_path / 'PAPOX.csv'
meteo_path = Path("/home/desan/meteo-papaloapan/")
meteo_dat = meteo_path / 'PAPOX.csv'
# Ruta del archivo de suelo que generamos
soil_path = Path("/home/desan/soil-data/humedad_regional_diaria.csv")

events = ('2008-09-26', '2010-09-06', '2017-10-06', '2018-10-23', '2020-09-05', '2020-09-22',
          '2022-09-16', '2024-10-20', '2024-10-21', '2024-10-22', '2024-10-23', '2024-10-24',
          '2024-10-25', '2024-10-26', '2024-10-27', '2024-10-28', '2024-10-29', '2025-08-07',
          '2021-08-28')

# Procesamiento de Precipitación (dm)
dm = pd.read_csv(meteo_dat, skiprows=8, usecols=[1, 2])
dm.columns = ['Fecha', 'Precipitacion(mm)']
dm['Fecha'] = pd.to_datetime(dm['Fecha'], dayfirst=True, format='mixed')
dm['Precipitacion(mm)'] = pd.to_numeric(dm['Precipitacion(mm)'], errors='coerce')
dm = dm.dropna(subset=['Precipitacion(mm)'])

# Procesamiento de Hidrología (dh)
dh = pd.read_csv(hydro_dat, skiprows=8, usecols=[0, 1])
dh.columns = ['Fecha', 'Nivel(m)']
dh['Fecha'] = pd.to_datetime(dh['Fecha'], dayfirst=True)
dh['Nivel(m)'] = pd.to_numeric(dh['Nivel(m)'], errors='coerce')
dh = dh.dropna(subset=['Nivel(m)'])

# Limpieza de outliers y límites (Tus valores)
Q1, Q3 = dh['Nivel(m)'].quantile(0.25), dh['Nivel(m)'].quantile(0.75)
IQR = Q3 - Q1
dh = dh[(dh['Nivel(m)'] >= Q1 - 1.5 * IQR) & (dh['Nivel(m)'] <= Q3 + 1.5 * IQR)]

ymin, ymax = float(dh['Nivel(m)'].min()), 12.0
xmin, xmax = pd.to_datetime('2017-01-01'), pd.to_datetime('2025-09-01')

# Carga de Suelo (ds_s) - Usamos el nombre de columna 'soil_moisture_avg' del paso anterior
ds_s = pd.read_csv(soil_path, parse_dates=['time'], index_col='time')
umbral_saturacion = 0.40

# --- GRÁFICA CON SUBPLOTS ---
fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# SUBPLOT 1: NIVEL (Azul) Y PRECIPITACIÓN (Rojo)
ax_top.plot(dh['Fecha'], dh['Nivel(m)'], color='b', label='Nivel del Agua')
ax_top.set_ylabel('Water level (m)', color='b', fontweight='bold')
ax_top.set_ylim(ymin, ymax)

ax_prec1 = ax_top.twinx()
ax_prec1.plot(dm['Fecha'], dm['Precipitacion(mm)'], color='tab:red', alpha=0.7, label='Precipitación')
ax_prec1.set_ylabel('Precipitation (mm/day)', color='tab:red', fontweight='bold')

# SUBPLOT 2: SOIL MOISTURE (Verde) Y PRECIPITACIÓN (Rojo)
ax_bot.plot(ds_s.index, ds_s['soil_moisture_avg'], color='g', linewidth=1.5, label='Soil Moisture')
ax_bot.set_ylabel('Soil Moisture (m³/m³)', color='g', fontweight='bold')

# Sombreado de saturación
#ax_bot.fill_between(ds_s.index, 0, 1, where=(ds_s['soil_moisture_avg'] >= umbral_saturacion),
#                    color='orange', alpha=0.3, transform=ax_bot.get_xaxis_transform(), label='Saturación')
ax_bot.axhline(y=umbral_saturacion, color='r', linestyle='--', linewidth=2, label=f'Saturación ({umbral_saturacion})')
ax_prec2 = ax_bot.twinx()
ax_prec2.plot(dh['Fecha'], dh['Nivel(m)'], color='tab:blue', alpha=0.5)
ax_prec2.set_ylabel('Water level (m)', color='tab:blue', fontweight='bold')

# --- ELEMENTOS COMUNES: LÍNEAS DE EVENTOS ---
for ax in [ax_top, ax_bot]:
    for d in events:
        ax.axvline(pd.to_datetime(d), color='green', alpha=0.6, linestyle=':', linewidth=1)
    ax.set_xlim(xmin, xmax)
    ax.grid(True, linestyle='--', alpha=0.3)

ax_bot.set_xlabel('Date')
ax_top.set_title('Análisis Hidrometeorológico y Humedad del Suelo')

plt.tight_layout()
plt.show()

# 1. Preparar los datos para la correlación
# Necesitamos que todos los DataFrames usen la fecha como índice para alinearlos
df_prec_corr = dm.set_index('Fecha')[['Precipitacion(mm)']]
df_nivel_corr = dh.set_index('Fecha')[['Nivel(m)']]
# df_suelo ya tiene 'time' como índice del paso anterior (asegúrate que el nombre coincida)
df_suelo_corr = ds_s[['soil_moisture_avg']]

# 2. Unificar las 3 series en un solo DataFrame alineado por fecha
# Usamos 'inner' join para considerar solo los días que tienen datos en las 3 estaciones
df_total = df_prec_corr.join([df_nivel_corr, df_suelo_corr], how='inner')

# 3. Calcular la matriz de correlación
matriz_corr = df_total.corr()

print("\n--- MATRIZ DE CORRELACIÓN ---")
print(matriz_corr)

# 4. Mostrar correlaciones específicas de forma legible
print(f"\nCorrelación Lluvia vs Nivel: {matriz_corr.loc['Precipitacion(mm)', 'Nivel(m)']: .3f}")
print(f"Correlación Lluvia vs Humedad: {matriz_corr.loc['Precipitacion(mm)', 'soil_moisture_avg']: .3f}")
print(f"Correlación Humedad vs Nivel: {matriz_corr.loc['soil_moisture_avg', 'Nivel(m)']: .3f}")

# 1. Asegurar alineación (usando el DataFrame unificado anterior)
# Si no has corrido el bloque anterior, aquí lo unificamos rápido:
df_total = dm.set_index('Fecha').join([dh.set_index('Fecha'), ds_s], how='inner')

# 2. Función para encontrar el máximo retraso
def calcular_mejor_lag(df, col_causa, col_efecto, max_dias=10):
    correlaciones = {}
    for lag in range(max_dias + 1):
        # Desplazamos la lluvia 'lag' días hacia adelante
        corr = df[col_causa].shift(lag).corr(df[col_efecto])
        correlaciones[lag] = corr
    
    mejor_lag = max(correlaciones, key=correlaciones.get)
    return mejor_lag, correlaciones[mejor_lag], correlaciones

# 3. Calcular para Nivel y para Humedad
lag_nivel, corr_nivel, lista_n = calcular_mejor_lag(df_total, 'Precipitacion(mm)', 'Nivel(m)')
lag_suelo, corr_suelo, lista_s = calcular_mejor_lag(df_total, 'Precipitacion(mm)', 'soil_moisture_avg')

print("--- ANÁLISIS DE LAG TIME (RETRASO) ---")
print(f"🌊 El río tarda {lag_nivel} días en alcanzar su correlación máxima ({corr_nivel:.3f}) tras la lluvia.")
print(f"🌱 El suelo tarda {lag_suelo} días en alcanzar su correlación máxima ({corr_suelo:.3f}) tras la lluvia.")

# 4. Graficar la ventana de correlación para ver el pico
plt.figure(figsize=(10, 5))
plt.plot(list(lista_n.keys()), list(lista_n.values()), marker='o', label='Lluvia vs Nivel')
plt.plot(list(lista_s.keys()), list(lista_s.values()), marker='s', label='Lluvia vs Humedad')
plt.axvline(lag_nivel, color='blue', linestyle='--', alpha=0.5)
plt.title('Determinación del Lag Time (Pico de Correlación)')
plt.xlabel('Días de retraso (Shift)')
plt.ylabel('Coeficiente de Correlación (Pearson)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# 1. Alineamos los datos en un solo DataFrame
df_all = dm.set_index('Fecha').join([dh.set_index('Fecha'), ds_s], how='inner')

# 2. Definimos la función para extraer ventanas de eventos
def correlacion_en_eventos(df, lista_eventos, ventana_dias=5):
    fragmentos = []
    
    for fecha_str in lista_eventos:
        fecha = pd.to_datetime(fecha_str)
        inicio = fecha - pd.Timedelta(days=ventana_dias)
        fin = fecha + pd.Timedelta(days=ventana_dias)
        
        # Extraemos el pedazo de datos de esa fecha
        pedazo = df.loc[inicio:fin]
        fragmentos.append(pedazo)
    
    # Concatenamos todos los eventos en un solo "super dataset" de crisis
    df_eventos = pd.concat(fragmentos)
    return df_eventos.corr(), df_eventos

# 3. Calculamos la correlación específica de eventos
matriz_eventos, df_solo_eventos = correlacion_en_eventos(df_all, events)

print("--- CORRELACIÓN EN VENTANAS DE EVENTOS (±5 días) ---")
print(matriz_eventos)

# Comparativa
c_nivel = matriz_eventos.loc['Precipitacion(mm)', 'Nivel(m)']
c_suelo = matriz_eventos.loc['Precipitacion(mm)', 'soil_moisture_avg']

print(f"\n💡 Durante inundaciones:")
print(f"La correlación Lluvia-Nivel subió a: {c_nivel:.3f}")
print(f"La correlación Lluvia-Suelo subió a: {c_suelo:.3f}")

# 1. Alineamos los datos en un solo DataFrame (usando tus variables dm, dh y ds_s)
# Asegúrate de que ds_s tenga el índice llamado 'time' o cámbialo a 'Fecha' para que coincida
if 'Fecha' not in ds_s.columns and ds_s.index.name != 'Fecha':
    ds_s.index.name = 'Fecha'

df_all = dm.set_index('Fecha').join([dh.set_index('Fecha'), ds_s], how='inner')

# 2. Función con ventana asimétrica (-10, +3)
def correlacion_ventana_critica(df, lista_eventos):
    fragmentos = []
    
    for fecha_str in lista_eventos:
        fecha = pd.to_datetime(fecha_str)
        # 10 días antes para ver la acumulación
        inicio = fecha - pd.Timedelta(days=10)
        # 3 días después para ver el pico del río
        fin = fecha + pd.Timedelta(days=3)
        
        # Extraer datos si existen en el rango
        pedazo = df.loc[inicio:fin]
        if not pedazo.empty:
            fragmentos.append(pedazo)
    
    # Unificamos todos los periodos de crisis
    df_crisis = pd.concat(fragmentos)
    return df_crisis.corr(), df_crisis

# 3. Cálculo de la matriz
matriz_crisis, df_estres = correlacion_ventana_critica(df_all, events)

print("--- MATRIZ EN VENTANA CRÍTICA (-10 a +3 días) ---")
print(matriz_crisis)

# Extracción de valores clave
c_lluvia_nivel = matriz_crisis.loc['Precipitacion(mm)', 'Nivel(m)']
c_suelo_nivel = matriz_crisis.loc['soil_moisture_avg', 'Nivel(m)']

print(f"\n📊 Análisis de Crisis en PAPOX:")
print(f"Correlación Lluvia -> Nivel: {c_lluvia_nivel:.3f}")
print(f"Correlación Suelo -> Nivel: {c_suelo_nivel:.3f}")

# Cambia .corr() por .corr(method='spearman')
matriz_spearman = df_estres.corr(method='spearman')

print("--- CORRELACIÓN DE SPEARMAN (No lineal) ---")
print(matriz_spearman)

# Compara los resultados
print(f"Pearson (Lineal): {matriz_crisis.loc['Precipitacion(mm)', 'Nivel(m)']: .3f}")
print(f"Spearman (No Lineal): {matriz_spearman.loc['Precipitacion(mm)', 'Nivel(m)']: .3f}")

# --- NUEVA SECCIÓN: SUAVIZADO DE SERIES (ROLLING MEAN) ---

# 1. Creamos versiones suavizadas en nuestro dataframe unificado (df_all)
# Usamos una ventana de 7 días para la lluvia (acumulación semanal)
df_all['precip_smooth'] = df_all['Precipitacion(mm)'].rolling(window=7, center=False).mean()

# Usamos una ventana de 3 días para el nivel (inercia del río)
df_all['nivel_smooth'] = df_all['Nivel(m)'].rolling(window=3, center=True).mean()

# Usamos una ventana de 5 días para el suelo
df_all['suelo_smooth'] = df_all['soil_moisture_avg'].rolling(window=5, center=True).mean()

# 2. Recalcular la correlación en la ventana crítica con datos suavizados
# (Usando tu lógica de -10 a +3 días)
fragmentos_smooth = []
for fecha_str in events:
    fecha = pd.to_datetime(fecha_str)
    inicio, fin = fecha - pd.Timedelta(days=10), fecha + pd.Timedelta(days=3)
    pedazo = df_all.loc[inicio:fin]
    if not pedazo.empty:
        fragmentos_smooth.append(pedazo)

df_estres_smooth = pd.concat(fragmentos_smooth).dropna() # dropna es clave tras el rolling

# 3. Comparar correlaciones
matriz_raw = df_estres_smooth[['Precipitacion(mm)', 'Nivel(m)', 'soil_moisture_avg']].corr()
matriz_smooth = df_estres_smooth[['precip_smooth', 'nivel_smooth', 'suelo_smooth']].corr()

print("--- COMPARATIVA DE CORRELACIÓN (Pearson) ---")
print(f"Lluvia vs Nivel (Original):  {matriz_raw.loc['Precipitacion(mm)', 'Nivel(m)']: .3f}")
print(f"Lluvia vs Nivel (Suavizada): {matriz_smooth.loc['precip_smooth', 'nivel_smooth']: .3f}")
print("-" * 40)
print(f"Suelo vs Nivel (Original):   {matriz_raw.loc['soil_moisture_avg', 'Nivel(m)']: .3f}")
print(f"Suelo vs Nivel (Suavizada):  {matriz_smooth.loc['suelo_smooth', 'nivel_smooth']: .3f}")

# --- SECCIÓN: PLOTEO DE SERIES SUAVIZADAS ---

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

# --- SUBPLOT 1: NIVEL Y PRECIPITACIÓN ---
# Nivel (Original en azul claro, Suavizado en azul fuerte)
ax_top.plot(df_all.index, df_all['Nivel(m)'], color='tab:blue', alpha=0.3, label='Nivel Original')
ax_top.plot(df_all.index, df_all['nivel_smooth'], color='blue', linewidth=2, label='Nivel Suavizado (3d)')
ax_top.set_ylabel('Water Level (m)', color='blue', fontweight='bold')
ax_top.set_ylim(ymin, ymax)

# Precipitación (Original en rojo claro, Suavizada en rojo fuerte)
ax_prec1 = ax_top.twinx()
ax_prec1.plot(df_all.index, df_all['Precipitacion(mm)'], color='tab:red', alpha=0.2)
ax_prec1.plot(df_all.index, df_all['precip_smooth'], color='red', linewidth=1.5, label='Lluvia Suavizada (7d)')
ax_prec1.set_ylabel('Precipitation (mm/day)', color='red', fontweight='bold')

# --- SUBPLOT 2: HUMEDAD Y PRECIPITACIÓN ---
# Suelo (Original en verde claro, Suavizado en verde fuerte)
ax_bot.plot(df_all.index, df_all['soil_moisture_avg'], color='tab:green', alpha=0.3)
ax_bot.plot(df_all.index, df_all['suelo_smooth'], color='green', linewidth=2, label='Humedad Suavizada (5d)')
ax_bot.set_ylabel('Soil Moisture (m³/m³)', color='green', fontweight='bold')

# Línea de saturación y sombreado sobre la serie suavizada
ax_bot.axhline(y=umbral_saturacion, color='darkred', linestyle='--', linewidth=2, label='Umbral Saturación')
ax_bot.fill_between(df_all.index, 0, 1, where=(df_all['suelo_smooth'] >= umbral_saturacion),
                    color='orange', alpha=0.3, transform=ax_bot.get_xaxis_transform(), label='Zona Crítica')

ax_prec2 = ax_bot.twinx()
ax_prec2.plot(df_all.index, df_all['nivel_smooth'], color='tab:blue', alpha=0.6)
ax_prec2.set_ylabel('Level (m)', color='blue', fontweight='bold')

# --- ELEMENTOS COMUNES (Líneas de eventos y límites) ---
for ax in [ax_top, ax_bot]:
    for d in events:
        ax.axvline(pd.to_datetime(d), color='black', alpha=0.5, linestyle=':', linewidth=1)
    ax.set_xlim(xmin, xmax)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', fontsize='small')

ax_bot.set_xlabel('Date')
ax_top.set_title('Comparativa de Series Suavizadas vs Originales en Eventos Críticos')

plt.tight_layout()
plt.show()
