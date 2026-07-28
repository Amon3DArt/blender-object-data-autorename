# ------------------------------------------------------------------------------------------
#  Copyright (c) Marco Caturano. All rights reserved.
#  Licensed under the GPLv3 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------

"""Object Data Auto Rename.

Keeps every object-data block (mesh, curve, camera, light, ...) named
identically to the object that owns it, whenever the object is renamed
via F2, Outliner double-click, or the Ctrl+F2 batch rename tool.
See core.py for the synchronization strategy and race-condition notes.
"""

import bpy

from . import core
from . import preferences
from . import ui


def register():
    preferences.register()
    core.register_msgbus()
    core.register_depsgraph_handler()
    ui.register()

    # Build the initial name-cache baseline without renaming anything.
    # Deferred via timer because bpy.data may not be fully ready at the
    # exact moment register() runs (e.g. during startup file load).
    bpy.app.timers.register(core.rebuild_cache_silently, first_interval=0.0)

    bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)

    ui.unregister()
    core.unregister_depsgraph_handler()
    core.unregister_msgbus()
    preferences.unregister()


@bpy.app.handlers.persistent
def _on_load_post(dummy):
    # A newly loaded file has an entirely different set of objects:
    # rebuild the baseline cache instead of diffing against the
    # previous file's state.
    core.rebuild_cache_silently()

    # Defensively re-subscribe msgbus on every file-load event
    # (File > New, Open, Revert, ...). `subscribe_rna`'s 'PERSISTENT'
    # option is meant to survive file loads, but this is not reliably
    # honored across every internal load code path (e.g. File > New /
    # read_homefile) on every Blender version -- explicitly clearing
    # and re-subscribing here guarantees the sync keeps working
    # regardless of that internal behavior.
    core.unregister_msgbus()
    core.register_msgbus()
