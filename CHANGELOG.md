# Changelog

## 1.0.2

Changed the strategy for detecting objects created during the session.

- Removed the `depsgraph_update_post` handler entirely. It ran on every
  scene re-evaluation just to catch a rare event, which is not an
  acceptable cost for what it did.
- Newly created objects are now resolved inside the rename sync pass
  that already runs only in response to an actual rename: since the
  name cache is rebuilt at registration and on every file load, any
  object missing from it appeared during the session, and is treated as
  just-renamed when it is part of the current selection.
- Added a cache rebuild on undo/redo, so an undo step cannot be
  mistaken for a rename. It fires only on undo/redo.
- Net effect: the add-on is now fully event-driven — no dependency
  graph handler, no polling timer, no per-frame work.

## 1.0.1

- Fixed the `website` field in the manifest, which pointed at a
  placeholder instead of the public source repository.
- Corrected the extension tags to match the actual scope of the add-on
  (`Object`, `Pipeline`).
- Fixed the sync stopping after `File > New` in an already running
  session: the msgbus subscription is now explicitly re-subscribed on
  every file load instead of relying on the `PERSISTENT` option alone.
- Multi-user (instanced) data is now renamed instead of skipped by
  default: renaming one instance updates every instance sharing the
  same data, and when several instances are renamed at once the active
  object's new name is used.
- Moved the enable/disable toggle to the Outliner header and reduced it
  to an icon-only button.

## 1.0.0

Initial version.

- Automatically renames an object's data (Mesh, Curve, Camera, Light,
  Armature, Text, Grease Pencil, Point Cloud, Volume, Hair Curves,
  Metaball, Lattice, Speaker, Light Probe, Surface) to match the object
  whenever it is renamed — via F2, Outliner double-click, or Ctrl+F2
  Batch Rename.
- Preferences: per object-type filter with matching Outliner icons,
  Select All / Deselect All, and an option to skip multi-user data.
