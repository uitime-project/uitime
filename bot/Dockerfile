FROM python:3.14-slim

WORKDIR /app

# Copy requirements to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the whole program
COPY . .

CMD ["python", "main.py"]