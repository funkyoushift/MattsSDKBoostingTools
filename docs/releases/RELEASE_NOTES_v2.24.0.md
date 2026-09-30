# Borderlands 4 Modding Tools v2.24.0

- Steam guests can send items to their own backpack through the normal size-based delivery queue.
- Drop My Backpack now works for your own character in a supported Steam guest session. Drop requests are submitted together; ground items appear as the host processes and replicates them.
- Host delivery keeps its existing behavior. Guest actions cannot target other players, and unsupported guest builds are rejected. Epic guest support is not included.

## Validation and limits

A fresh-map guest test received all 979 requested items in 64 chunks, then emptied the backpack with one full drop submission without a disconnect. The integrated helper also passed a separate live delivery/drop check.

Exact item-code preservation is not guaranteed in guest delivery: 322 of the 979 received codes differed from the inputs in both test runs. This can include changed parts. Keep the original codes if exact construction matters. This test did not establish exact ground-pickup counts or repeat save/reload persistence for the full list.

Android remains on the existing 1.5.0 build. Update the desktop app and SDK mod together.
