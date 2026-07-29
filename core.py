# ------------------------------------------------------------------------------------------
#  Copyright (c) Marco Caturano. All rights reserved.
#  Licensed under the GPLv3 License. See LICENSE in the project root for license information.
# ------------------------------------------------------------------------------------------

"""Core synchronization logic.

Strategy
--------
Blender does not expose a direct "on rename confirmed" event, but every
rename path (F2 in the viewport, double-click in the Outliner, and the
Ctrl+F2 batch rename tool) ends up doing the same thing under the hood:
writing to the RNA property `Object.name`. Instead of hooking every
operator individually, we subscribe to that property through `bpy.msgbus`.
This keeps us compatible with any current or future UI entry point that
performs the same underlying change (including renaming from the Python
console).

Race-condition / thread-safety notes
-------------------------------------
* `msgbus` notifications can fire from inside Blender's internal RNA
  update handling, where mutating `bpy.data` is not guaranteed to be
  safe. We never touch data directly inside the notify callback; we
  only set a "pending" flag and defer the actual work to
  `bpy.app.timers`, which runs on the next safe tick of the main loop.
* `bpy.msgbus` does not tell us *which* object changed, only that
  *some* `Object.name` changed. We keep a small cache keyed by
  `session_uid` (stable across renames, unlike the name itself) and
  diff the whole `bpy.data.objects` collection when the deferred sync
  runs. This makes the sync self-correcting no matter how many
  notifications were merged or in what order they arrived.
* A single boolean guard (`_sync_scheduled`) prevents stacking multiple
  redundant timers when many objects are renamed at once (e.g. batch
  rename). Blender's main loop is single threaded, so this guard is
  sufficient without needing an actual lock.
* The cache is rebuilt (without performing any rename) on add-on
  registration and on `load_post`, so opening a file that legitimately
  has mismatched object/data names never triggers a mass-rename.

Objects created during the session
-----------------------------------
Object creation (Add menu, duplicate, import, append, ...) does not
emit an `Object.name` notification, so a brand-new object is not in
`_name_cache` yet when the user renames it for the first time. Rather
than watching for new objects with a `depsgraph_update_post` handler
-- which would run on every scene re-evaluation and cost something on
every single update, forever, just to catch a rare event -- this is
resolved lazily, inside the sync pass that already runs *only* when a
rename actually happened:

Because the cache is fully rebuilt at registration and on every file
load, any object missing from the cache necessarily appeared during
the current session. When the sync runs, such an object is treated as
just-renamed if it is currently selected or active, and is otherwise
only recorded as a baseline. That selection test is reliable because
every rename entry point operates on the selection: F2 renames the
active object, an Outliner double-click makes its object active, and
Batch Rename acts on the selected objects.

The practical result is that this add-on costs literally nothing while
the user is not renaming anything -- no handler on the dependency
graph, no polling timer, no per-frame work.

Multi-user data (instances)
----------------------------
When several objects share the same object-data (e.g. Alt+D linked
duplicates), renaming that data-block updates the name shown for every
object using it -- there is nothing extra to "propagate", it is the
same datablock. The only real decision is *whose* new name wins when
more than one of those instances is renamed in the same pass (e.g. a
Ctrl+F2 batch rename applied to a multi-selection):
* One renamed instance in the group -> its new name is used.
* Several renamed instances in the group -> the active object's new
  name is used, so the result does not depend on iteration order.
See `_pick_rename_target()` for the exact rule.
"""

import bpy

from .data_types import OBJECT_DATA_TYPES, filter_property_name

# Unique, private owner token for our msgbus subscription.
_msgbus_owner = object()

# session_uid -> last known object name.
_name_cache = {}

# Debounce guard, see module docstring.
_sync_scheduled = False


def get_addon_preferences(context=None):
    """Return this add-on's AddonPreferences.

    Resolved via __package__ so it keeps working whether Blender loaded
    us as a legacy add-on ("object_data_autorename") or as a namespaced
    Extension ("bl_ext.<repo>.object_data_autorename").
    """
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences


def _is_type_enabled(prefs, object_type):
    return getattr(prefs, filter_property_name(object_type), True)


def _get_active_object():
    """Best-effort fetch of the current active object.

    Guarded because `bpy.context` inside a deferred timer callback may,
    in rare headless/background contexts, lack a view layer.
    """
    view_layer = getattr(bpy.context, "view_layer", None)
    return view_layer.objects.active if view_layer else None


def _get_selected_uids():
    """Return the session_uids of the selected objects plus the active one.

    Used to decide whether an object that is not yet in the name cache
    (i.e. one created during this session) is the subject of the rename
    that just triggered this sync. Every rename entry point acts on the
    selection, so this is a reliable signal -- see the module docstring.

    Guarded with getattr because `bpy.context` inside a deferred timer
    callback may lack these members in background/headless contexts.
    """
    uids = set()

    selected = getattr(bpy.context, "selected_objects", None)
    if selected:
        uids.update(obj.session_uid for obj in selected)

    active = _get_active_object()
    if active is not None:
        uids.add(active.session_uid)

    return uids


