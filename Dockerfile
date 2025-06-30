# Start with a standard Python base image
FROM python:3.9-slim

# Install all system dependencies in a single RUN command to avoid conflicts
RUN apt-get update && \
    # Install prerequisite packages needed for adding new repositories and for your app
    apt-get install -y gnupg curl g++ ghostscript && \
    # Add the Microsoft GPG key for authentication
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    # Add the Microsoft package repository itself
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    # IMPORTANT: Update package lists again after adding the new repository
    apt-get update && \
    # Install the ODBC driver and unixodbc-dev together, accepting the EULA
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    # Clean up apt caches to keep the final image size smaller
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