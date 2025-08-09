# Use official Playwright image (has Chromium and system deps)
FROM mcr.microsoft.com/playwright/python:v1.35.0-focal

# Set workdir
WORKDIR /app

# Create venv (optional) and install deps
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && playwright install --with-deps chromium

# Copy app code
COPY . .

# Expose port (Render sets PORT env; this is just documentation)
EXPOSE 10000

# Environment for Flask/Gunicorn
ENV PYTHONUNBUFFERED=1

# Start with gunicorn
# Bind 0.0.0.0 and use webapp:app (Flask app object); use PORT from env with fallback
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-10000} webapp:app"] 