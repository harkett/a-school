FROM python:3.12-slim

WORKDIR /app

# Dépendances Python (mêmes versions que requirements.txt — la boîte est identique A/B)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le code arrive par volume (.:/app) au run ; ce COPY sert au build autonome.
COPY . .

EXPOSE 8001
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
