import os
from flask import Flask, render_template, request
import csv
import pandas as pd
from flask_caching import Cache
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from waitress import serve

app = Flask(__name__)
app.secret_key = 'camilo123'

# Configuración de Flask-Caching
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Rutas dinámicas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'static/archivo')
RUTA_CSV = os.path.join(DATA_DIR, 'data.csv')

FILES = {
    "Wind": ("08 wind-generation.csv", "Electricity from wind (TWh)"),
    "Solar": ("12 solar-energy-consumption.csv", "Electricity from solar (TWh)"),
    "Hidropower": ("05 hydropower-consumption.csv", "Electricity from hydro (TWh)"),
    "Biofuels": ("16 biofuel-production.csv", "Biofuels Production - TWh - Total"),
    "Geothermal": ("17 installed-geothermal-capacity.csv", "Geothermal Capacity")
}

datos_globales = {}
datos_cargados = False

def cargar_datos_renovables(ruta_csv):
    try:
        with open(ruta_csv, mode='r', encoding='utf-8') as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            return [
                {
                    'entity': fila['Entity'],
                    'code': fila['Code'],
                    'year': int(fila['Year']),
                    'renewables': float(fila['Renewables (% equivalent primary energy)'])
                } for fila in lector
            ]
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return []

def cargar_datos():
    global datos_globales, datos_cargados
    if not datos_cargados:
        datos_globales['renovables'] = cargar_datos_renovables(RUTA_CSV)
        for key, (file_name, column) in FILES.items():
            file_path = os.path.join(DATA_DIR, file_name)
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df[column] = pd.to_numeric(df[column], errors='coerce').fillna(0)
                datos_globales[key] = df[column].sum()
        datos_cargados = True

def generar_grafico(figura, formato='png'):
    img = BytesIO()
    plt.tight_layout()
    figura.savefig(img, format=formato)
    img.seek(0)
    plt.close(figura)
    return base64.b64encode(img.getvalue()).decode('utf-8')

@cache.memoize(timeout=300)
def obtener_grafico_barras():
    data = {key: value for key, value in datos_globales.items() if isinstance(value, (int, float))}
    df = pd.DataFrame(list(data.items()), columns=['Fuente', 'Producción (TWh)'])

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(df['Fuente'], df['Producción (TWh)'], color=['blue', 'orange', 'green', 'red', 'purple'][:len(df)])
    ax.set_title('Producción de Energía Renovable por Fuente', fontsize=12)
    ax.set_xlabel('Fuente de Energía', fontsize=12)
    ax.set_ylabel('Producción (TWh)', fontsize=12)
    
    return generar_grafico(fig)

@cache.memoize(timeout=300)
def obtener_grafico_pastel():
    df_renewables = pd.read_csv(os.path.join(DATA_DIR, '04 share-electricity-renewables.csv'))
    df_wind = pd.read_csv(os.path.join(DATA_DIR, '11 share-electricity-wind.csv'))
    df_solar = pd.read_csv(os.path.join(DATA_DIR, '15 share-electricity-solar.csv'))
    df_hydro = pd.read_csv(os.path.join(DATA_DIR, '07 share-electricity-hydro.csv'))

    year = df_renewables['Year'].max()
    wind_data = df_wind[df_wind['Year'] == year]
    solar_data = df_solar[df_solar['Year'] == year]
    hydro_data = df_hydro[df_hydro['Year'] == year]

    wind_percentage = wind_data['Wind (% electricity)'].iloc[0] if 'Wind (% electricity)' in wind_data else 0
    solar_percentage = solar_data['Solar (% electricity)'].iloc[0] if 'Solar (% electricity)' in solar_data else 0
    hydro_percentage = hydro_data['Hydro (% electricity)'].iloc[0] if 'Hydro (% electricity)' in hydro_data else 0

    data_pie = {
        'Energia Renovable': ['Eólica', 'Solar', 'Hidroeléctrica'],
        'Participacion': [wind_percentage, solar_percentage, hydro_percentage]
    }
    df_graph = pd.DataFrame(data_pie)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(df_graph['Participacion'], labels=df_graph['Energia Renovable'], autopct='%1.1f%%', startangle=90, colors=['skyblue', 'gold', 'lightgreen'])
    ax.set_title('Participación de Energías Renovables', fontsize=14)
    ax.axis('equal')
    
    return generar_grafico(fig)

