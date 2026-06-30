import sys

filepath = r'c:\Users\japzo\OneDrive\Desktop\Blender Add-on Workshop\Layouts-Systems-Draftsman-Toolkit-Addon\operators.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = "cutter.display_type = 'BOUNDS'"
replacement = "cutter.display_type = 'TEXTURED'"

if target in content:
    content = content.replace(target, replacement, 1) # only replace the first one in Quick Boolean
    with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)
    print('SUCCESS')
else:
    print('TARGET NOT FOUND')
