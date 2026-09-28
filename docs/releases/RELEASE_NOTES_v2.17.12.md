# MSBT v2.17.12

This update repairs the desktop update flow and bookmark editing/imports.

- Avoid updater file locks from an older setup process. Launch failures are shown and can be retried.
- Reopen MSBT automatically after Restart and Install finishes.
- Detect older bundled resources even when the app version matches the latest release, without downgrading a newer app.
- Restore the existing-folder dropdown in Bookmarks > Details > Folder path.
- Preserve long bookmark codes without truncation or rejecting an otherwise valid bulk import. Codes beyond the tested delivery size are identified as saved but not deliverable.
- Refresh the bundled GZO catalog, including removal of its withdrawn oversized item.

Validation: updater and bookmark regression tests, settings restart checks, installer checks, real public-package fresh installation, and restart/install handoff. The real update reopened MSBT and preserved all 980 saved bookmarks unchanged.

No experimental large-item delivery changes are included. Android remains v1.4.2. Existing saved bookmarks are preserved; refreshing the catalog does not delete user bookmarks.
