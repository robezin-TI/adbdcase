FROM python:3.9-slim

WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Instala numpy primeiro com versão específica
RUN pip install numpy==1.23.5

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
