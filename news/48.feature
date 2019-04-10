Create symlink to latest timestamped blobstorage backup.
When ``blob_timestamps`` is false, ``blobstorage.0`` is a stable filename,
but with ``blob_timestamps`` true, such a stable name was missing.
[maurits]