import requests
import pandas as pd
import numpy as np
from google.cloud import secretmanager
from google.auth import default
from google.cloud import bigquery

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

def get_data_from_api(ticker, api_key, function='TIME_SERIES_INTRADAY'):
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

def get_date_and_latest_price(ticker, api_key):
    api_data = get_data_from_api(ticker, api_key)
    date_and_price = list(api_data['Time Series (60min)'].items())[0]
    date = date_and_price[0]
    closing_price = date_and_price[1]['4. close']
    return date, closing_price

def calculo_indice(df, chain_adjustment):
    vector_pond = pd.Series(df['Ponderador'])
    vector_ult_precio = pd.Series(df['Precio de cierre'], dtype='float')
    ArgDR_Index = vector_pond.dot(vector_ult_precio) * chain_adjustment
    return ArgDR_Index

def add_to_bigquery(fecha, valor, project_id="abiding-lead-452321-n0", dataset_id="adr_index", table_id="argdr_serie_historica"):
    """
    Adds a (fecha, valor) tuple as a new row to a BigQuery table.
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

def argdr_index(request):
    """
    Entry point for the Cloud Function.
    """
    # Constants from your original script
    tickers_dict = {
        'YPF Sociedad Anonima': 'YPF',
        'Grupo Supervielle': 'SUPV',
        'Grupo Financiero Galicia ADR': 'GGAL',
        'BBVA Argentina': 'BBAR',
        'Banco Macro B ADR': 'BMA',
        'Telecom Argentina ADR': 'TEO',
        'Cresud SACIF': 'CRESY',
        'Central Puerto': 'CEPU',
        'Pampa Energia ADR': 'PAM',
        'Loma Negra ADR': 'LOMA',
        'IRSA ADR': 'IRS',
        'Transportadora Gas ADR': 'TGS',
        'Bioceres Crop': 'BIOX',
        'Edenor ADR': 'EDN'
    }
    
    cap_bursatiles = {
        'YPF Sociedad Anonima': 13946871640,
        'Grupo Supervielle': 1233150264,
        'Grupo Financiero Galicia ADR': 8523720280,
        'BBVA Argentina': 3843734562,
        'Banco Macro B ADR': 5493200605,
        'Telecom Argentina ADR': 5272228248,
        'Cresud SACIF': 633031172,
        'Central Puerto': 1881929669,
        'Pampa Energia ADR': 4208906073,
        'Loma Negra ADR': 1295332593,
        'IRSA ADR': 1042296329,
        'Transportadora Gas ADR': 3894785724,
        'Bioceres Crop': 276407628,
        'Edenor ADR': 1623461084
    }
    
    chain_adjustment_feb_25 = 0.911886396417253
    
    # Get API key from Secret Manager
    project_id = "562376856357" 
    api_key = access_secret(secret_id="ALPHAVANTAGE_API_KEY", project_id=project_id)
    
    # Calculate ponderadores
    suma_cap = sum(cap_bursatiles.values())
    firmas_y_pond = []
    for i in cap_bursatiles:
        firmas_y_pond.append([i, (cap_bursatiles[i]/suma_cap)])
    ponderadores = dict(firmas_y_pond)
    
    # Create tickers_y_ponderadores
    tickers_y_ponderadores = {tickers_dict[nombre_empresa]:ponderador for (nombre_empresa,ponderador) in ponderadores.items()}
    
    # Get tickers list
    tickers_list = list(tickers_dict.values())
    
    # Get data for each ticker
    dates = []
    df_rows = []
    for ticker in tickers_list:
        date, closing_price = get_date_and_latest_price(ticker, api_key)
        dates.append(date)
        ticker_and_price = {
            'Ticker': ticker,
            'Precio de cierre': closing_price,
            'Ponderador': tickers_y_ponderadores[ticker]
        }
        df_rows.append(ticker_and_price)
    
    # Create DataFrame and calculate index
    df = pd.DataFrame(df_rows)
    valor = calculo_indice(df, chain_adjustment_feb_25)
    fecha = dates[-1]
    
    # Add to BigQuery
    add_to_bigquery(fecha, valor)
    
    return f"Index calculation completed. Date: {fecha}, Value: {valor}"

# For local testing
if __name__ == "__main__":
    argdr_index(None)