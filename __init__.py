# --------------------------------------------------------------------------------
# Copyright (c) 2026 Greenlex Systems Services Incorporated. All rights reserved.
#
# Licensed under the GNU General Public License (GPL).
# Original Architecture & Logic by Greenlex Systems Services Incorporated.
#
# No person or organization is authorized to misrepresent this work or claim
# original authorship for themselves. Proper attribution is mandatory.
# --------------------------------------------------------------------------------

bl_info = {
    "name": "Layouts & Systems Draftsman Toolkit",
    "author": "Greenlex Systems Services Incorporated",
    "version": (1, 4, 0),
    "blender": (5, 1, 2),
    "location": "View3D > Sidebar > Layouts & Systems Toolkit",
    "description": "A comprehensive toolkit for native, non-destructive URDF creation and rigging for ROS/Gazebo.",
    "category": "Import-Export",
    "doc_url": "https://github.com/Japzon/Layouts-Systems-Draftsman-Toolkit-Addon.git",
    "tracker_url": "https://github.com/Japzon/Layouts-Systems-Draftsman-Toolkit-Addon/issues",
}

# Project Task: Robust Registration System (Project Task 1.1.2)
# Handles module reloading to prevent 'ghost' notifications in Preferences.
if "bpy" in locals():
    import importlib
    if "core" in locals(): importlib.reload(core)
    if "properties" in locals(): importlib.reload(properties)
    if "operators" in locals(): importlib.reload(operators)
    if "panels" in locals(): importlib.reload(panels)
    if "config" in locals(): importlib.reload(config)
    if "anim_onion_skin" in locals(): importlib.reload(anim_onion_skin)
    if "anim_library" in locals(): importlib.reload(anim_library)
import bpy
from . import config
from . import core
from . import properties
from . import operators
from . import panels
from . import anim_onion_skin
from . import anim_library

addon_keymaps = []


def register():
    # 0. Hard Registry Cleanup - Clears the persistent 'Missing Add-ons' warning
    try:
        legacy_ids = ["fabrication_construction_draftsman_tools", "fabrication_construction_draftman_tools", "Fabrication_Construction_Draftsman_Tools_Blender_Addon"]
        addon_prefs = bpy.context.preferences.addons
        for old_id in legacy_ids:
            if old_id in addon_prefs: # Standard ID check
                 try: addon_prefs.remove(addon_prefs[old_id])
                 except: pass # Fallback
                 print(f"[LSD] Registry Purge: Cleared ghost '{old_id}'.")
    except:
        pass
    # 1. Properties - Scene attributes must exist before operators/panels call them
    properties.register()
    # 2. Operators - Register commands
    operators.register()
    # 3. Core - Handlers and logic
    core.register()
    panels.register()
    anim_onion_skin.register()
    anim_library.register()
    
    # 5. Keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new("lsd.directional_translate", 'G', 'PRESS')
        addon_keymaps.append((km, kmi))
        
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new("lsd.directional_translate", 'G', 'PRESS')
        addon_keymaps.append((km, kmi))
        
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new("lsd.global_math_input", 'EQUAL', 'PRESS')
        addon_keymaps.append((km, kmi))
def unregister():
    # Unregister in reverse order with broad exception handling
    # to prevent "ghost" entries in the addon list if one module fails.
    try:
        panels.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Panels): {e}")
    
    try:
        core.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Core): {e}")
        
    try:
        anim_onion_skin.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Onion Skin): {e}")
        
    try:
        anim_library.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Anim Library): {e}")
        
    try:
        operators.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Operators): {e}")
        
    try:
        properties.unregister()
    except Exception as e:
        print(f"[LSD] Unregister Warning (Properties): {e}")
        
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
if __name__ == "__main__":
    register()
