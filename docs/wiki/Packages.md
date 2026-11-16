# Packages

![Packages overview](https://raw.githubusercontent.com/Starf0x/PSADT-Frontend/main/docs/screenshots/02-packages.webp)

The **Packages** page lists every package with its name, vendor, version and when it was last changed. Click a name to open it.

## Export counters

At the top you see three counters:

- **Total**: how many packages have been exported.
- **Yours**: how many of those you exported.
- **Per user**: the count for every user.

A package counts **once per version**. Downloading the same version again, or downloading both the ZIP and the `.intunewin`, does not raise the counter. When you change the version under [App info](App-info) and export again, it counts as a new package. The package counts for the user who downloaded that version first.

## Creating a package

Click **New package**, give it a name, and the [editor](App-info) opens. Editors and administrators can create packages. Only administrators can delete a package (the **Delete** link in the list). Read-only users can view and export them.

## Templates

To reuse a package, open it and click **Save as template** at the top of the editor. A template keeps the app info, all install/uninstall steps and the detection rules. Files are not included.

To start from a template, pick it next to **New package**. You don't have to type a name: leave it empty and the template's application name is used. You can also click **Use** in the template list below the packages; the new package is created and opens straight away. In that list you can also **rename** or **delete** a template.
