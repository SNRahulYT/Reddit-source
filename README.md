# Moe's Reddit — SideStore source

This repository publishes a SideStore/AltStore-compatible source for Moe's Reddit.

The updater checks Moe's App Hub every 6 hours, finds the Reddit version and the
Google Drive download link belonging to the Reddit card, and updates
`moe-reddit.json`.

## Current IPA metadata

- Bundle ID: `com.reddit.Reddit`
- Version: `2026.33.0`
- Build: `636848`

## Setup

1. Upload all files while preserving `.github/workflows/update.yml`.
2. Enable GitHub Actions.
3. Run **Actions → Update Moe Reddit source → Run workflow** once.
4. Open `moe-reddit.json`.
5. Tap **Raw** and copy that URL.
6. Add the Raw URL to SideStore as a source.

The scheduled workflow checks every 6 hours. GitHub does not guarantee that a
scheduled job starts exactly on the minute.

If Moe changes the HTML structure of his site, the workflow intentionally fails
instead of writing an unverified/broken download URL.
