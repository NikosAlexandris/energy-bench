# Energy-Bench Project Consolidation Analysis

**Date:** 2026-05-16  
**Status:** Draft for Review  
**Purpose:** Identify opportunities to simplify, deduplicate, and harmonize the codebase

---

## Executive Summary

This analysis reviews the Energy-Bench project to identify areas for consolidation, deduplication, and terminology harmonization. The project is well-structured with a modular CLI architecture, but there are opportunities to improve consistency and reduce complexity.

**Key Findings:**
- ✅ Strong modular architecture with clear separation of concerns
- ⚠️ Duplicate helper functions (`sum_columns` vs `safe_sum_series`)
- ⚠️ Inconsistent parameter naming across commands (18 files use same parameters)
- ⚠️ Mixed terminology (high/low frequency vs indicator/target)
- ⚠️ Repetitive command structure across 7 energy types
- ✅ Good centralized configuration in `variables.py`

---

## 1. Project Structure Overview

### Core Architecture

```
src/energybench/
├── cli.py              # Main CLI entrypoint (cyclopts)
├── benchmark.py        # Core benchmarking logic
├── variables.py        # Energy type configuration registry
├── helpers.py          # Utility functions
├── io/
│   ├── input.py       # CSV reading with polars
│   └── output.py      # Centralized output saving
├── models/
│   └── scaling.py     # Scaling algorithms
├── commands/          # CLI subcommands
│   ├── benchmark/     # 7 energy-type commands
│   ├── compare/       # Comparison operations
│   ├── plot/          # Visualization
│   ├── scale/         # Scaling operations
│   ├── validate/      # Validation logic
│   └── analyse/       # Analysis tools
└── compare/           # Series comparison utilities
```

### Strengths

1. **Modular CLI Design**: Clean separation using cyclopts
2. **Centralized Configuration**: `VARIABLES` registry in `variables.py`
3. **Centralized I/O**: `io/input.py` and `io/output.py` provide consistent interfaces
4. **Type Safety**: Uses enums and type hints
5. **Documentation**: Good inline documentation and AGENTS.md

---

## 2. Duplicate Functions Analysis

### 2.1 Helper Functions: `sum_columns` vs `safe_sum_series`

**Location:** `src/energybench/helpers.py`

#### Current State

Two nearly identical functions exist:

```python
# Function 1: sum_columns (lines 5-24)
def sum_columns(
    df: pd.DataFrame,
    columns: list[str],
    label: str,
    factor: float = 1.0,
) -> pd.Series:
    """Sum specified columns, warning about missing but using available ones."""
    # Implementation...

# Function 2: safe_sum_series (lines 27-51)
def safe_sum_series(
    df: pd.DataFrame,
    value_columns: list[str],
    series_name: str,
) -> pd.Series:
    """
    Safely sum specified columns, filtering to those that exist.
    Warns about missing columns but continues with available ones.
    """
    # Nearly identical implementation...
```

#### Usage Analysis

- **`sum_columns`**: Used in 18 locations across 8 files
  - `benchmark.py` (2 uses)
  - `compare/shape.py` (2 uses)
  - `experiments/kalman_demo.py` (2 uses)
  - `commands/compare/series.py` (1 use)
  - `commands/compare/scaled_vs_target.py` (1 use)
  - `commands/analyse/bias.py` (2 uses)

- **`safe_sum_series`**: Used in 2 locations
  - `commands/plot/original_vs_target.py` (1 use)

#### Differences

1. **Parameter names**: `label` vs `series_name`, `columns` vs `value_columns`
2. **Factor parameter**: `sum_columns` has optional `factor` parameter (unused in codebase)
3. **Implementation**: Identical logic, just different naming

#### Recommendation

**CONSOLIDATE** into single function:

```python
def sum_columns(
    df: pd.DataFrame,
    columns: list[str],
    name: str,
    factor: float = 1.0,
) -> pd.Series:
    """
    Sum specified columns with graceful handling of missing columns.
    
    Args:
        df: Input DataFrame
        columns: Column names to sum
        name: Name for resulting Series
        factor: Optional scaling factor (default: 1.0)
    
    Returns:
        Series with summed values
        
    Raises:
        ValueError: If no columns found
        
    Warns:
        If some requested columns are missing
    """
```

**Action Items:**
1. Keep `sum_columns` as the canonical function
2. Remove `safe_sum_series` 
3. Update 2 call sites in `commands/plot/original_vs_target.py`
4. Remove unused `factor` parameter if not needed (check usage)

---

## 3. Terminology Inconsistencies

### 3.1 Parameter Naming Across Commands

