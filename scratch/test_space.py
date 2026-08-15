import bpy

for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type != 'NLA_EDITOR':
            original = area.type
            area.type = 'NLA_EDITOR'
            
            found = False
            for space in area.spaces:
                print("Space found:", space.type)
                if space.type == 'NLA_EDITOR':
                    found = True
            
            print("NLA Space found in area.spaces:", found)
            area.type = original
            break
    break

import sys
sys.exit(0)
