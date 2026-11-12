# Folder Package Sync Guide

[简体中文](folder-package-sync.zh-CN.md) | **English** · [Home](../README.en.md)

Updated on 2026-11-12. This guide describes the folder package mode under development. The published `extension-v0.7.4` and legacy 0.5.x packages do not include it. Check the corresponding future release notes for availability.

## Two separate directories

| Location              | Contents                                                                  | When it changes                                                              |
| --------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ArtHub sync directory | Project manifest, folder ZIPs, commit JSON logs and checkpoints           | Published after manual submission; ArtHub transfers the files                |
| Local data directory  | Extracted records, unsubmitted drafts, received state, indexes and caches | Saved during editing; switches to a complete dataset after receiving updates |

Keep these directories separate and place local data outside ArtHub's synchronized scope. The application does not call an ArtHub upload API and does not treat a successful directory write as confirmation of cloud synchronization.

## First connection

1. Let ArtHub synchronize the project files to a directory on this computer.
2. Select the project sync directory when first opening the application. Later, use “设置 → ArtHub 文件夹包同步 → 选择 ArtHub 同步目录” to switch projects.
3. The application reads the manifest and logs, validates complete ZIPs and extracts them into local storage. If logs arrive before packages, or a package is missing or damaged, it retains the last complete version and waits.
4. Check the sync and local data paths in Settings. Existing cached records can open before the background update check; received records remain available when the sync directory is offline.
5. For AI search, download or import models on each computer and build its local image index. Models, image indexes, query databases and GPU caches are not included in shared data packages.

## Editing and manual submission

1. Import assets, edit names or fields, or restore historical records. These changes first become local drafts.
2. Click “提交更新” in the toolbar and review the pending folders and their changes.
3. Select the folders to publish and enter a commit message. Related changes, such as moving records or changing parent-child relationships, are selected together.
4. Click “提交更新” in the panel. The application captures the submission snapshot, validates its ZIPs and publishes the packages, followed by the commit log, to the sync directory.
5. Confirm publication and the remaining pending count. ArtHub then transfers the files; use ArtHub's own UI to check cloud progress.

Edits made after the captured snapshot remain pending local drafts. An interrupted publication can be resumed or its snapshot discarded; discarding the snapshot retains local drafts.

## Why one package per folder

Each folder package contains its direct records, relevant revision history and originals. Subfolders have independent packages; parent packages retain child-folder relationships. Project-wide records have a separate package. Content hashes identify packages without overwriting previous versions.

A small edit usually adds packages for the affected folders and one JSON log. This is not one package per record, and changing a child folder does not automatically repack the entire parent system. Moves between folders can require multiple related packages.

There is a fixed overhead: a library with many folders containing very few records may have more files overall. Historical packages accumulate with submissions and should be maintained according to the team's needs.

## Receiving updates on another client

After discovering a new log, a client waits for every referenced package and predecessor commit. It verifies hashes, extracts into a staging area and switches local data only after the complete update succeeds. Detection is normally automatic; “检查接收更新” also starts a check.

Unsubmitted local changes are retained. Concurrent edits to the same record preserve conflicting branches, which must be resolved through history/conflict controls before submission. The application does not silently use last-writer-wins and does not provide a cross-computer atomic editing lock.

## Verified example

| Step            | Client A                                   | Client B                       | Sync file changes                                                               |
| --------------- | ------------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------- |
| Initial state   | 任务追踪主界面.png                         | Same name                      | None                                                                            |
| Save draft      | Renamed to 任务追踪主界面_人工提交演示.png | Original name remains          | No new files; original file hashes unchanged                                    |
| Submit manually | Select “任务追踪 / 01 总览与导航 / 主界面” | Not received yet               | One ZIP of 47,883 bytes and one JSON log of 812 bytes                           |
| Receive update  | New name                                   | New name appears automatically | Matching revision IDs and original image hashes; both record revisions retained |

This demonstration used two independent source runtimes with separate local data and sync directories, with local file copying simulating ArtHub transport. The sync directory grew from 783 to 785 files. Only one folder package and one log were added; other packages were not rebuilt. Real ArtHub cloud transfer, placeholder downloads and two physical computers remain unverified.

## Migrating an existing library

1. Retain the original library and backups. Ensure participating clients support the folder package protocol; stop editing during migration and wait for the old directory to finish synchronizing.
2. Open the original library and choose “将当前资料库迁移为文件夹包” in Settings.
3. Choose a new empty ArtHub sync directory outside the original library. The application generates and validates a migration copy while retaining the original.
4. Verify folders, records, images and history with a compatible client, then point other computers to the same new project. Older clients cannot directly use it.
5. Reopen the retained library to roll back if needed. Export and preserve post-migration changes separately; they are not automatically written back to the original library.

Existing AI search caches are local data. Switching projects may require rebuilding the image index, without affecting original images or records.

## History, checkpoints and file counts

View commit history in Settings. Restoring historical records creates local drafts; manual submission is required to publish them to other computers.

History maintenance first creates a checkpoint and then allows manual cleanup of covered packages and logs. Before cleanup, the retained checkpoint and its packages are revalidated in the sync directory. **Verify that team computers have received the checkpoint, ArtHub has completed transfer and backups are retained before cleanup.** The application cannot confirm ArtHub cloud completion itself.

A long-offline client with missing predecessors waits first. A complete late commit can be manually imported as drafts, reviewed and submitted. Checkpoint cleanup is not a global distributed lock.

## Current limits

- A package is limited to 3 GB of extracted data, 30,000 entries and 32 MiB of metadata. Commit logs are limited to 1 MiB. Log size grows with submission scope and is not guaranteed to be only a few KB.
- Initial imports of large libraries can take time. Local demonstrations are not benchmarks for indexing thousands of images, low-end hardware or real network transfers.
- Image loading from deeply nested Windows cache paths has been fixed; originals do not need to be moved or uploaded again.
- This mode does not share AI indexes, open shared SQLite/LanceDB databases concurrently, or expose an ArtHub cloud-status API.

[中文首页](../README.md) · [English home](../README.en.md)
