import cdsapi

dataset = "reanalysis-era5-land"
# Vamos a intentar bajarlo en bloques de un año, pero con menos horas
years = ["2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"]

client = cdsapi.Client()

for year in years:
    print(f"Downloading year: {year}...")
    target_file = f"soil_water_{year}.nc"
    
    request = {
        "variable": ["volumetric_soil_water_layer_1"],
        "year": [year],
        "month": [f"{i:02d}" for i in range(1, 13)],
        "day": [f"{i:02d}" for i in range(1, 32)],
        "time": ["00:00", "06:00", "12:00", "18:00"], # 4 datos al día en lugar de 24
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [18.54, -96.23, 17.77, -95.67]
    }

    try:
        client.retrieve(dataset, request).download(target_file)
        print('Finalized: {target_file}")
    except Exception as e:
        print('Error')

print("Process completed")
