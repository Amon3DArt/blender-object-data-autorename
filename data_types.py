# ------------------------------------------------------------------------------------------
#  Copyright (c) Marco Caturano. All rights reserved.
#  Licensed under the GPLv3 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------

"""Central definition of the object types that own an object-data block.

Keeping this mapping in a single, dependency-free module avoids circular
imports between `core.py` (rename logic) and `preferences.py` (UI/filters).
"""

# Maps Object.type -> (human readable label, matching Outliner data-block icon).
# 'EMPTY' is intentionally excluded: Object.data is always None for empties,
# so there is nothing to rename.
OBJECT_DATA_TYPES = {
    'MESH': ("Mesh", 'OUTLINER_DATA_MESH'),
    'CURVE': ("Curve", 'OUTLINER_DATA_CURVE'),
    'SURFACE': ("Surface", 'OUTLINER_DATA_SURFACE'),
    'META': ("Metaball", 'OUTLINER_DATA_META'),
    'FONT': ("Text", 'OUTLINER_DATA_FONT'),
    'CURVES': ("Hair Curves", 'OUTLINER_DATA_CURVES'),
    'POINTCLOUD': ("Point Cloud", 'OUTLINER_DATA_POINTCLOUD'),
    'VOLUME': ("Volume", 'OUTLINER_DATA_VOLUME'),
    'GPENCIL': ("Grease Pencil (Legacy)", 'OUTLINER_DATA_GREASEPENCIL'),
    'GREASEPENCIL': ("Grease Pencil", 'OUTLINER_DATA_GREASEPENCIL'),
    'ARMATURE': ("Armature", 'OUTLINER_DATA_ARMATURE'),
    'LATTICE': ("Lattice", 'OUTLINER_DATA_LATTICE'),
    'LIGHT': ("Light", 'OUTLINER_DATA_LIGHT'),
    'LIGHT_PROBE': ("Light Probe", 'OUTLINER_DATA_LIGHTPROBE'),
    'CAMERA': ("Camera", 'OUTLINER_DATA_CAMERA'),
    'SPEAKER': ("Speaker", 'OUTLINER_DATA_SPEAKER'),
}


def filter_property_name(object_type: str) -> str:
    """Return the AddonPreferences BoolProperty name used for a given object type."""
    return f"filter_{object_type}"