**Issue:** 18 command files use identical parameter sets but with inconsistent naming conventions.

#### Current Parameter Names

Commands use these parameter names:
- `high_frequency_csv` / `low_frequency_csv`
- `high_frequency_datetime_column` / `low_frequency_datetime_column`
- `high_frequency_series` / `low_frequency_series`

#### Terminology Conflicts

The codebase mixes two naming conventions:

**Convention 1: Frequency-based** (used in function signatures)
- `high_frequency_*` = hourly data
- `low_frequency_*` = daily data

**Convention 2: Role-based** (used in documentation and internal logic)
- `indicator` = high-frequency data to be adjusted (ENTSO-E)
- `target` = low-frequency reference data (SFOE)

#### From AGENTS.md

The documentation explicitly prefers role-based terminology:

```
Preferred terminology:
- target: Low-frequency reference data (SFOE daily totals)
- indicator: High-frequency data to be adjusted (ENTSO-E hourly)
- adjusted / benchmarked: Output after temporal disaggregation
- original: Unadjusted high-frequency data
```

#### Recommendation

**HARMONIZE** to role-based terminology throughout:

**Before:**
```python
def benchmark(
    variable: str,
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    ...
)
```

**After:**
```python
def benchmark(
    variable: str,
    indicator_csv: Path,           # ENTSO-E hourly data
    target_csv: Path,              # SFOE daily data
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    ...
)
```

**Benefits:**
1. Aligns with documentation and domain language
2. More intuitive for users (indicator = what we adjust, target = what we match)
3. Shorter parameter names
4. Consistent with internal variable names

**Impact:** 18 files need parameter renaming (but backward compatibility can be maintained with deprecation warnings)

---

### 3.2 Configuration Keys in `variables.py`

**Current State:**

```python
cfg["target_type"]              # SFOE column names
cfg["indicator_type"]           # ENTSO-E column names
cfg["target_types_present"]     # Available SFOE columns
cfg["indicator_types_present"]  # Available ENTSO-E columns
```

**Also has legacy keys:**
```python
cfg["entsoe_types"]  # Same as indicator_type
cfg["sfoe_types"]    # Same as target_type
```

#### Recommendation

**KEEP** current structure but clarify documentation:
- `target_type` / `indicator_type` are canonical
- `entsoe_types` / `sfoe_types` are for configuration only
- Add clear docstrings explaining the distinction

---

## 4. Command Structure Duplication

### 4.1 Benchmark Commands

**Issue:** 7 nearly identical command files in `commands/benchmark/`:
- `nuclear.py`, `water.py`, `river.py`, `storage.py`, `solar.py`, `wind.py`, `thermal.py`

#### Current Pattern

Each file follows this template:

```python
from pathlib import Path
from cyclopts import App
from pandas import Timestamp
from energybench.benchmark import benchmark
from energybench.io.output import save_dataframe, build_filename

app = App(help="Benchmark {energy_type} generation...")

@app.default
def {energy_type}(
    high_frequency_csv: Path,
    low_frequency_csv: Path,
    start: Timestamp,
    end: Timestamp,
    high_frequency_datetime_column: str = "DateTime",
    low_frequency_datetime_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
):
    """Benchmark {energy_type} generation..."""
    variable = '{energy_type}'
    benchmarked_dataframe = benchmark(...)
    filename = build_filename(...)
    save_dataframe(...)
```

**Differences:** Only the variable name and help text change.

#### Recommendation

**Option A: Keep Current Structure** (Recommended)
- ✅ Explicit and easy to understand
- ✅ Each energy type can have custom parameters if needed
- ✅ Clear help text per energy type
- ⚠️ Some duplication but manageable

**Option B: Generate Commands Dynamically**
```python
# In cli.py
for var_name, var_config in VARIABLES.items():
    create_benchmark_command(var_name, var_config)
```
- ✅ Less duplication
- ⚠️ Less explicit, harder to customize
- ⚠️ Harder to debug

**Decision:** Keep current structure but ensure consistency in:
1. Parameter order
2. Help text format
3. Error handling

---

### 4.2 Scale Commands

**Location:** `commands/scale/`

Two scaling methods with similar signatures:
- `simple.py`: Basic proportional scaling
- `advanced.py`: Scaling with constraints (min_value, preserve_zeros)

#### Current State

Both functions have nearly identical structure:

```python
def scale_high_frequency_series(...)  # simple.py
def scale_high_frequency_series_advanced(...)  # advanced.py
```

#### Recommendation

**CONSOLIDATE** into single function with method parameter:

