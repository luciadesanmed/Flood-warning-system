import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.colors as mcolors
import pandas as pd
from pathlib import Path
from scipy import stats

# Data path
hydro_path = Path("/home/desan/hidro-papaloapan/")
hydro_dat = hydro_path / 'PAPOX.csv'
meteo_path = Path("/home/desan/meteo-papaloapan/")
meteo_dat = meteo_path / 'PAPOX.csv'

#Flood events (determined with news articles):
events = ('2008-09-26', '2010-09-06', '2017-10-06', '2018-10-23', '2020-09-05', '2020-09-22',
          '2022-09-16', '2024-10-20', '2024-10-21', '2024-10-22', '2024-10-23', '2024-10-24',
          '2024-10-25', '2024-10-26', '2024-10-27', '2024-10-28', '2024-10-29', '2025-08-07',
          '2021-08-28')

#Precipitation data:
dm = pd.read_csv(meteo_dat, skiprows=8, usecols=[1, 2])
dm.columns = ['Fecha', 'Precipitacion(mm)']
#Convert to datetime:
dm['Fecha'] = pd.to_datetime(dm['Fecha'], dayfirst=True, format='mixed')
dm['Precipitacion(mm)'] = pd.to_numeric(dm['Precipitacion(mm)'], errors='coerce')
#Data cleaning:
#Data cleaning:
dm = dm.dropna(subset=['Precipitacion(mm)'])

#Hydrological data:
dh = pd.read_csv(hydro_dat, skiprows=8, usecols=[0, 1])
dh.columns = ['Fecha', 'Nivel(m)']

#Convert to datetime objects
dh['Fecha'] = pd.to_datetime(dh['Fecha'], dayfirst=True)
dh['Nivel(m)'] = pd.to_numeric(dh['Nivel(m)'], errors='coerce')

#Data cleaning:
dh = dh.dropna(subset=['Nivel(m)'])
#Removing outliers:
# Calculate the 'Middle 50%' of the data
Q1 = dh['Nivel(m)'].quantile(0.25)
Q3 = dh['Nivel(m)'].quantile(0.75)
IQR = Q3 - Q1

# Define bounds (1.5 is standard, use 1.1 for stricter cleaning)
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Filter the data
dh = dh[(dh['Nivel(m)'] >= lower_bound) & (dh['Nivel(m)'] <= upper_bound)]

# y min and max
ymin = float(dh['Nivel(m)'].min())
ymax = float(dh['Nivel(m)'].max())
#y_min = 4.0
ymax = 12.0
# Define limits as datetime objects
xmin = pd.to_datetime('2017-01-01')
xmax = pd.to_datetime('2025-09-1')

fig, ax1 = plt.subplots(figsize=(12, 6))
for d in events:
    plt.axvline(pd.to_datetime(d), color='green', alpha=0.8, linestyle=':', linewidth=1.5)
ax1.plot(dh['Fecha'], dh['Nivel(m)'], linestyle='-', color='b')
#ax1.title('Water level')
ax1.set_xlabel('Date')
ax1.set_ylabel('Water level (m)')
#plt.grid(True, linestyle='--', alpha=0.7)
ax1.set_ylim(ymin,ymax)
ax1.set_yticks(np.linspace(ymin, ymax, 10))
#ax1.set_xticks(rotation=45)
ax1.set_xlim(xmin, xmax)

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Precipitation (mm/day)', color=color2)
ax2.plot(dm['Fecha'], dm['Precipitacion(mm)'], linestyle='-', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_xlim(xmin, xmax)

#plt.tight_layout()
plt.show()

#Anomaly plots:
#Mean from the time i am considering, this is not a climatology:
# 3. Filter and calculate mean
mask = (dh['Fecha'] >= xmin) & (dh['Fecha'] <= xmax)
hydro_mean = dh.loc[mask, 'Nivel(m)'].mean()
mask = (dm['Fecha'] >= xmin) & (dm['Fecha'] <= xmax)
prec_mean = dm.loc[mask, 'Precipitacion(mm)'].mean()

#Anomaly plots:
fig, ax1 = plt.subplots(figsize=(12, 6))
for d in events:
    plt.axvline(pd.to_datetime(d), color='green', alpha=0.8, linestyle=':', linewidth=1.5)
ax1.plot(dh['Fecha'], dh['Nivel(m)'] - hydro_mean, linestyle='-', color='b')
#ax1.title('Water level')
ax1.set_xlabel('Date')
ax1.set_ylabel('Water level (m)')
#plt.grid(True, linestyle='--', alpha=0.7)
#ax1.set_ylim(y_min,y_max)
#ax1.set_yticks(np.linspace(ymin, ymax, 10))
#ax1.set_xticks(rotation=45)
ax1.set_xlim(xmin, xmax)

ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Precipitation (mm/day)', color=color2)
ax2.plot(dm['Fecha'], dm['Precipitacion(mm)'] - prec_mean, linestyle='-', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_xlim(xmin, xmax)

#plt.tight_layout()
plt.show()
