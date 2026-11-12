# --- Frontend build ---
FROM node:22-alpine AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# --- Runtime ---
FROM python:3.13-slim
LABEL org.opencontainers.image.title="PSADT Frontend" \
      org.opencontainers.image.description="Web UI for building PSAppDeployToolkit v4 packages" \
      org.opencontainers.image.source="https://github.com/Starf0x/PSADT-Frontend" \
      org.opencontainers.image.licenses="MIT" \
      net.unraid.docker.icon="https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/assets/icon.png" \
      net.unraid.docker.webui="http://[IP]:[PORT:8000]/"
ARG PWSH_VERSION=7.4.6
ARG PSADT_VERSION=4.1.8
ARG PSADT_SHA256=50cb8d32973fc7648060a48cad63912ecb5caca5a70754f37e83aa06bd380283
ARG TARGETARCH
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PSADT_DATA_DIR=/data \
    PSADT_PWSH_PATH=/opt/pwsh/pwsh DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 \
    POWERSHELL_TELEMETRY_OPTOUT=1 POWERSHELL_UPDATECHECK=Off XDG_CACHE_HOME=/tmp XDG_DATA_HOME=/tmp \
    PSADT_TOOLKIT_ZIP=/opt/psadt/PSAppDeployToolkit_Template_v4.zip
WORKDIR /app/backend
# PowerShell 7: alleen gebruikt om gegenereerde scripts op syntax te controleren (parser, geen uitvoering)
RUN ARCH=$([ "$TARGETARCH" = "arm64" ] && echo arm64 || echo x64) \
 && python -c "import urllib.request as u; u.urlretrieve('https://github.com/PowerShell/PowerShell/releases/download/v${PWSH_VERSION}/powershell-${PWSH_VERSION}-linux-${ARCH}.tar.gz', '/tmp/pwsh.tgz')" \
 && mkdir -p /opt/pwsh && tar xzf /tmp/pwsh.tgz -C /opt/pwsh && rm /tmp/pwsh.tgz && chmod +x /opt/pwsh/pwsh
# Officieel PSADT v4-pakket (module, exe, assets) voor de ZIP/.intunewin-export, gecontroleerd op sha256
RUN mkdir -p /opt/psadt \
 && python -c "import urllib.request as u; u.urlretrieve('https://github.com/PSAppDeployToolkit/PSAppDeployToolkit/releases/download/${PSADT_VERSION}/PSAppDeployToolkit_Template_v4.zip', '/opt/psadt/PSAppDeployToolkit_Template_v4.zip')" \
 && echo "${PSADT_SHA256}  /opt/psadt/PSAppDeployToolkit_Template_v4.zip" | sha256sum -c -
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd --system --uid 10001 --home /app psadt \
 && mkdir -p /data && chown psadt /data
COPY VERSION /app/VERSION
COPY release-notes /app/release-notes
COPY backend/app ./app
COPY --from=ui /ui/dist /app/frontend/dist
USER psadt
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
