# 1. Use the official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application code
COPY . .

# 5. Expose the port FastAPI runs on
EXPOSE 8000

# 6. The command to start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
