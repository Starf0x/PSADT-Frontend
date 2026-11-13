# Promotional website for PSADT Frontend: a static page served by nginx (non-root, port 8080).
FROM nginxinc/nginx-unprivileged:1.27-alpine
LABEL org.opencontainers.image.title="PSADT Frontend website" \
      org.opencontainers.image.description="Promotional website for PSADT Frontend" \
      org.opencontainers.image.source="https://github.com/Starf0x/PSADT-Frontend"
COPY --chown=nginx:nginx index.html /usr/share/nginx/html/index.html
COPY --chown=nginx:nginx img/ /usr/share/nginx/html/img/
EXPOSE 8080
