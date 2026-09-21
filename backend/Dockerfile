# Deliberately insecure container (SAST / container-scan findings):
#  - base image pinned to 'latest' (non-reproducible, may carry CVEs)
#  - runs as root (no USER directive)
#  - pip install with unpinned deps
#  - secrets baked in via committed .env
FROM python:latest

WORKDIR /app
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

# The large deliberately-vulnerable AI/ML manifest (requirements.txt, ~90 pkgs)
# is copied into the image via `COPY . .` below for SCA / container scanning,
# but is NOT installed (its torch/tensorflow/jax pins conflict on purpose).

COPY . .

EXPOSE 8080
# runs as root, debug on
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
