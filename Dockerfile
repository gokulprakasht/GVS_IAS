FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential ffmpeg && rm -rf /var/lib/apt/lists/*
RUN groupadd -r ias && useradd -r -g ias -d /app -s /sbin/nologin ias
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY --chown=ias:ias . .
RUN mkdir -p /app/data /app/output /app/logs && chown -R ias:ias /app/data /app/output /app/logs
USER ias
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
