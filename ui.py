# ------------------------------------------------------------------------------------------
#  Copyright (c) Marco Caturano. All rights reserved.
#  Licensed under the GPLv3 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------

"""Outliner header integration.

Blender's Header/Menu ``append``/``prepend`` API only supports adding
content at the very start or the very end of a header's draw call --
there is no supported way to inject a widget at an arbitrary mid-row
position (the Outliner header is drawn in immediate mode, not as a
modifiable widget tree). Reconstructing the header from scratch to get
pixel-perfect placement would mean duplicating Blender's internal
source for `OUTLINER_HT_header`, which is fragile and version-specific
-- exactly what we want to avoid for 4.5/5.2 compatibility.

We therefore ``append`` to `OUTLINER_HT_header`, which places the
toggle at the far right of the header, right after the existing
filter / new collection / library icons.
"""

import bpy


def draw_header_toggle(self, context):
    prefs = context.preferences.addons[__package__].preferences
    layout = self.layout
    layout.separator(factor=1.0)
    layout.prop(
        prefs,
        "enabled",
        text="",
        icon='FONT_DATA',
        toggle=True,
    )


def register():
    bpy.types.OUTLINER_HT_header.append(draw_header_toggle)


def unregister():
    bpy.types.OUTLINER_HT_header.remove(draw_header_toggle)
