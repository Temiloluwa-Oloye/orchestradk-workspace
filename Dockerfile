# Use a lightweight, stable Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker build cache
COPY requirements.txt .

# Install dependencies directly into the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the workspace
COPY . .

# Ensure the output directory exists and has full write permissions
RUN mkdir -p output && chmod 777 output

# Set the default entrypoint to the OrchestrADK CLI
ENTRYPOINT ["python", "-m", "src.cli.main"]