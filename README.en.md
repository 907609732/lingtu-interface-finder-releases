# Quick Interface Finder · Game UI Library and Local Image Search

[简体中文（默认）](README.md) | **English**

Organize game interface screenshots, engine names, Figma links and GM notes by system and folder. Find references through a table view, image albums and local visual similarity search.

[Downloads and releases](https://github.com/907609732/lingtu-interface-finder-releases/releases) · [Folder package sync guide](docs/folder-package-sync.en.md)

## Versions and downloads

Documentation updated on **2026-11-12**. Published packages and features under development are listed separately:

| Type                   | Version and link                                                                                                            | How to use                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Published extension    | [0.7.4 · AI资源领航 extension](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/extension-v0.7.4) | Import the extension ZIP into a compatible host                                  |
| Legacy standalone app  | [0.5.7 · EXE installer](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.7)                  | Legacy standalone installation and rollback                                      |
| Legacy offline trial   | [0.5.8 · Slim full trial](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.8)                | Download the matching offline EXE and all volumes                                |
| Separate AI models     | [TensorRT for RTX model package](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1)   | Import through model settings in compatible versions                             |
| Sync under development | [One package per folder with manual submission](docs/folder-package-sync.en.md)                                             | Verified in a local development build; not added to the published packages above |

GitHub's `releases/latest` currently points to the legacy standalone release. Use the dedicated **0.7.4 extension** link above for the extension. This documentation update does not upgrade existing packages or change the legacy update feed.

## Features

- **Structured reference tables:** organize systems, folders and subfolders; edit engine names, UI/stitching Figma links and GM notes directly in cells.
- **Images and albums:** view inline attachments and open full-size albums; rename images, confirm deletion and restore deleted items.
- **Browsing and filtering:** switch layouts, fields, filters and sorting; adjust column widths, row heights and table dimensions. Light theme is the default; a dark theme is available.
- **Screenshot search:** paste or select an image to search locally with Chinese-CLIP and DINOv2. Similarity scores rank candidates; they are not accuracy percentages.
- **Revisions and conflicts:** retain history and restore earlier versions; preserve conflicting branches when people edit the same record.
- **Local media previews:** preview images, video, audio and selected attachment formats, subject to the relevant release's format support.

## Install the 0.7.4 extension

1. Use an AI资源领航 host that implements the `hostApi: 1` workbench extension interface.
2. Download `quick-interface-finder-0.7.4-extension.zip` from the [0.7.4 release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/extension-v0.7.4).
3. Close the current Quick Interface Finder workbench. Import the ZIP through “更多功能 → 快速找界面” in the host's extension management UI. Do not extract it manually.
4. Open the workbench and select an existing library. Download or import the separate model package when you need AI image search.

This ZIP is a workbench extension, not a standalone EXE, a host installer or the `update.zip` expected by the legacy updater. Older hosts must first be upgraded to support the extension interface.

## Folder package sync: save locally, publish manually

> **Development feature.** The following workflow is not included in the published `extension-v0.7.4` ZIP or legacy 0.5.x installers. Do not open a new folder package project with an older client.

```text
Edit records → save local drafts → select folders and submit manually
             → changed folder ZIPs + commit JSON → ArtHub transfer
             → other computers validate and extract → local records update
```

Each folder package contains its own direct records and historical originals. Subfolders have separate packages, and project-wide records have their own package. Ordinary saves do not publish packages. Related changes, such as moves between folders, are submitted together.

On first connection, choose an ArtHub sync directory in Settings. Packages are validated and extracted into a separate local data directory. Editing remains available offline, and incoming updates preserve unsubmitted local drafts. **Each computer prepares its own AI models, image index and GPU cache; these are not synchronized with the data packages.**

See the [English sync guide](docs/folder-package-sync.en.md) for setup, migration, concurrent edits and history maintenance.

## Verified two-client demonstration

On 2026-11-12, two isolated local clients demonstrated this workflow:

| Stage                | Observed result                                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Edit one demo record | `任务追踪主界面.png` → `任务追踪主界面_人工提交演示.png`                                                        |
| Save a draft only    | Client A changed; client B retained the original name; no new sync files                                        |
| Submit manually      | Exactly one ZIP (47,883 bytes) and one JSON commit log (812 bytes) were added                                   |
| Receive on client B  | The new name appeared automatically; revision IDs and original image hashes matched; history remained available |

The demonstration used local file copying to simulate transport. **It was not a real ArtHub cloud or two-physical-computer acceptance test.** Successfully publishing to a sync directory does not confirm cloud upload completion.

One package per folder has a fixed overhead and may increase total file count in deeply divided libraries. Historical packages accumulate with submissions and can be cleaned up manually after validating a checkpoint.

## AI models and runtime requirements

- The current desktop target is Windows x64. The extension reuses the host's Electron runtime and includes its own inference runtime and media tools, without model weights or user data.
- Compatible TensorRT for RTX models target NVIDIA RTX 30/40/50 GPUs. The verified device is an RTX 3080 Ti; other GPUs require compatibility checks.
- Download online through “设置 → 本地 AI 模型”, or download a ZIP from the [model release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1) and import it offline. A separate Python, PyTorch or CUDA Toolkit installation is not required.
- Library management and text-field search work without models. Legacy PyTorch model folders cannot be imported directly into the RTX runtime.
- In folder package mode, each computer generates its own image index and can reuse its existing local cache.

## Legacy standalone installation and rollback

The [0.5.7 EXE installer](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-Setup.exe) downloads and verifies that legacy version's application, runtime and bundled models. Initial installation requires internet access; allow about 20 GiB of space including download caches. The legacy installer does not have a commercial code-signing certificate.

For offline use, download every matching `.7z.*` volume into one directory, extract from `.001` and keep the complete application directory. The 0.5.8 offline trial also requires the EXE and both data volumes listed on its release page. Existing 0.5.x users should follow their release's update instructions; an extension ZIP cannot replace a legacy update package.

Older release assets remain available for rollback. Folder package migration creates a copy in a new directory and retains the original library. Before reverting to that library, preserve any changes made after migration separately.

## Data and distribution boundaries

This public repository distributes releases, documentation and release assembly scripts. It does not publish an application source archive. User libraries, local settings, recognition databases and model weights are not uploaded with this documentation update.

Checksums, licenses, signing status and tested hardware are documented in the corresponding release and package. Real ArtHub transfer between computers, placeholder downloads, low-end hardware and large-library performance still require separate acceptance testing.

---

[简体中文](README.md) · [Folder package sync guide](docs/folder-package-sync.en.md) · [All releases](https://github.com/907609732/lingtu-interface-finder-releases/releases)
