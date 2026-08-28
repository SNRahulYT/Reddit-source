# Moe's Reddit — SideStore source

This repository creates an AltStore/SideStore-compatible JSON source for Moe's Reddit.

## Confirmed from the supplied IPA

- Bundle ID: `com.reddit.Reddit`
- Version: `2026.33.0`
- Build: `636848`

## How to use

1. Create a new GitHub repository.
2. Upload `moe-reddit.json`, `update_source.py`, and `.github/workflows/update.yml`.
3. Open **Actions** in the repository and enable GitHub Actions if GitHub asks.
4. Run **Update Moe Reddit source** manually once.
5. Open the generated `moe-reddit.json` and use its **Raw** URL as your SideStore source.

The workflow then checks Moe's app page every 6 hours and commits the JSON when it finds a newer version.

## Important

Moe currently serves the IPA through a download/Google Drive link. The updater tries to discover that link from the app page and converts common Google Drive file links into a direct-download form.

If Moe changes the website HTML, the workflow may fail rather than silently publishing a broken source. Check the Actions log if that happens.
