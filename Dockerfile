  # Start with a standard Python base image
  FROM python:3.9-slim

  # Install prerequisite system packages
  RUN apt-get update && apt-get install -y gnupg curl g++ unixodbc-dev ghostscript

  # Add the Microsoft package repository and install the ODBC driver
  # ---- THIS IS THE CRUCIAL PART FOR THE EULA ----
  RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
      && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
      && apt-get update \
      && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
      && rm -rf /var/lib/apt/lists/*
  # ----------------------------------------------

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