import os

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return

    # 1. Strip trailing whitespace and normalize
    lines = [line.rstrip() for line in lines]
    
    new_lines = []
    for i in range(len(lines)):
        line = lines[i]
        
        if line.strip():
            new_lines.append(line)
            continue
            
        # It's a blank line. Decide whether to keep it.
        if i == 0 or i == len(lines) - 1:
            continue # Skip blank lines at start/end
            
        prev_line = new_lines[-1] if new_lines else ""
        # Find next non-blank line
        next_line = ""
        for j in range(i + 1, len(lines)):
            if lines[j].strip():
                next_line = lines[j]
                break
        
        if not next_line:
            continue
            
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        next_indent = len(next_line) - len(next_line.lstrip())
        
        # Rule: No blank lines after a line ending in ':'
        if prev_line.strip().endswith(':'):
            continue
            
        # Rule: No consecutive blank lines (collapse to 1)
        if i > 0 and not lines[i-1].strip():
            continue
            
        # Rule: Inside a block (indent > 0), be very stingy with blank lines.
        # Only keep if it's a "top level" break within a class or similar,
        # but the user said "remove ALL whitespace between codes".
        # So let's only keep it if it's at indent 0 (between classes/functions).
        if prev_indent == 0 and next_indent == 0:
            new_lines.append('')
        else:
            # Inside a function or class: remove the blank line to "compact" the code
            # as requested to avoid "malformed edits".
            pass

    # Ensure exactly one blank line between top-level items
    # Actually, the loop above might have removed TOO many.
    # Let's do a second pass to ensure top-level items have a gap.
    
    final_lines = []
    for i in range(len(new_lines)):
        line = new_lines[i]
        final_lines.append(line)
        if i < len(new_lines) - 1:
            next_line = new_lines[i+1]
            # If both are at top level and are "big" blocks, add a gap
            if line.strip() and next_line.strip():
                if (line.startswith('def ') or line.startswith('class ') or line.startswith('# ---')) and \
                   (next_line.startswith('def ') or next_line.startswith('class ') or next_line.startswith('# ---')):
                    final_lines.append('')
                elif not line.startswith(' ') and (next_line.startswith('def ') or next_line.startswith('class ')):
                    final_lines.append('')

    # Write back
    content = '\n'.join(final_lines)
    # Final cleanup of triple-newlines just in case
    content = content.replace('\n\n\n', '\n\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content + '\n')

def main():
    targets = [
        'core.py',
        'operators.py',
        'generators.py',
        'properties.py',
        'config.py',
        '__init__.py',
        'dev_tool.py',
        'zip_addon.py'
    ]
    
    for t in targets:
        if os.path.exists(t):
            print(f"Aggressively cleaning {t}...")
            clean_file(t)
            
    panel_dir = 'panels'
    if os.path.exists(panel_dir):
        for f in os.listdir(panel_dir):
            if f.endswith('.py'):
                p = os.path.join(panel_dir, f)
                print(f"Aggressively cleaning {p}...")
                clean_file(p)

if __name__ == "__main__":
    main()
