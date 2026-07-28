# ------------------------------------------------------------------------------------------
#  Copyright (c) Marco Caturano. All rights reserved.
#  Licensed under the GPLv3 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------

"""Add-on preferences: master enable switch, multi-user data safety
switch, and a per object-type filter with Select All / Deselect All
convenience operators.
"""

import bpy
from bpy.types import AddonPreferences, Operator
from bpy.props import BoolProperty

from .data_types import OBJECT_DATA_TYPES, filter_property_name


class OBJECTDATAAUTORENAME_OT_select_all_types(Operator):
    """Enable auto-rename for every object type"""
    bl_idname = "object_data_autorename.select_all_types"
    bl_label = "Select All"
    bl_options = {'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        for object_type in OBJECT_DATA_TYPES:
            setattr(prefs, filter_property_name(object_type), True)
        return {'FINISHED'}


class OBJECTDATAAUTORENAME_OT_deselect_all_types(Operator):
    """Disable auto-rename for every object type"""
    bl_idname = "object_data_autorename.deselect_all_types"
    bl_label = "Deselect All"
    bl_options = {'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        for object_type in OBJECT_DATA_TYPES:
            setattr(prefs, filter_property_name(object_type), False)
        return {'FINISHED'}


class OBJECTDATAAUTORENAME_AddonPreferences(AddonPreferences):
    # Must match the add-on's own package id so Blender can resolve it
    # both as a legacy add-on and as a namespaced Extension.
    bl_idname = __package__

    enabled: BoolProperty(
        name="Enable Auto Rename",
        description="When enabled, renaming an object also renames its object-data to match",
        default=True,
    )

    skip_multiuser_data: BoolProperty(
        name="Skip Multi-User Data",
        description=(
            "Do not rename object-data shared (linked) by more than one object. "
            "When disabled (default), renaming an instance renames the shared data too "
            "(updating every other instance); if several instances are renamed at once, "
            "the active object's new name is used"
        ),
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.prop(self, "enabled")
        col.prop(self, "skip_multiuser_data")

        layout.separator()
        layout.label(text="Auto-Rename by Object Type:")

        row = layout.row(align=True)
        row.operator(OBJECTDATAAUTORENAME_OT_select_all_types.bl_idname, icon='CHECKBOX_HLT')
        row.operator(OBJECTDATAAUTORENAME_OT_deselect_all_types.bl_idname, icon='CHECKBOX_DEHLT')

        grid = layout.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for object_type, (label, icon) in OBJECT_DATA_TYPES.items():
            grid.prop(self, filter_property_name(object_type), text=label, icon=icon)


classes = (
    OBJECTDATAAUTORENAME_OT_select_all_types,
    OBJECTDATAAUTORENAME_OT_deselect_all_types,
    OBJECTDATAAUTORENAME_AddonPreferences,
)


def register():
    # Dynamically attach one BoolProperty per object-data type before the
    # class is registered, instead of hand-maintaining a long, easily
    # out-of-sync, duplicated list of properties.
    for object_type, (label, icon) in OBJECT_DATA_TYPES.items():
        OBJECTDATAAUTORENAME_AddonPreferences.__annotations__[filter_property_name(object_type)] = BoolProperty(
            name=label,
            description=f"Auto-rename object-data for {label} objects",
            default=True,
        )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