@cache.memoize(timeout=300)
def obtener_grafico_lineas():
    """Genera el gráfico de líneas de capacidad instalada de energía eólica vs solar."""
    wind_data = pd.read_csv(os.path.join(DATA_DIR, '09 cumulative-installed-wind-energy-capacity-gigawatts.csv'))
    solar_data = pd.read_csv(os.path.join(DATA_DIR, '13 installed-solar-PV-capacity.csv'))

    wind_data = wind_data[['Year', 'Wind Capacity']].dropna()
    solar_data = solar_data[['Year', 'Solar Capacity']].dropna()

    wind_data['Year'] = pd.to_numeric(wind_data['Year'], errors='coerce')
    solar_data['Year'] = pd.to_numeric(solar_data['Year'], errors='coerce')

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(wind_data['Year'], wind_data['Wind Capacity'], label='Capacidad Eólica', color='blue', marker='o')
    ax.plot(solar_data['Year'], solar_data['Solar Capacity'], label='Capacidad Solar', color='orange', marker='x')

    ax.set_title('Tendencias en la Capacidad Instalada (Eólica vs Solar)')
    ax.set_xlabel('Año')
    ax.set_ylabel('Capacidad Instalada (Gigawatts)')
    ax.legend()
    ax.grid(True)

    return generar_grafico(fig)

@cache.memoize(timeout=300)
def obtener_grafica_area():
    renewable_data = pd.read_csv('static/archivo/02 modern-renewable-energy-consumption.csv')

    renewable_data = renewable_data[renewable_data['Entity'] == 'World']

    renewable_data['Total Renewable Energy'] = (
        renewable_data['Geo Biomass Other - TWh'] +
        renewable_data['Solar Generation - TWh'] +
        renewable_data['Wind Generation - TWh'] +
        renewable_data['Hydro Generation - TWh']
    )

    fig, ax = plt.subplots(figsize=(6, 5))

    ax.fill_between(renewable_data['Year'], renewable_data['Total Renewable Energy'], color='green', alpha=0.5, label='Energía Renovable')

    conventional_data = pd.DataFrame({
        'Year': renewable_data['Year'],
        'Total Conventional Energy': [1000] * len(renewable_data['Year'])
    })

    ax.fill_between(conventional_data['Year'], conventional_data['Total Conventional Energy'], color='red', alpha=0.5, label='Energía Convencional')

    ax.set_title('Comparación entre Consumo de Energía Renovable y Convencional', fontsize=10)
    ax.set_xlabel('Año', fontsize=12)
    ax.set_ylabel('Consumo de Energía (TWh)', fontsize=12)

    ax.legend(loc='upper left')

    return generar_grafico(fig)

@cache.memoize(timeout=300)
def cargar_archivo():
    data = []
    try:
        with open('static/archivo/data_pagina.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Saltar encabezado
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    cargar_datos()

    porcentaje_renovable = None
    error = None

    if request.method == 'POST':
        try:
            consumo_total = float(request.form['consumo_total'])
            if consumo_total <= 0:
                error = "El consumo total debe ser un valor positivo."
            else:
                produccion_total_renovable = sum(energia['renewables'] for energia in datos_globales['renovables'])
                porcentaje_renovable = min((consumo_total / produccion_total_renovable) * 100, 100)
        except ValueError:
            error = "Por favor ingrese un valor válido para el consumo total."

    # Generación de gráficos y carga de tabla
    graph_url = obtener_grafico_barras()
    graph_url2 = obtener_grafico_pastel()
    graph_url3 = obtener_grafico_lineas()
    graph_url4 = obtener_grafica_area()
    archivo_data = cargar_archivo()


    return render_template('index.html', porcentaje_renovable=porcentaje_renovable, error=error,graph_url=graph_url, graph_url2=graph_url2, graph_url3=graph_url3, graph_url4=graph_url4, data=archivo_data)

if __name__ == '__main__':
    if os.getenv('RENDER_ENV') == 'true':
        print("Running on Render")
        serve(app, host='0.0.0.0', port=5000)
    else:
        print("Running locally")
        app.run(debug=True, host='0.0.0.0', port=5000)