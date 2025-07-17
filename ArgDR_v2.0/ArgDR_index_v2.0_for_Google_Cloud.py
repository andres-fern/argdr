# %%
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
import sqlite3
from google.cloud import secretmanager
from google.auth import default
from google.cloud import bigquery
from datetime import datetime

# %%
# Access the API key

def access_secret(secret_id, project_id):
    """
    Retrieve a secret from Google Cloud Secret Manager.
    
    Args:
        secret_id (str): The ID of the secret to retrieve
        project_id (str): Your Google Cloud project ID
    
    Returns:
        str: The secret value
    """
    
    credentials, project_id = default()
    client = secretmanager.SecretManagerServiceClient(credentials=credentials)

    try:
        # Explicitly get credentials
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Return the decoded secret
        return response.payload.data.decode('UTF-8')
    
    except Exception as e:
        print(f"Error accessing secret: {e}")
        return None

api_key = access_secret(secret_id="ALPHAVANTAGE_API_KEY",project_id="562376856357")

# %%
tickers_dict = {
    'YPF Sociedad Anonima' : 'YPF',
    'Grupo Supervielle' : 'SUPV',
    'Grupo Financiero Galicia ADR' : 'GGAL',
    'BBVA Argentina' : 'BBAR',
    'Banco Macro B ADR' : 'BMA',
    'Telecom Argentina ADR' : 'TEO',
    'Cresud SACIF' : 'CRESY',
    'Central Puerto' : 'CEPU',
    'Pampa Energia ADR' : 'PAM',
    'Loma Negra ADR' : 'LOMA',
    'IRSA ADR' : 'IRS',
    'Transportadora Gas ADR' : 'TGS',
    'Bioceres Crop' : 'BIOX',
    'Edenor ADR' : 'EDN'
}


# %%
tickers_list = list(tickers_dict.values())

# %%
cap_bursatiles_25_feb_25 = {
    'YPF Sociedad Anonima' :            13946871640,
    'Grupo Supervielle' :               1233150264,
    'Grupo Financiero Galicia ADR' :    8523720280,
    'BBVA Argentina' :                  3843734562,
    'Banco Macro B ADR' :               5493200605,
    'Telecom Argentina ADR' :           5272228248,
    'Cresud SACIF' :                    633031172,
    'Central Puerto' :                  1881929669,
    'Pampa Energia ADR' :               4208906073,
    'Loma Negra ADR' :                  1295332593,
    'IRSA ADR' :                        1042296329,
    'Transportadora Gas ADR' :          3894785724,
    'Bioceres Crop' :                   276407628,
    'Edenor ADR' :                      1623461084
}

cap_bursatiles_16_jul_25 = {
    'YPF Sociedad Anonima' :            12102234641,         
    'Grupo Supervielle' :               889238357,                  
    'Grupo Financiero Galicia ADR' :    7465867337,                 
    'BBVA Argentina' :                  3005342937,                    
    'Banco Macro B ADR' :               4078498436,                    
    'Telecom Argentina ADR' :           3848640474,                    
    'Cresud SACIF' :                    644063746,                    
    'Central Puerto' :                  1712056372,                    
    'Pampa Energia ADR' :               3840171311,                    
    'Loma Negra ADR' :                  1220646750,                    
    'IRSA ADR' :                        1086066840,                    
    'Transportadora Gas ADR' :          3863169760,                    
    'Bioceres Crop' :                   240709690,                   
    'Edenor ADR' :                      1112447021                    
}



# Seleccionar el diccionario más reciente de 
# capitalizaciones bursátiles
cap_bursatiles = cap_bursatiles_16_jul_25

suma_cap = sum(cap_bursatiles.values())

firmas_y_pond = []

for i in cap_bursatiles:
    firmas_y_pond.append([i, (cap_bursatiles[i]/suma_cap)])

ponderadores = dict(firmas_y_pond)

# %%
tickers_y_ponderadores = {tickers_dict[nombre_empresa]:ponderador for (nombre_empresa,ponderador) in ponderadores.items()}

# %%
tickers_y_ponderadores

# %%
# Este script "hereda" el ajuste de encadenamiento
# a fecha febrero de 2025 del script 'ArgDR_index_v1.0.ipynb'
chain_adjustment_feb_25 = 0.911886396417253
# Update 2025-07-17: al haber nuevos ponderadores, se actualiza
# el chain adjustment (ver reponderación en:
# https://github.com/andres-fern/argdr/blob/main/ArgDR_v2.0/ArgDR_index_v2.0_for_Google_Cloud.ipynb)
chain_adjustment_jul_25 = 0.9087699742721543