```python
def scale_series(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    method: str = "simple",  # or "advanced"
    min_value: float = 0.0,
    preserve_zeros: bool = True,
    ...
)
```

Or keep separate but ensure consistent naming and documentation.

---

## 5. Output Management

### 5.1 Current State

**Strengths:**
- Centralized in `io/output.py`
- Consistent functions: `save_dataframe()`, `save_figure()`, `save_text()`
- Automatic directory creation
- Standardized filename building with `build_filename()`

**Issues:**
- Some commands still construct filenames manually
- Inconsistent use of `variable` subdirectories

#### Recommendation

**ENFORCE** consistent output patterns:

1. **Always use `build_filename()`** for filename construction
2. **Always use `save_*()` functions** instead of direct pandas/matplotlib calls
3. **Document output structure** in README

---

## 6. Function Signature Patterns

### 6.1 Common Parameter Sets

Many commands share these parameters:

```python
# Data source parameters (18 files)
high_frequency_csv: Path
low_frequency_csv: Path
start: Timestamp
end: Timestamp
high_frequency_datetime_column: str = "DateTime"
low_frequency_datetime_column: str = "Date"
output_dir: Path = Path("output")
```

#### Recommendation

**CREATE** parameter groups using dataclasses or TypedDict:

```python
from dataclasses import dataclass
from pathlib import Path
from pandas import Timestamp

@dataclass
class DataSourceParams:
    """Common parameters for data source specification."""
    indicator_csv: Path
    target_csv: Path
    start: Timestamp
    end: Timestamp
    indicator_time_column: str = "DateTime"
    target_time_column: str = "Date"
    output_dir: Path = Path("output")
```

**Benefits:**
1. Single source of truth for parameter definitions
2. Easier to maintain consistency
3. Better type checking
4. Reusable across commands

---

## 7. Code Quality Observations

### 7.1 Strengths

1. **Type Hints**: Good use of type hints throughout
2. **Error Handling**: Graceful handling of missing columns
3. **Warnings**: Informative warnings for data quality issues
4. **Documentation**: Good docstrings and inline comments
5. **Testing**: Pandas optimizations enabled (`copy_on_write`, `infer_string`)

### 7.2 Areas for Improvement

1. **Commented Code**: Some files have commented-out code (e.g., `benchmark.py` lines 42-43, 52-53)
2. **Magic Numbers**: Some hardcoded values (e.g., `warn_threshold=10.0`, `min_daily_sum=0.01`)
3. **Configuration**: Could move more constants to configuration file

---

## 8. Prioritized Recommendations

### High Priority (Quick Wins)

1. **Remove `safe_sum_series` function** (2 call sites to update)
   - Impact: Low
   - Effort: 1 hour
   - Benefit: Reduced confusion, cleaner API

2. **Remove commented code** in `benchmark.py`
   - Impact: Low
   - Effort: 15 minutes
   - Benefit: Cleaner codebase

3. **Document output structure** in README
   - Impact: Medium
   - Effort: 30 minutes
   - Benefit: Better user understanding

### Medium Priority (Consistency Improvements)

4. **Harmonize parameter names** to role-based terminology
   - Impact: High (18 files)
   - Effort: 4-6 hours
   - Benefit: Better alignment with documentation, clearer intent
   - Note: Can maintain backward compatibility with deprecation warnings

5. **Create parameter dataclasses** for common parameter groups
   - Impact: Medium
   - Effort: 2-3 hours
   - Benefit: Better maintainability, type safety

6. **Consolidate scaling functions** into single interface
   - Impact: Medium
   - Effort: 2-3 hours
   - Benefit: Simpler API, less duplication

### Low Priority (Nice to Have)

7. **Move magic numbers to configuration**
   - Impact: Low
   - Effort: 1-2 hours
   - Benefit: More configurable, easier to tune

8. **Add integration tests** for command workflows
   - Impact: Medium
   - Effort: 8-12 hours
   - Benefit: Better confidence in refactoring

---

## 9. Implementation Plan

### Phase 1: Quick Wins (1-2 hours)

```markdown
- [ ] Remove `safe_sum_series` function
- [ ] Update 2 call sites in `commands/plot/original_vs_target.py`
- [ ] Remove commented code in `benchmark.py`
- [ ] Add output structure documentation to README
```

### Phase 2: Terminology Harmonization (4-6 hours)

```markdown
- [ ] Create deprecation plan for parameter names
- [ ] Update function signatures (18 files)
- [ ] Update documentation
- [ ] Add deprecation warnings for old parameter names
- [ ] Update examples in README and AGENTS.md
```

### Phase 3: Structural Improvements (4-6 hours)

