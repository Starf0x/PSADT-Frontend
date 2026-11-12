# --- Frontend build ---
FROM node:22-alpine AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# --- Runtime ---
FROM python:3.13-slim
ARG PWSH_VERSION=7.4.6
ARG TARGETARCH
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PSADT_DATA_DIR=/data \
    PSADT_PWSH_PATH=/opt/pwsh/pwsh DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
    POWERSHELL_TELEMETRY_OPTOUT=1 POWERSHELL_UPDATECHECK=Off XDG_CACHE_HOME=/tmp XDG_DATA_HOME=/tmp
WORKDIR /app/backend
# PowerShell 7: alleen gebruikt om gegenereerde scripts op syntax te controleren (parser, geen uitvoering)
RUN ARCH=$([ "$TARGETARCH" = "arm64" ] && echo arm64 || echo x64) \
 && python -c "import urllib.request as u; u.urlretrieve('https://github.com/PowerShell/PowerShell/releases/download/v${PWSH_VERSION}/powershell-${PWSH_VERSION}-linux-${ARCH}.tar.gz', '/tmp/pwsh.tgz')" \
 && mkdir -p /opt/pwsh && tar xzf /tmp/pwsh.tgz -C /opt/pwsh && rm /tmp/pwsh.tgz && chmod +x /opt/pwsh/pwsh
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd --system --uid 10001 --home /app psadt \
 && mkdir -p /data && chown psadt /data
COPY VERSION /app/VERSION
COPY backend/app ./app
COPY --from=ui /ui/dist /app/frontend/dist
USER psadt
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