def _pick_rename_target(objects_in_group, active_object):
    """Choose whose new name should become the shared data's new name.

    * A single renamed object in the group: that object's new name wins
      (this is the common case: one instance renamed, its data -- and
      therefore every other instance sharing it -- follows).
    * Several renamed objects sharing the same data-block at once (e.g.
      a Ctrl+F2 batch rename applied to a multi-selection of
      instances): the currently active object's new name wins, so the
      result is predictable instead of depending on `bpy.data.objects`
      iteration order.
    * If, in that multi-object case, the active object is not part of
      this particular group (unusual edge case), fall back to a
      deterministic choice (alphabetically first new name) rather than
      an arbitrary one.
    """
    if len(objects_in_group) == 1:
        return objects_in_group[0]
    if active_object is not None and active_object in objects_in_group:
        return active_object
    return min(objects_in_group, key=lambda o: o.name)


def _sync_object_data_names():
    """Deferred, timer-driven pass that reconciles object/data names."""
    global _sync_scheduled
    _sync_scheduled = False

    prefs = get_addon_preferences()

    current_uids = set()
    renamed_objects = []
    unseen_objects = []

    for obj in bpy.data.objects:
        uid = obj.session_uid
        current_uids.add(uid)
        new_name = obj.name
        old_name = _name_cache.get(uid)

        # Always refresh the cache first so a later disabled/filtered
        # sync never leaves stale state behind.
        _name_cache[uid] = new_name

        if old_name is None:
            # Not in the cache: the object appeared during this session
            # (created, duplicated, imported, appended). Resolved below.
            unseen_objects.append(obj)
        elif old_name != new_name:
            renamed_objects.append(obj)

    # Prune objects that no longer exist to avoid unbounded growth.
    for uid in list(_name_cache.keys()):
        if uid not in current_uids:
            del _name_cache[uid]

    if not prefs.enabled:
        return None  # One-shot timer: do not repeat.

    if unseen_objects:
        # A rename just happened somewhere; any session-new object that
        # is part of the current selection is almost certainly its
        # subject, so treat it as renamed. Objects outside the selection
        # are left alone and keep only the baseline recorded above.
        selected_uids = _get_selected_uids()
        renamed_objects.extend(
            obj for obj in unseen_objects if obj.session_uid in selected_uids
        )

    if not renamed_objects:
        return None  # One-shot timer: do not repeat.

    # Group the objects that were just renamed by the object-data
    # block they share (keyed by the data-block's own session_uid,
    # stable regardless of its current name), so that instances of
    # the same multi-user data renamed together are resolved as one
    # decision instead of fighting each other.
    groups = {}
    for obj in renamed_objects:
        data = obj.data
        if data is None:
            continue
        if obj.type not in OBJECT_DATA_TYPES:
            continue
        if not _is_type_enabled(prefs, obj.type):
            continue
        groups.setdefault(data.session_uid, []).append(obj)

    active_object = _get_active_object()

    for data_uid, objects_in_group in groups.items():
        data = objects_in_group[0].data
        if data.users > 1 and prefs.skip_multiuser_data:
            continue
        target = _pick_rename_target(objects_in_group, active_object)
        if data.name != target.name:
            data.name = target.name

    return None  # One-shot timer: do not repeat.


def _on_object_name_changed():
    """msgbus notify callback. Never mutates data, only schedules work."""
    global _sync_scheduled
    if _sync_scheduled:
        return
    _sync_scheduled = True
    bpy.app.timers.register(_sync_object_data_names, first_interval=0.0)


def rebuild_cache_silently():
    """Repopulate the name cache without performing any rename.

    Used on add-on registration and on file load, where the current
    object names must become the new baseline instead of being treated
    as pending renames.
    """
    _name_cache.clear()
    for obj in bpy.data.objects:
        _name_cache[obj.session_uid] = obj.name
    return None  # One-shot timer compatible.


@bpy.app.handlers.persistent
def _on_undo_redo_post(scene, _unused=None):
    """Re-baseline the cache after an undo/redo step.

    Undo/redo restores a previous state of the whole blend data, which
    can bring objects back, remove them, or revert names. Rebuilding the
    baseline here keeps the cache honest and avoids acting on a diff
    that the user did not actually perform.

    This fires only when the user undoes or redoes something, so it adds
    no cost to normal interaction. The optional second parameter keeps
    the signature valid across Blender versions, which pass a varying
    number of arguments to application handlers.
    """
    rebuild_cache_silently()


def register_msgbus():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "name"),
        owner=_msgbus_owner,
        args=(),
        notify=_on_object_name_changed,
        options={'PERSISTENT'},
    )


def unregister_msgbus():
    bpy.msgbus.clear_by_owner(_msgbus_owner)


def register_undo_redo_handlers():
    for handlers in (bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if _on_undo_redo_post not in handlers:
            handlers.append(_on_undo_redo_post)


def unregister_undo_redo_handlers():
    for handlers in (bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        if _on_undo_redo_post in handlers:
            handlers.remove(_on_undo_redo_post)
