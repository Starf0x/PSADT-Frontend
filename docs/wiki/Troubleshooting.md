# Troubleshooting

### I can't sign in over http://
`PSADT_COOKIE_SECURE` is `true`, so the browser drops the session cookie on a plain `http://` address. Use HTTPS, or set `PSADT_COOKIE_SECURE=false` for local use and restart the app.

### After an update the app still shows the old version, or a page is empty
The browser or the service still runs the old version. In the LXC run `systemctl restart psadt-frontend` once, then reload the page with Ctrl+F5. Since 0.2.33 the updater restarts the service on its own.

### The download buttons are grey
The check above them found an error. Fix the red items (they name the step or field) and the buttons unlock. Warnings don't block.

### "Fix the problems shown in the check first"
The server checked the package again and found an error, for example because a file was removed by the [retention](System) setting. Open the Export tab again to see which problem it is.

### The syntax check says pwsh is not available
PowerShell 7 isn't installed on the server. The Docker image and LXC install include it; on a self-built server install `powershell` from Microsoft's package repository. The check never runs your script, it only parses it.

### Read on an MSI shows an error
The file isn't a valid MSI, or it's an `.msp`/`.exe`. Pick the `.msi` itself.

### The admin password is lost
Docker: `docker compose logs | grep 'admin password'`. LXC: `cat /root/psadt-frontend-admin.txt` or `journalctl -u psadt-frontend | grep 'admin password'`. Another administrator can also set a new password on the [Users](Users-and-roles) page.

### Where are my data?
In `PSADT_DATA_DIR`: the database `psadt.db` and the uploads. Back up this folder.
