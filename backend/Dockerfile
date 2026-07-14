FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY schema.sql ./
COPY ekip.json* ./
COPY firsatlar.json* ./
COPY tasklar.json* ./
COPY basvurular.json* ./
COPY projeler.json* ./

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
