import pyodbc
from azure.storage.blob import BlobServiceClient
import json
import io
import os

# Replace with your Azure SQL details
server = os.environ.get('SQL_SERVER')
database = os.environ.get('SQL_DATABASE')
username = os.environ.get('SQL_USERNAME')
password = os.environ.get('SQL_PASSWORD')
driver = '{ODBC Driver 18 for SQL Server}'

# Create connection string
conn_str = (
    f'DRIVER={driver};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

def download_blob(blob_name):
    # Replace with your Azure Storage details
    connection_string = os.environ.get('STORAGE_CONNECTION_STRING')
    container_name = os.environ.get('STORAGE_CONTAINER_NAME')
    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    # Download the PDF file into memory
    pdf_bytes = blob_client.download_blob().readall()
    pdf_file = io.BytesIO(pdf_bytes)
    #print(f"PDF file object for '{blob_name}' created successfully in memory.")
    return pdf_file

def process_customer(customer_id):
    pdf_file = None
    json_file = None
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customer WHERE CustomerID = ? or Aadhar =?", (customer_id,customer_id))
        row = cursor.fetchone()
        if row:
            # Get column names
            columns = [column[0] for column in cursor.description]
            # Create dict from row
            customer_data = dict(zip(columns, row))
            # Use the CustomerID from the data for the filename
            customer_id_from_db = customer_data.get("CustomerID", customer_id)
            # Hold JSON in memory
            json_str = json.dumps(customer_data, indent=4)
            json_file = io.StringIO(json_str)
            #print(f"JSON file object for customer '{customer_id_from_db}' created successfully in memory.")
            one_glance_statement = row[6]
            if one_glance_statement:
                if not one_glance_statement.lower().endswith('.pdf'):
                    one_glance_statement += '.pdf'
                #print(f"OneGlanceStatement: {one_glance_statement}")
                pdf_file = download_blob(one_glance_statement)
#            else:
#                print("No OneGlanceStatement found for this customer.")
    return pdf_file, json_file