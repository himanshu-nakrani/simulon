FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch first (much smaller than default)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY backend/__init__.py ./backend/__init__.py

# HF Spaces runs on port 7860
ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
