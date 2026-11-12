# What's new

Plain-language notes for each version, newest first. The app shows these on the System page.
Every version gets a "## x.y.z" heading; keep the lines short and write for people, not programmers.

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
