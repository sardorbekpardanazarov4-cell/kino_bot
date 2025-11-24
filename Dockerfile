FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ma'lumotlar saqlanishi uchun /data papkasi
ENV DB_FILE=/data/kino_baza.json

CMD ["python", "bot.py"]