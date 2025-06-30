import pyodbc
from azure.storage.blob import BlobServiceClient
import json
import io
from MyGenAIPOC_RAG import build_qa_chain  # Import the function from your RAG module

# Replace with your Azure SQL details
server = 'mygenaipoc.database.windows.net'
database = 'genaipoc'
username = 'rdg'
password = 'Azure@4758'
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
    connection_string = "DefaultEndpointsProtocol=https;AccountName=mygenaipoc;AccountKey=p8J69jdICgF4PZMnl9KmkBNxOx0lzg7PC815pdFywJqB1dqusZlsnAXg6PzpMiAXCopZCihYFuWn+AStxyPMcQ==;EndpointSuffix=core.windows.net"
    container_name = "mygenaipoc"
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

# Accept input for CustomerID
customer_id = input("Enter Customer ID or Aadhar: ")
pdf_file, json_file = process_customer(customer_id)

if json_file:
    # Build the QA chain using the downloaded PDF (if any) and in-memory JSON:
    qa_chain = build_qa_chain(
        pdf_file=pdf_file,  # pdf_file can be None
        json_file=json_file,
        embedding_deployment="text-embedding-ada-002",
        embedding_model="text-embedding-ada-002",
        embedding_endpoint="https://dasgu-mchng52g-eastus2.openai.azure.com/",
        llm_deployment="gpt-4o",
        llm_endpoint="https://dasgu-mchng52g-eastus2.openai.azure.com/"
    )

    # Initial question
    query = (
        """I am a relationship manager in Axis Bank and this attached document has details about one of my customers. \
           First check if the Customer Status is Exited or Blacklisted. \
           If Exited then say Customer is no longer with us and give no further response. \
           If Blacklisted then say Customer is Blacklisted and give no further response.\
           If neither then don't mention anything about the status, just give the Customer Name and Type and move on to answer the questions below\
           1. Are there any upcoming dates in 2023 for his deposits, credit cards, investments, insurance, etc.?\
           2. What are the top 2 up-selling or cross-selling opportunities for this customer based on his current portfolio?"""
    )
    while True:
        result = qa_chain(query)
        print("Answer:", result['result'])
        follow_up = input("Do you have any further questions about this customer? (Type your question or 'no' to exit): ").strip()
        if follow_up.lower() in ["no", "n", "no further questions", "exit", "quit"]:
            print("Session ended.")
            break
        query = follow_up
else:
    print("Customer not found. Please check the Customer ID or Aadhar and try again.")