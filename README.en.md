# Quick Interface Finder · Game UI Library and Local Image Search

[简体中文（默认）](README.md) | **English**

Organize game interface screenshots, engine names, Figma links and GM notes by system and folder. Find references through a table view, image albums and local visual similarity search.

[Downloads and releases](https://github.com/907609732/lingtu-interface-finder-releases/releases) · [ArtHub direct folder sync guide](docs/folder-package-sync.en.md)

## Versions and downloads

Documentation updated on **2026-11-18**. Current downloads and historical versions:

| Type                   | Version and link                                                                                                            | How to use                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Current dual edition | [0.7.5 · Release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5) | Standalone APP ZIP / compatible-host extension ZIP |
| Published extension    | [0.7.4 · AI资源领航 extension](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/extension-v0.7.4) | Import the extension ZIP into a compatible host                                  |
| Legacy standalone app  | [0.5.7 · EXE installer](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.7)                  | Legacy standalone installation and rollback                                      |
| Legacy offline trial   | [0.5.8 · Slim full trial](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.8)                | Download the matching offline EXE and all volumes                                |
| Separate AI models     | [TensorRT for RTX model package](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1)   | Import through model settings in compatible versions                             |
| Direct folder sync | [ArtHub guide](docs/folder-package-sync.en.md) | Included in 0.7.5; legacy packages are read-only migration sources |

Use the dedicated **0.7.5 download links**. The historical `releases/latest` target and update feed remain unchanged for legacy updater compatibility. Neither full ZIP is a legacy incremental update package.

## Changes in 0.7.5

Direct normal-folder sync replaces manual package submission. Caches remain local. The release adds compact, theme-matched chrome, expandable field summaries, image previews in the local recycle bin and incremental AI index scheduling. [Cloud checks](https://github.com/907609732/lingtu-interface-finder-releases/actions/runs/44303948563) and a local run of the downloaded final APP and extension passed using isolated fixtures. Real ArtHub two-computer transfer and GPU inference were not exercised in this release acceptance.

## Features

- **Structured reference tables:** organize systems, folders and subfolders; edit engine names, UI/stitching Figma links and GM notes directly in cells.
- **Images and albums:** view inline attachments and open full-size albums; rename images, confirm deletion and restore deleted items.
- **Browsing and filtering:** switch layouts, fields, filters and sorting; adjust column widths, row heights and table dimensions. Light theme is the default; a dark theme is available.
- **Screenshot search:** paste or select an image to search locally with Chinese-CLIP and DINOv2. Similarity scores rank candidates; they are not accuracy percentages.
- **Revisions and conflicts:** retain history and restore earlier versions; preserve conflicting branches when people edit the same record.
- **Local media previews:** preview images, video, audio and selected attachment formats, subject to the relevant release's format support.

## Install the 0.7.5 extension

1. Use an AI资源领航 host that implements the `hostApi: 1` workbench extension interface.
2. Download `quick-interface-finder-0.7.5-extension.zip` from the [0.7.5 release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5).
3. Close the current Quick Interface Finder workbench. Import the ZIP through “更多功能 → 快速找界面” in the host's extension management UI. Do not extract it manually.
4. Open the workbench and select an existing library. Download or import the separate model package when you need AI image search.

This ZIP is a workbench extension, not a standalone EXE, a host installer or the `update.zip` expected by the legacy updater. Older hosts must first be upgraded to support the extension interface.

### Standalone APP

Download `quick-interface-finder-0.7.5-app-windows-x64.zip` from the [0.7.5 release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5), extract the entire folder and run “快速找界面.exe”. Use a separate directory from any running older version. See the [release notes](docs/0.7.5-版本说明.md) for changes and validation scope.

## Normal folder synchronized directly by ArtHub

> **Included in 0.7.5.** Historical `extension-v0.7.4` and 0.5.x packages do not include this workflow.

```text
Edit records → save directly into a normal folder (originals + immutable revisions)
             → ArtHub synchronizes that folder
             → other computers open the same folder and read records/history
```

Libraries no longer create folder ZIPs, commit logs or a manual publish step. There is no “Submit updates” button and no automatic extraction. Saving writes into the shared folder; ArtHub transfers it. **SQLite, query cache, thumbnails/previews, AI models and indexes, GPU caches, tasks and recycle stay on each computer and are never written into the shared folder.**

On first connection, select an existing ArtHub library folder or create a library in an empty folder. Concurrent edits to the same record keep conflict branches instead of silently overwriting.

Legacy `format 3 / folder-packages` projects are read-only migration sources. Opening one does not create an empty library. Use “Migrate legacy folder package to a normal library” explicitly. Migration copies to a side-by-side normal directory and verifies file hashes, revisions and originals. It preserves local uncommitted edits, conflicts, prepared/outgoing snapshots, remote-only commits and local recycle. A failure never switches the destination; old directories, packages, state, outgoing, archives and recycle are retained. See the [English sync and migration guide](docs/folder-package-sync.en.md).

## Historical implementation and acceptance limits

On 2026-11-12 an isolated development environment verified “one package per folder + manual submission,” including local draft retention, publishing one ZIP＋JSON, receiving on a second client, and matching revisions/original hashes. That daily workflow has been replaced by direct normal-folder synchronization; the record is historical only.

The old demonstration simulated transport with local file copying. **It was not a real ArtHub cloud or two-physical-computer acceptance test.** Direct-folder mode still needs real ArtHub two-machine, offline recovery and concurrent-sync acceptance. A successful directory write does not confirm cloud upload completion.

## AI models and runtime requirements

- The current desktop target is Windows x64. The extension reuses the host's Electron runtime and includes its own inference runtime and media tools, without model weights or user data.
- Compatible TensorRT for RTX models target NVIDIA RTX 30/40/50 GPUs. The verified device is an RTX 3080 Ti; other GPUs require compatibility checks.
- Download online through “设置 → 本地 AI 模型”, or download a ZIP from the [model release page](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1) and import it offline. A separate Python, PyTorch or CUDA Toolkit installation is not required.
- Library management and text-field search work without models. Legacy PyTorch model folders cannot be imported directly into the RTX runtime.
- In direct-folder mode, each computer generates its own image index, previews and feature cache; none of these are written into the ArtHub shared folder.

## Legacy standalone installation and rollback

The [0.5.7 EXE installer](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-Setup.exe) downloads and verifies that legacy version's application, runtime and bundled models. Initial installation requires internet access; allow about 20 GiB of space including download caches. The legacy installer does not have a commercial code-signing certificate.

For offline use, download every matching `.7z.*` volume into one directory, extract from `.001` and keep the complete application directory. The 0.5.8 offline trial also requires the EXE and both data volumes listed on its release page. Existing 0.5.x users should follow their release's update instructions; an extension ZIP cannot replace a legacy update package.

Older release assets remain available for rollback. Legacy folder-package migration creates a normal-library copy in a new directory and retains the old directory, packages, state and recycle. Before reverting, preserve any changes made after migration separately.

## Data and distribution boundaries

This public repository distributes releases, documentation and release assembly scripts. It does not publish an application source archive. User libraries, local settings, recognition databases and model weights are not uploaded with this documentation update.

Checksums, licenses, signing status and tested hardware are documented in the corresponding release and package. Real ArtHub transfer between computers, placeholder downloads, low-end hardware and large-library performance still require separate acceptance testing.

---

[简体中文](README.md) · [ArtHub direct folder sync guide](docs/folder-package-sync.en.md) · [All releases](https://github.com/907609732/lingtu-interface-finder-releases/releases)
