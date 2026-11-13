# PSADT Frontend website

A one-page promotional website for PSADT Frontend: `index.html` plus the screenshots in `img/`. No build step, no external scripts or fonts.

- **Image:** `ghcr.io/starf0x/psadt-frontend-website:latest`, built by `.github/workflows/website.yml` on every change in `website/` on main. nginx, non-root, port 8080.
- **Unraid:** in the Unraid terminal run
  `wget -O /boot/config/plugins/dockerMan/templates-user/my-PSADT-Frontend-Website.xml https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/unraid/psadt-frontend-website.xml`,
  then Docker › Add Container › Template: *PSADT-Frontend-Website* › Apply. The template is `unraid/psadt-frontend-website.xml`.
- **Local preview:** open `index.html` in a browser, or `docker build -t psadt-site website && docker run -p 8080:8080 psadt-site`.
- **Screenshots:** copies of `docs/screenshots/`; replace both when the app changes.
