import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import matplotlib.pyplot as plt


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

def filter_dataframe_by_date(df, start_date):
    """
    Filter a DataFrame by date, handling timezone issues.
    
    Parameters:
    df (pandas.DataFrame): DataFrame with datetime index
    start_date (str): Date string in format 'YYYY-MM-DD'
    
    Returns:
    pandas.DataFrame: Filtered DataFrame
    """
    # Check if the DataFrame index has timezone info
    is_tz_aware = df.index.tz is not None
    
    # Convert start_date to datetime with appropriate timezone
    if is_tz_aware:
        print('tz_aware')
        # If DataFrame has timezone, make sure start_date has the same timezone
        tz = df.index.tz
        start_datetime = pd.to_datetime(start_date).tz_localize(tz)
    else:
        # If DataFrame has no timezone, use naive datetime
        start_datetime = pd.to_datetime(start_date)
    
    # Filter the DataFrame
    filtered_df = df[df.index >= start_datetime]
    print(f"Filtered from {len(df)} to {len(filtered_df)} rows")
    
    return filtered_df

result = get_bigquery_data()

#print(result.tail(7))

# Create a DataFrame with proper datetime index
if 'Fecha' in result.columns:
    result = result.set_index('Fecha')
result.index = pd.to_datetime(result.index)
filtered_df = filter_dataframe_by_date(result, start_date='2024-01-01')

# Remove duplicates
filtered_df = filtered_df.drop_duplicates()

# Print the last seven observations of the time series
print(filtered_df.tail(7))

# Get percentage changes
value_last_observation = filtered_df.at[filtered_df.index[-1],'Valor']
print('last:',type(value_last_observation))
value_next_to_last_observation = filtered_df.at[filtered_df.index[-2],'Valor']
print('next to last:',type(value_next_to_last_observation))
value_week_before = filtered_df.at[filtered_df.index[-6],'Valor']
percentage_change_daily = 100*((value_last_observation/value_next_to_last_observation)-1)
percentage_change_weekly = 100*((value_last_observation/value_week_before)-1)
print(f"El ArgDR index varió un {round(percentage_change_daily,3)}% respecto de la jornada anterior y "
      f"un {round(percentage_change_weekly,3)}% respecto a hace una semana.")


# Make a chart for all values since 2024-01-01

plt.figure(figsize=(24,10))
plt.plot(filtered_df.index, filtered_df['Valor'], linewidth = 3.5)
plt.title('Evolución del ArgDR Index, 2024-25', fontsize=35)
plt.yticks(fontsize=20)

# Format x-axis with dates
plt.gca().xaxis.set_major_locator(plt.MultipleLocator(21))  # Set ticks every 21 days
plt.gcf().autofmt_xdate()  # Auto-format date labels
plt.xticks(fontsize=20, rotation=35)

plt.grid()
plt.ylim(filtered_df['Valor'].min() * 0.8, filtered_df['Valor'].max() * 1.06)
# Save the plot as a .jpeg file
plt.savefig('ArgDR_v2.0\\Graph and chart outputs\\ArgDR_chart_since_2024.jpeg', format='jpeg')


# Make a chart for the last 60 observations ("zooming-in")

filtered_df_60_latest = filtered_df[-60:]
plt.figure(figsize=(24,10))
plt.plot(filtered_df_60_latest.index, filtered_df_60_latest['Valor'], linewidth = 3.5)
plt.title('Evolución del ArgDR Index, últimas 60 jornadas', fontsize=35)
plt.yticks(fontsize=20)

# Format x-axis with dates
plt.gca().xaxis.set_major_locator(plt.MultipleLocator(21))  # Set ticks every 21 days
plt.gcf().autofmt_xdate()  # Auto-format date labels
plt.xticks(fontsize=20, rotation=35)

plt.grid()
plt.ylim(filtered_df['Valor'].min() * 0.8, filtered_df['Valor'].max() * 1.06)
# Save the plot as a .jpeg file
plt.savefig('ArgDR_v2.0\\Graph and chart outputs\\ArgDR_chart_60_latest.jpeg', format='jpeg')