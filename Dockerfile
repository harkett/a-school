FROM python:3.12-slim

WORKDIR /app

# Une police UNICODE, pour ÉCRIRE des PDF. Les polices de base d'un PDF sont limitées au latin-1 :
# le tiret cadratin « — », l'apostrophe typographique « ’ », le « œ » ou un signe mathématique
# feraient tomber la génération du référentiel. DejaVu couvre tout ça et pèse 2 Mo.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python (mêmes versions que requirements.txt — la boîte est identique A/B)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le code arrive par volume (.:/app) au run ; ce COPY sert au build autonome.
COPY . .

EXPOSE 8001
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
