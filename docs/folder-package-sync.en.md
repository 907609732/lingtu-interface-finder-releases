# ArtHub Direct Folder Sync Guide

[简体中文](folder-package-sync.zh-CN.md) | **English** · [Back to home](../README.en.md)

Updated 2026-11-18. In 0.7.5, a library is a normal folder. Original files, immutable revisions and catalog records are written directly into that folder, and ArtHub synchronizes it. This feature is included in 0.7.5; historical `extension-v0.7.4` and 0.5.x packages do not include it.

> Historical note: on 2026-11-12 a development build verified “one package per folder + manual submission.” That daily workflow is retired. Legacy format 3 projects are supported only by a read-only migration path; this is no longer a packaging or publication guide.

## One normal folder

| Location | Contents | Behavior |
| --- | --- | --- |
| ArtHub-synchronized folder | `library.json`, `revisions/`, `assets/`, `media/`, `catalog/revisions/` | Written on save; ArtHub transfers it |
| Per-computer local cache | SQLite, query cache, thumbnails/previews, features and AI index, tasks, recycle | Stays on each computer; never enters the shared folder |

Keep the two locations separate. The app does not call the ArtHub upload API and does not present a successful local write as a completed cloud upload. Use ArtHub's own status for transfer progress.

## First connection

1. Let ArtHub synchronize the library folder to this computer.
2. Choose “Open library folder” on the welcome screen, or select the same normal directory in Settings.
3. The app reads `library.json`, immutable revisions and originals directly. It does not create package projects or unpack automatically.
4. Each computer prepares its own AI models. SQLite, vector indexes, previews and recycle are local.
5. If the folder is temporarily offline, open pages and local cache are not deleted. ArtHub synchronizes after the connection returns.

To create a library, choose an empty folder. The app writes a normal library layout and a `.gitignore`; it does not create `packages/`, `commits/` or a local `state.json` in the shared folder.

## Editing and synchronization

1. Upload media, edit names/fields or restore a historical version. Saving writes directly into the normal folder.
2. Immutable revisions keep their parent relationships. Concurrent edits to one record retain conflict branches; no side is silently chosen as the winner.
3. ArtHub transfers new revisions and originals to other computers. Another computer opens the same folder.
4. There is no “Submit updates” button and no daily packaging, manual publication, automatic extraction or checkpoint cleanup workflow.
5. Local caches stay outside the shared directory, so SQLite, LanceDB, previews and GPU caches are not synchronized.

## Migrating a legacy folder package

A legacy `format: 3 / folder-packages` project cannot be edited by the current version. Opening it shows a read-only migration notice and does not create an empty library.

1. Choose “Migrate legacy folder package to a normal library” in Settings or on the welcome screen.
2. Select the old synchronization directory. The app first looks for the local workspace recorded in settings. If it cannot find one, it clearly warns that only fully committed data in the old directory can be migrated.
3. Select an empty destination folder. A non-empty destination is rejected; the source is never overwritten.
4. The migrator copies the latest local generation into a side-by-side normal directory. It preserves uncommitted revisions, conflicts, revisions and files referenced by prepared/outgoing snapshots, and applies available remote-only commits read-only first.
5. It verifies each file's SHA-256, revision references, originals and recycle before switching. An interrupted or failed migration, a concurrent source change or a verification failure never switches the destination; the operation can be retried.
6. The local recycle is copied under the same library ID and record paths, so recovery still works after migration.
7. The old directory, packages, `state.json`, `outgoing/`, `archives/` and local recycle are retained. A migration log under the local cache `migrations/` records the source, destination, counts, tree hash and rollback notes.

Offline migration uses only the latest local generation and records that unapplied remote-only commits remain in the old directory. Recheck after ArtHub reconnects. Missing originals and corrupt packages are never guessed or silently filled.

## Current limits

- AI models, query databases, previews and feature caches are not copied into the shared folder.
- Incomplete, corrupt or missing-original commits in an old package are not repaired automatically. Migration stops and leaves the old data intact.
- Real ArtHub two-machine transfer, placeholder downloads, network interruption and cloud completion status still require environment-specific acceptance testing.
- Older clients cannot edit the new normal-library format. Preserve changes made after migration before rolling back.

[简体中文](folder-package-sync.zh-CN.md) · [Back to English home](../README.en.md)
