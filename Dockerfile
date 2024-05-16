FROM python:3.10

WORKDIR /app

# Install requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src/ ./src/
CMD ["python3"]
