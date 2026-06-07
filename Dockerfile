# Start with a stable Debian Bookworm-based Python image
FROM python:3.11-slim-bookworm

# Install system dependencies and Microsoft ODBC Driver 18
RUN apt-get update && \
    apt-get install -y curl g++ ghostscript gnupg ca-certificates && \
    mkdir -p /etc/apt/keyrings && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Define the command to run your application
CMD ["streamlit", "run", "MyGenAIPOC_UI.py", "--server.port=8501", "--server.address=0.0.0.0"]
