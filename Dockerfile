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

# Expose port
EXPOSE 10000

# Environment for Flask/Gunicorn
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Start with gunicorn
# Bind 0.0.0.0 and use webapp:app (Flask app object)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "webapp:app"] 