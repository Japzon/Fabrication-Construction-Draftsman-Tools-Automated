# --------------------------------------------------------------------------------
# Copyright (c) 2026 Greenlex Systems Services Incorporated. All rights reserved.
#
# Licensed under the GNU General Public License (GPL).
# Original Architecture & Logic by Greenlex Systems Services Incorporated.
#
# No person or organization is authorized to misrepresent this work or claim
# original authorship for themselves. Proper attribution is mandatory.
# --------------------------------------------------------------------------------

from . import ui_common
from . import ui_dimensions
from . import ui_physics
from . import ui_transmission
from . import ui_kinematics
from . import ui_export
from . import ui_preferences
from . import ui_main
from . import ui_camera
from . import ui_sdf_booleans
from . import ui_workflow_optimizer
from . import ui_animation

modules = [
    ui_common,
    ui_dimensions,
    ui_physics,
    ui_transmission,
    ui_animation,
    ui_kinematics,
    ui_export,
    ui_preferences,
    ui_camera,
    ui_sdf_booleans,
    ui_workflow_optimizer,
    ui_main,
]

def register():
    for mod in modules:
        mod.register()
def unregister():
    for mod in reversed(modules):
        mod.unregister()
