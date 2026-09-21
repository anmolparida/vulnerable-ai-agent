# Deliberately insecure container (SAST / container-scan findings):
#  - base image pinned to 'latest' (non-reproducible, may carry CVEs)
#  - runs as root (no USER directive)
#  - pip install with unpinned deps
#  - secrets baked in via committed .env
FROM python:latest

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# AI/ML dependency manifest: present in the image for SCA / container scanning
# but intentionally NOT installed (torch/tensorflow/etc. would bloat the image
# and aren't needed to run the mock agent). Lab-only: pip install -r requirements-ai.txt
COPY requirements-ai.txt .

COPY . .

EXPOSE 8080
# runs as root, debug on
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
