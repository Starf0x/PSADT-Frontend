# What's new

Plain-language notes for each version, newest first. The app shows these on the System page.
Every version gets a "## x.y.z" heading; keep the lines short and write for people, not programmers.

## 0.3.11
- An upload that gets stuck now stops after a minute without progress and says why (often a reverse proxy or tunnel with a size limit, or a full disk), instead of waiting forever.

## 0.3.0
- Only administrators can delete packages now. Editors can still create and change them.

## 0.2.99
- Fixed: the daily usage check-in could be refused by the collector's firewall because it identified itself as a Python script. It now identifies itself as PSADT Frontend.
- The GitHub page has a new README with screenshots, and the wiki now has a full user guide with a page for every screen.

## 0.2.88
- The export counter counts each package once per version. Downloading it again, or as both ZIP and .intunewin, no longer adds to the count. A new version does count. The package goes to whoever downloaded it first.

## 0.2.77
- Buttons and highlighted tabs have softer colours and dark text, so they stay easy to read whatever the colour of the day.

## 0.2.66
- The background now has the same soft glow as My Audiobook Collection, and the colours of the whole app change a little every night.
- Anonymous daily check-in, as in My Audiobook Collection: once a day the app tells its author it is running (version, Docker/LXC, days running, a random id). Nothing about your packages, files or users is sent. It can be turned off with PSADT_USAGE_OPTOUT=1 on the server.

## 0.2.55
- Downloading a package now shows what is happening: first "Building the package…", then a progress bar, and finally the file name when it is done.
- When the download buttons are locked, a line below them tells you to fix the problems in the check first.

## 0.2.44
- The download buttons check the package once more just before downloading. If something is wrong, you stay on the page and see what to fix, instead of a page with a technical error.

## 0.2.33
- The Packages page counts every successful download: in total, by you, and per user.
- New detection rule "MSIX package": finds an app installed for all users, with Get-AppxProvisionedPackage or with DISM. Part of the name is enough.
- Registry keys get one-click buttons for HKLM, HKCU, HKEY_CLASSES_ROOT and HKU.
- Updating from the System page now shows a moving progress bar with a percentage, and the page reloads by itself when it is done.
- Fixed: after an update the old version kept running in the background, so some pages stayed empty and new options (such as winget) were refused. The app is now always restarted.

## 0.2.22
- Detection rule "MSI ProductCode": choose an MSI (already uploaded, or browse your PC) and its ProductCode is filled in for you. The product name and version are shown as a check.
- After an update the browser now always loads the new version straight away, instead of showing the old page from its cache.

## 0.2.11
- Every file field in a step now has a Browse button: pick a file on your PC and it is uploaded and selected in one go.
- Run EXE can now also start programs that are already on every Windows PC, such as winget, msiexec, PowerShell and cmd. No upload needed. winget is found automatically, also when Intune installs as SYSTEM.
- The app now always uses a dark design, with more colour and depth.

## 0.2.0
- Changes to a package are now saved automatically a moment after you make them. Nothing is lost anymore when the page reloads or the app restarts for an update.
- If you try to leave the page while something is still being saved, your browser warns you first.

## 0.1.99
- When a newer version is out, administrators see an orange dot next to System and a message at the top of every page.
- The System page has a "Check now" button, and the app looks for new versions every 15 minutes instead of every hour.

## 0.1.88
- Arguments, paths and code in a step now use the full width, so long commands are easy to read.
- Under the arguments you can click {Files} or one of your uploaded files to insert its full path, so you do not have to type it.

## 0.1.77
- In the arguments of a step you can write {Files} for the package's Files folder on the PC. For example: --msix-path "{Files}\app.msix".

## 0.1.66
- Users now have a full name next to their login name. Add it when you create a user; everyone can change their own name under their account.
- New packages fill in your full name as script author.
- While files upload you see a progress bar for each file.
- The "Check syntax" button works again on Proxmox containers. If the check cannot run, the message now explains that it is a server problem and not a mistake in your package.

## 0.1.55
- When an update is available, the System page now shows what is new before you install it.
- These notes are written in plain language, in English, Dutch and German.

## 0.1.44
- Everyone picks their own language. Your choice is saved with your account, so it follows you to any computer.

## 0.1.33
- The Export tab checks your package before you download it. Red problems must be fixed first; orange ones are tips.
- You can choose how long uploaded installers stay on the server: forever, right after a download, or a number of days.
- You can choose the default folder where the installation log is written on the PC. Each package can use its own folder.
- New icon and a fresh, cleaner look.
- MSIX and APPX files can now be uploaded.

## 0.1.22
- The app speaks English, Dutch and German. Pick your language at the bottom of the menu.
- Containers on Proxmox can update themselves: go to System and click "Install it".

## 0.1.11
- Fixed the Proxmox installation, which could stop before it was finished.

## 0.1.0
- Install on Proxmox with one command, the same way as the community helper scripts.
