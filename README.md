<!--
------------------------------------------------------------------------------------------
 Copyright (c) Marco Caturano. All rights reserved.
 Licensed under the GPLv3 License. See LICENSE in the project root for license information.
------------------------------------------------------------------------------------------
-->

# Object Data Auto Rename

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Blender](https://img.shields.io/badge/Blender-4.5%2B-orange.svg)](https://www.blender.org/)
[![Extension](https://img.shields.io/badge/Blender-Extension-brightgreen.svg)](https://extensions.blender.org/)

Keeps every object-data block (Mesh, Curve, Camera, Light, Armature, Text,
Grease Pencil, Point Cloud, Volume, Hair Curves, Metaball, Lattice,
Speaker, Light Probe, Surface) named identically to the object that owns
it — automatically, on every rename.

## Why

Consistent object/data naming makes the Outliner easier to scan, asset
browsers easier to search, and any pipeline or script that relies on
naming conventions more reliable. Keeping the two in sync by hand is
tedious and easy to forget — this extension does it for you, every time.

## How it works

The sync triggers on any of the standard Blender rename workflows,
automatically:

- **F2** in the 3D Viewport
- **Double-click** in the Outliner
- **Ctrl+F2** Batch Rename tool

No operator to run, no manual step — object and data names simply stay
aligned as you work.

### Instances (multi-user data)

Renaming one instance of a shared (linked) object-data block updates
every other instance automatically, since they all point to the same
data-block. If several instances are renamed together (e.g. via Batch
Rename on a multi-selection), the **active object's** new name is used,
so the result is predictable rather than depending on internal ordering.

## Features

- 🔄 Automatic, event-driven sync — no polling, minimal performance
  impact (see [Performance](#performance) below).
- 🖱️ One-click toggle in the Outliner header to enable/disable the sync
  instantly, without disabling the extension.
- 🎛️ Preferences panel with a per object-type filter (icons match the
  Outliner's own data-block icons), plus Select All / Deselect All.
- 🔗 Correct handling of multi-user (instanced) data, with an option to
  skip it entirely if you prefer names to stay independent.
- ✅ Compatible with Blender 4.5 and 5.2.

## Installation

1. Download the latest release `.zip` from the
   [Releases](../../releases) page (or from the
   [Blender Extensions Platform](https://extensions.blender.org/) listing).
2. In Blender: drag & drop the `.zip` into the Blender window, or go to
   `Edit > Preferences > Get Extensions / Add-ons > Install from Disk...`
   and select the file.
3. Enable the extension if it isn't enabled automatically.

## Usage

- Toggle the sync on/off from the icon button in the **Outliner header**
  (right side, next to the filter / new collection / library icons).
- Open `Preferences > Add-ons > Object Data Auto Rename` to:
  - Enable/disable the sync globally.
  - Choose whether multi-user (shared) data should be skipped.
  - Filter which object types participate, with Select All / Deselect All.

## Performance

The sync is entirely event-driven (`bpy.msgbus` on `Object.name`, plus a
cheap object-count check on `depsgraph_update_post` to catch newly
created objects). There is no per-frame scanning and no polling. See the
[project wiki](../../wiki) / issue tracker for more detail if you're
profiling a very large scene.

## Contributing

Issues and pull requests are welcome. Please keep changes consistent
with the existing code style (English code and comments, license header
on every source file — see any `.py` file for the exact format).

## License

GNU General Public License v3.0 or later — see [LICENSE](LICENSE).

Copyright (c) 2026 Marco Caturano.