# %%
def get_data_from_api(ticker:str, function='TIME_SERIES_INTRADAY'):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": ticker,
        "interval": "60min",
        "apikey": api_key,
        "extended_hours": "false"
    }
    response = requests.get(base_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# %%
def get_date_and_latest_price(ticker:str):
    api_data = get_data_from_api(ticker)
    date_and_price = list(api_data['Time Series (60min)'].items())[0]
    date = date_and_price[0]
    closing_price = date_and_price[1]['4. close']
    return date, closing_price

# %%
dates = []
df_rows = []
for ticker in tickers_list:
    date, closing_price = get_date_and_latest_price(ticker)
    dates.append(date)
    ticker_and_price = {'Ticker':ticker,'Precio de cierre':closing_price,'Ponderador':tickers_y_ponderadores[ticker]}
    df_rows.append(ticker_and_price)

# %%
df = pd.DataFrame(df_rows)

# %%
sum(df['Ponderador'])

# %%
def calculo_indice(df:pd.DataFrame, chain_adjustment):
    vector_pond = pd.Series(df['Ponderador'])
    vector_ult_precio = pd.Series(df['Precio de cierre'], dtype='float')
    ArgDR_Index = vector_pond.dot(vector_ult_precio) * chain_adjustment
    return ArgDR_Index

# %%
valor = calculo_indice(df,chain_adjustment_jul_25)

# %%
fecha = dates[-1]

# %%
print(fecha,valor)

# %%

def add_to_bigquery(fecha, valor, project_id="abiding-lead-452321-n0", dataset_id="adr_index", table_id="argdr_serie_historica"):
    """
    Adds a (fecha, valor) tuple as a new row to a BigQuery table.
    
    Parameters:
    fecha (str or datetime): The date value to insert, can be a string like '2024-02-26 13:49:00'
    valor (float): The value to insert
    project_id (str): The GCP project ID
    dataset_id (str): The BigQuery dataset ID
    table_id (str): The BigQuery table ID
    
    Returns:
    bool: True if the operation was successful, False otherwise
    """
    # Initialize a BigQuery client
    client = bigquery.Client()
    
    # Construct the full table ID
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
    # Ensure valor is a float
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        print(f"Error: 'valor' must be a numeric value, got {valor}")
        return False
    
    # Prepare the row to be inserted
    row_to_insert = [
        {"Fecha": fecha, 
         "Valor": valor}
    ]
    
    # Configure the load job
    job_config = bigquery.LoadJobConfig(
        # Specify the write disposition to append data
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        # Auto-detect the schema
        autodetect=True,
    )
    
    try:
        # Insert the row into the table
        load_job = client.load_table_from_json(
            row_to_insert, 
            table_ref, 
            job_config=job_config
        )
        
        # Wait for the job to complete
        load_job.result()
        
        print(f"Successfully added data to {table_ref}")
        return True
        
    except Exception as e:
        print(f"Error adding data to BigQuery: {e}")
        return False

# %%
add_to_bigquery(fecha,valor)

# %%
def get_bigquery_data(project_id="abiding-lead-452321-n0", dataset_id="adr_index", table_id="argdr_serie_historica"):
    """
    Returns all data from a BigQuery table as a pandas DataFrame.
    
    Parameters:
    project_id (str): The GCP project ID
    dataset_id (str): The BigQuery dataset ID
    table_id (str): The BigQuery table ID
    
    Returns:
    pandas.DataFrame: DataFrame containing all data from the specified BigQuery table
    """
    # Initialize a BigQuery client
    client = bigquery.Client()
    
    # Construct the full table ID
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    try:
        # Construct a SQL query to get all data from the table
        query = f"SELECT * FROM `{table_ref}`"
        
        # Execute the query and convert results to a DataFrame
        print(f"Fetching data from {table_ref}...")
        df = client.query(query).to_dataframe()
        df = df.sort_values(by='Fecha')
        df = df.reset_index(drop=True)
        
        # Print information about the resulting DataFrame
        print(f"Successfully loaded {len(df)} rows into DataFrame")
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"DataFrame data types: \n{df.dtypes}")
        
        return df
        
    except Exception as e:
        print(f"Error fetching data from BigQuery: {e}")
        return None

# Example usage:
# df = get_bigquery_data()
# print(df.head())  # Display the first 5 rows


# %%
result = get_bigquery_data()
print(result.tail(7))
# 
# # %%
# def filter_dataframe_by_date(df, start_date):
#     """
#     Filter a DataFrame by date, handling timezone issues.
#     
#     Parameters:
#     df (pandas.DataFrame): DataFrame with datetime index
#     start_date (str): Date string in format 'YYYY-MM-DD'
#     
#     Returns:
#     pandas.DataFrame: Filtered DataFrame
#     """
#     # Check if the DataFrame index has timezone info
#     is_tz_aware = df.index.tz is not None
#     
#     # Convert start_date to datetime with appropriate timezone
#     if is_tz_aware:
#         # If DataFrame has timezone, make sure start_date has the same timezone
#         tz = df.index.tz
#         start_datetime = pd.to_datetime(start_date).tz_localize(tz)
#     else:
#         # If DataFrame has no timezone, use naive datetime
#         start_datetime = pd.to_datetime(start_date)
#     
#     # Filter the DataFrame
#     filtered_df = df[df.index >= start_datetime]
#     print(f"Filtered from {len(df)} to {len(filtered_df)} rows")
#     
#     return filtered_df
# 

# %%
## Create a DataFrame with proper datetime index
## df = pd.DataFrame({'values': result['Valor']}, index=result['Fecha'])
# result = result.set_index('Fecha')
# result.index = pd.to_datetime(result.index)
# filtered_df = filter_dataframe_by_date(result, start_date='2024-01-01')
# filtered_df
# 
# # %%
# plt.figure(figsize=(24,10))
# plt.plot(filtered_df.index, filtered_df['Valor'], linewidth = 3.5)
# plt.title('Evolución del ArgDR Index, 2024-25', fontsize=35)
# plt.yticks(fontsize=20)
# 
# # Format x-axis with dates
# plt.gca().xaxis.set_major_locator(plt.MultipleLocator(21))  # Set ticks every 21 days
# plt.gcf().autofmt_xdate()  # Auto-format date labels
# plt.xticks(fontsize=20, rotation=35)
# 
# plt.grid()
# plt.ylim(filtered_df['Valor'].min() * 0.8, filtered_df['Valor'].max() * 1.06)
# # Save the plot as a .jpeg file
# plt.savefig('ArgDR_chart.jpeg', format='jpeg')
# 
# %%



