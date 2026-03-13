import xarray as xr
import pandas as pd
import glob
import os

# --- RUTA ---
carpeta_datos = "/home/desan/soil-data/" 
patron_busqueda = os.path.join(carpeta_datos, "soil_water_*.nc")
archivos = sorted(glob.glob(patron_busqueda))

if not archivos:
    print(f"❌ No se encontraron archivos en: {carpeta_datos}")
else:
    print(f"✅ Archivos encontrados: {len(archivos)}")
    
    # Abrir archivos (ERA5-Land suele usar 'swvl1' como nombre de variable)
    ds = xr.open_mfdataset(archivos, combine='by_coords')

    # 1. Normalizar dimensión de tiempo
    if 'valid_time' in ds.coords:
        ds = ds.rename({'valid_time': 'time'})
    
    # 2. Manejo de 'expver' (Datos provisionales vs consolidados)
    if 'expver' in ds.dims:
        print("Fusionando dimensiones 'expver'...")
        ds = ds.sel(expver=1).combine_first(ds.sel(expver=5))

    # 3. Ajuste de Huso Horario (UTC a México -6)
    ds['time'] = ds['time'] - pd.Timedelta(hours=6)

    # 4. PROMEDIO DIARIO (Para cada píxel de la región)
    # Esto reduce las horas a días, pero mantiene la malla de 48 puntos
    ds_daily = ds.resample(time='D').mean()

    # 5. PROMEDIO REGIONAL (Espacial)
    # Colapsamos latitud y longitud promediando todos los puntos
    # Usamos 'swvl1' que es el nombre interno de la variable de humedad
    region_mean = ds_daily['swvl1'].mean(dim=['latitude', 'longitude'])

    # 6. Guardar resultados
    # Convertir a DataFrame para exportar a CSV
    df_regional = region_mean.to_dataframe(name='soil_moisture_avg')
    
    # Limpiar columnas extras si existen (como 'expver' o 'number')
    columnas_extra = [c for c in ['number', 'expver'] if c in df_regional.columns]
    df_regional = df_regional.drop(columnas_extra, axis=1)

    csv_output = os.path.join(carpeta_datos, "humedad_regional_diaria.csv")
    df_regional.to_csv(csv_output)
    
    print(f"\n✅ Promedio regional guardado en: {csv_output}")
    print(f"📊 Total de días procesados: {len(df_regional)}")
