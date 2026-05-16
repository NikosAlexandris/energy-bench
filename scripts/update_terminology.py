#!/usr/bin/env python3
"""
Script to update source-specific terminology to generic terms across the codebase.

This script replaces ENTSO-E/SFOE references with generic indicator/target terminology
to support the source-agnostic design principle.
"""

import re
from pathlib import Path

# Replacement patterns (case-insensitive)
REPLACEMENTS = [
    # In docstrings and comments
    (r'\bENTSO-E hourly\b', 'hourly indicator'),
    (r'\bSFOE daily\b', 'daily target'),
    (r'\bENTSO-E\b', 'indicator source'),
    (r'\bSFOE\b', 'target source'),
    
    # Variable names in examples
    (r'\bentsoe_data\b', 'indicator_data'),
    (r'\bsfoe_data\b', 'target_data'),
    (r'\bentsoe_hourly\b', 'hourly_indicator'),
    (r'\bsfoe_daily\b', 'daily_target'),
    (r'\bentsoe_csv\b', 'indicator_csv'),
    (r'\bsfoe_csv\b', 'target_csv'),
    
    # In help text
    (r'e\.g\.,?\s+ENTSO-E', 'e.g., indicator'),
    (r'e\.g\.,?\s+SFOE', 'e.g., target'),
]

def update_file(file_path: Path) -> tuple[bool, int]:
    """Update terminology in a single file.
    
    Returns:
        (changed, num_replacements): Whether file was changed and number of replacements
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        replacements = 0
        
        for pattern, replacement in REPLACEMENTS:
            new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
            if count > 0:
                content = new_content
                replacements += count
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True, replacements
        return False, 0
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def main():
    """Update terminology in all Python files."""
    root = Path(__file__).parent.parent
    src_dir = root / "src" / "energybench"
    
    # Files to update
    target_files = [
        # Commands
        "commands/scale/advanced.py",
        "commands/scale/simple.py",
        "commands/list.py",
        "commands/analyse/bias.py",
        "commands/analyse/methods.py",
        "commands/benchmark/storage.py",
        "commands/benchmark/nuclear.py",
        "commands/benchmark/water.py",
        "commands/benchmark/river.py",
        "commands/compare/series.py",
        "commands/compare/app.py",
        "commands/compare/scaled_vs_target.py",
        "commands/plot/original_vs_target.py",
        # Library modules
        "compare/shape.py",
        "analyse/bias_detection.py",
        "validate/plot.py",
        "models/disaggregation.py",
    ]
    
    total_files = 0
    total_replacements = 0
    
    print("Updating terminology in Python files...")
    print("=" * 60)
    
    for rel_path in target_files:
        file_path = src_dir / rel_path
        if file_path.exists():
            changed, count = update_file(file_path)
            if changed:
                total_files += 1
                total_replacements += count
                print(f"✓ {rel_path}: {count} replacements")
        else:
            print(f"✗ {rel_path}: not found")
    
    print("=" * 60)
    print(f"Updated {total_files} files with {total_replacements} total replacements")

if __name__ == "__main__":
    main()