```markdown
- [ ] Create parameter dataclasses
- [ ] Consolidate scaling functions
- [ ] Move magic numbers to configuration
- [ ] Update command implementations
```

### Phase 4: Testing & Validation (2-4 hours)

```markdown
- [ ] Test all commands with new parameter names
- [ ] Verify backward compatibility
- [ ] Update integration tests
- [ ] Performance testing
```

---

## 10. Risk Assessment

### Low Risk Changes
- Removing `safe_sum_series` (only 2 call sites)
- Removing commented code
- Documentation updates

### Medium Risk Changes
- Parameter renaming (many files, but can maintain compatibility)
- Creating parameter dataclasses (requires careful testing)

### High Risk Changes
- Consolidating scaling functions (changes API surface)
- Dynamic command generation (changes architecture)

---

## 11. Backward Compatibility Strategy

For parameter renaming, use this pattern:

```python
def benchmark(
    variable: str,
    indicator_csv: Path | None = None,
    target_csv: Path | None = None,
    # Deprecated parameters
    high_frequency_csv: Path | None = None,
    low_frequency_csv: Path | None = None,
    **kwargs
):
    """Benchmark energy generation time series."""
    
    # Handle deprecated parameters
    if high_frequency_csv is not None:
        warnings.warn(
            "Parameter 'high_frequency_csv' is deprecated, use 'indicator_csv' instead",
            DeprecationWarning,
            stacklevel=2
        )
        indicator_csv = indicator_csv or high_frequency_csv
    
    if low_frequency_csv is not None:
        warnings.warn(
            "Parameter 'low_frequency_csv' is deprecated, use 'target_csv' instead",
            DeprecationWarning,
            stacklevel=2
        )
        target_csv = target_csv or low_frequency_csv
    
    # Validate required parameters
    if indicator_csv is None or target_csv is None:
        raise ValueError("Both indicator_csv and target_csv are required")
    
    # Continue with implementation...
```

---

## 12. Success Metrics

### Code Quality Metrics
- Reduce duplicate code by ~15%
- Improve naming consistency to 100%
- Reduce parameter count through dataclasses

### User Experience Metrics
- Clearer parameter names (user survey)
- Better documentation coverage
- Fewer support questions about terminology

### Maintainability Metrics
- Faster onboarding for new contributors
- Easier to add new energy types
- Reduced cognitive load

---

## Appendix A: File Impact Analysis

### Files Requiring Changes (by Priority)

**High Priority:**
- `src/energybench/helpers.py` (remove duplicate function)
- `src/energybench/commands/plot/original_vs_target.py` (update call sites)
- `src/energybench/benchmark.py` (remove commented code)

**Medium Priority (Parameter Renaming):**
- `src/energybench/benchmark.py`
- `src/energybench/commands/benchmark/*.py` (7 files)
- `src/energybench/commands/scale/*.py` (2 files)
- `src/energybench/commands/compare/*.py` (3 files)
- `src/energybench/commands/plot/*.py` (2 files)
- `src/energybench/commands/validate/*.py` (2 files)
- `src/energybench/commands/analyse/*.py` (2 files)
- `src/energybench/commands/kalman.py`

**Total:** 22 files requiring updates for full harmonization

---

## Appendix B: Terminology Mapping

| Current Term | Recommended Term | Rationale |
|--------------|------------------|-----------|
| `high_frequency_csv` | `indicator_csv` | Aligns with domain language |
| `low_frequency_csv` | `target_csv` | Clearer intent |
| `high_frequency_datetime_column` | `indicator_time_column` | Shorter, clearer |
| `low_frequency_datetime_column` | `target_time_column` | Shorter, clearer |
| `high_frequency_series` | `indicator_series` | Consistent with CSV naming |
| `low_frequency_series` | `target_series` | Consistent with CSV naming |
| `high_frequency_indicator` | `indicator` | Redundant qualifier |
| `low_frequency_target` | `target` | Redundant qualifier |

---

## Conclusion

The Energy-Bench project has a solid foundation with good modular architecture and centralized configuration. The main opportunities for improvement are:

1. **Removing duplicate functions** (quick win)
2. **Harmonizing terminology** to match documentation (medium effort, high impact)
3. **Consolidating common patterns** through dataclasses (medium effort, medium impact)

These changes will make the codebase more maintainable, easier to understand, and better aligned with the documented conventions in AGENTS.md.

**Recommended Next Steps:**
1. Review this analysis with the team
2. Prioritize changes based on available time
3. Start with Phase 1 (quick wins)
4. Implement Phase 2 (terminology) with backward compatibility
5. Consider Phase 3 (structural) for future releases
