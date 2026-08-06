import ast
import re

target_classes = {'LSD_PG_Collision_Properties', 'LSD_PG_Material_Properties', 'LSD_PG_Transmission_Properties'}
target_funcs = {'update_collision_sync_all', 'update_collision_decimate', 'update_collision_thickness'}

def remove_nodes(filepath):
    with open(filepath, 'r') as f:
        source = f.read()

    tree = ast.parse(source)
    lines_to_remove = set()
    
    for node in tree.body:
        delete_node = False
        
        if isinstance(node, ast.ClassDef) and node.name in target_classes:
            delete_node = True
        elif isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            delete_node = True

        if delete_node:
            start = node.lineno
            end = getattr(node, 'end_lineno', start)
            if hasattr(node, 'decorator_list') and node.decorator_list:
                start = node.decorator_list[0].lineno
            for i in range(start, end + 1):
                lines_to_remove.add(i)

    if not lines_to_remove:
        return

    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    out = []
    for i, line in enumerate(lines, 1):
        if i not in lines_to_remove:
            out.append(line)
            
    with open(filepath, 'w') as f:
        f.writelines(out)

remove_nodes("properties.py")

with open("properties.py", "r") as f:
    content = f.read()

for cls in target_classes:
    content = re.sub(r',\s*' + cls, '', content)
    content = re.sub(cls + r'\s*,', '', content)

with open("properties.py", "w") as f:
    f.write(content)
