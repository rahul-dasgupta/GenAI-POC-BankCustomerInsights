from azure.storage.blob import BlobServiceClient

def download_blob(blob_name):
    # Replace with your Azure Storage details
    connection_string = "DefaultEndpointsProtocol=https;AccountName=mygenaipoc;AccountKey=p8J69jdICgF4PZMnl9KmkBNxOx0lzg7PC815pdFywJqB1dqusZlsnAXg6PzpMiAXCopZCihYFuWn+AStxyPMcQ==;EndpointSuffix=core.windows.net"
    container_name = "mygenaipoc"
    download_file_path = f"/Users/Rahul/Downloads/{blob_name}"

    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    # Download the PDF file
    with open(download_file_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())

    print(f"Downloaded {blob_name} to {download_file_path}")

# Example usage (uncomment to test directly)
# download_blob("OGS005065437202301.pdf")