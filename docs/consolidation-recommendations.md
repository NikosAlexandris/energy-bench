# Energy-Bench Consolidation & Harmonization Recommendations

**Date**: 2026-05-16  
**Status**: Draft for Review

## Executive Summary

This document provides a comprehensive analysis of the Energy-Bench codebase, identifying duplication, terminology inconsistencies, and opportunities for consolidation. The goal is to make the project simpler to understand and use.

---

## 1. Terminology Standardization

### Current Issues

The codebase uses multiple terms for the same concepts, creating confusion:

| Concept | Current Terms Used | Recommended Standard |
|---------|-------------------|---------------------|
| ENTSO-E hourly data | `high_frequency`, `indicator`, `hourly`, `entsoe` | **`indicator`** |
| SFOE daily data | `low_frequency`, `target`, `daily`, `sfoe` | **`target`** |
| Benchmarked output | `benchmarked`, `adjusted`, `output` | **`benchmarked`** |
| Original ENTSO-E | `original`, `unadjusted` | **`original`** |
| Scaled output | `scaled`, `scaled_per_day` | **`scaled`** |

### Recommended Terminology

**Primary terms** (use consistently across all code):
- **`indicator`**: High-frequency time series data to be adjusted (e.g., ENTSO-E hourly, Swissgrid 15-min, or any other source)
- **`target`**: Low-frequency reference values (e.g., SFOE daily, or any other authoritative source)
- **`benchmarked`**: Output after temporal disaggregation
- **`original`**: Unadjusted indicator values
- **`scaled`**: Output after simple scaling operations

**Important**: These terms are **source-agnostic**. While the current implementation uses ENTSO-E and SFOE data, the terminology and architecture should support any high-frequency indicator and low-frequency target sources.

**Naming patterns**:
- Variables: `indicator_series`, `target_series`, `benchmarked_values`
- Parameters: `indicator_csv`, `target_csv`, `indicator_column`
- Files: `indicator_hourly.csv`, `target_daily.csv`
- Columns: `nuclear_indicator_gwh`, `nuclear_target_gwh`, `nuclear_benchmarked_gwh`

**Source metadata** (preserve in output):
- `indicator_source`: "ENTSO-E", "Swissgrid", or custom source name
- `target_source`: "SFOE" or custom source name
- This allows tracking data provenance without hardcoding source names in core logic

---

## 2. Source-Agnostic Design Principles

### Critical Design Goal

**The tool must remain generic and extensible**, supporting any high-frequency and low-frequency time series sources, not just ENTSO-E and SFOE.

### Current Issues

1. **Hardcoded source names in configuration**:
   - `entsoe_types` and `sfoe_types` keys hardcode specific sources
   - Makes it difficult to use alternative data sources

2. **Source-specific terminology in code**:
   - Comments and variable names reference specific sources
   - Creates mental model tied to specific datasets

3. **Limited flexibility for new sources**:
   - No clear pattern for adding new indicator sources (e.g., Swissgrid, custom APIs)
   - No mechanism to specify source metadata

### Recommended Approach

#### 2.1 Generic Configuration Schema

```python
VARIABLES = {
    "nuclear": {
        "label": "Nuclear",
        "kind": "atomic",
        
        # Generic column specifications (source-agnostic)
        "indicator_types": ["Nuclear"],      # Column names in indicator CSV
        "target_types": ["Kernkraft"],       # Column names in target CSV
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Allow runtime override of sources
        "indicator_source_field": "indicator_source",
        "target_source_field": "target_source",
    }
}
```

#### 2.2 Runtime Source Specification

```python
# Allow users to specify sources at runtime
def benchmark(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_source: str = "ENTSO-E",    # NEW: Allow custom source name
    target_source: str = "SFOE",          # NEW: Allow custom source name
    indicator_time_column: str = "DateTime",
    target_time_column: str = "Date",
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
) -> DataFrame:
    """
    Benchmark indicator series using temporal disaggregation.
    
    Args:
        indicator_source: Name of indicator data source (e.g., "ENTSO-E", "Swissgrid", "CustomAPI")
        target_source: Name of target data source (e.g., "SFOE", "CustomReference")
    """
```

#### 2.3 Output Metadata

All outputs should include source provenance:

```python
output_dataframe["indicator_source"] = indicator_source  # User-specified or default
output_dataframe["target_source"] = target_source        # User-specified or default
output_dataframe["indicator_columns"] = ", ".join(cfg["indicator_types"])
output_dataframe["target_columns"] = ", ".join(cfg["target_types"])
```

#### 2.4 Documentation Pattern

```python
def benchmark(...):
    """
    Benchmark high-frequency indicator series against low-frequency targets.
    
    This function is source-agnostic and works with any time series data:
    - Indicator: Any high-frequency series (hourly, 15-min, etc.)
    - Target: Any low-frequency reference (daily, weekly, etc.)
    
    Examples:
        # ENTSO-E hourly vs SFOE daily (default)
        benchmark("nuclear", entsoe_hourly.csv, sfoe_daily.csv, ...)
        
        # Swissgrid 15-min vs SFOE daily
        benchmark("nuclear", swissgrid_15min.csv, sfoe_daily.csv,
                  indicator_source="Swissgrid", ...)
        
        # Custom API vs custom reference
        benchmark("nuclear", custom_hourly.csv, custom_daily.csv,
                  indicator_source="CustomAPI", 
                  target_source="CustomReference", ...)
    """
```

### Benefits of Source-Agnostic Design

1. **Extensibility**: Easy to add new data sources without code changes
2. **Flexibility**: Users can benchmark any time series combination
3. **Provenance**: Clear tracking of data sources in outputs
4. **Future-proof**: Accommodates new data sources as they become available
5. **Reusability**: Tool can be used for non-energy applications

### Implementation Checklist

- [ ] Remove hardcoded source names from configuration keys
- [ ] Add `indicator_source` and `target_source` parameters to core functions
- [ ] Update output DataFrames to include source metadata
- [ ] Revise documentation to emphasize source-agnostic design
- [ ] Add examples using alternative data sources
- [ ] Update AGENTS.md with source-agnostic terminology
- [ ] Create guide for adding new data sources

---

## 3. Function Duplication

### 2.1 Helper Functions - CRITICAL DUPLICATION

**Location**: `src/energybench/helpers.py`

```python
# DUPLICATE FUNCTIONS - CONSOLIDATE TO ONE
def sum_columns(df, columns, label, factor=1.0) -> pd.Series
def safe_sum_series(df, value_columns, series_name) -> pd.Series
```

**Issue**: Both functions do the same thing - sum columns with missing column warnings.

**Recommendation**: 
```python
# KEEP ONLY THIS VERSION (more descriptive name)
def sum_columns(
    df: pd.DataFrame,
    columns: list[str],
    output_name: str,
    factor: float = 1.0,
    strict: bool = False,
) -> pd.Series:
    """
    Sum specified columns, handling missing columns gracefully.
    
    Args:
        df: Input DataFrame
        columns: Column names to sum
        output_name: Name for output Series
        factor: Multiplicative factor (e.g., for unit conversion)
        strict: If True, raise error when columns missing; if False, warn and continue
    
    Returns:
        Series with summed values
    """
```

**Action**: 
1. Merge functionality into single `sum_columns` function
2. Add `strict` parameter for error vs warning behavior
3. Update all 21 call sites to use unified function
4. Remove `safe_sum_series`

### 2.2 Comparison Modules - STRUCTURAL DUPLICATION

**Duplicate modules**:
- `src/energybench/compare/series.py` (library functions)
- `src/energybench/commands/compare/series.py` (CLI command)

**Issue**: Confusing structure - similar names, different purposes.

**Recommendation**:
```
src/energybench/
├── compare/              # Library functions (keep)
│   ├── metrics.py       # Rename from series.py
│   ├── shape.py
│   └── types_.py
└── commands/
    └── compare/         # CLI commands (keep)
        ├── app.py
        ├── series.py    # CLI command
        └── types.py
```

**Action**:
1. Rename `compare/series.py` → `compare/metrics.py` (clearer purpose)
2. Update imports across codebase
3. Add docstring clarifying library vs CLI distinction

---

## 3. Parameter Naming Harmonization

### Current Inconsistencies

Different functions use different parameter names for the same concepts:

| Function | Indicator Param | Target Param | Time Column |
|----------|----------------|--------------|-------------|
| `benchmark()` | `high_frequency_csv` | `low_frequency_csv` | `high_frequency_datetime_column` |
| `read_csv()` | `source` | - | `time_column` |
| `scale_series()` | `high_frequency_series` | `low_frequency_series` | - |
| `prepare_dataframe()` | `high_frequency_indicator` | `low_frequency_target` | - |

### Recommended Standard Signatures

```python
# Core benchmarking function
def benchmark(
    variable: str,
    indicator_csv: Path,              # was: high_frequency_csv
    target_csv: Path,                 # was: low_frequency_csv
    start: Timestamp,
    end: Timestamp,
    indicator_time_column: str = "DateTime",  # was: high_frequency_datetime_column
    target_time_column: str = "Date",         # was: low_frequency_datetime_column
    output_dir: Path = Path("output"),
    method: str = "chow-lin",
    conversion: str = "sum",
) -> DataFrame:
    """Benchmark indicator series using temporal disaggregation."""
```

```python
# Scaling functions
def scale_series(
    indicator_series: pd.Series,      # was: high_frequency_series
    target_series: pd.Series,         # was: low_frequency_series
    warn_threshold: float = 10.0,
    min_daily_sum: float = 0.01,
) -> pd.Series:
    """Scale indicator series to match target values."""
```

```python
# Data preparation
def prepare_dataframe(
    target_series: pd.Series,         # was: low_frequency_target
    indicator_series: pd.Series,      # was: high_frequency_indicator
) -> pd.DataFrame:
    """Convert to tempdisagg format."""
```

---

## 4. Configuration Harmonization

### Current Issues in `variables.py`

**Inconsistent key names**:
```python
VARIABLES = {
    "nuclear": {
        "entsoe_types": [...],        # Hardcoded source: should be indicator_types
        "sfoe_types": [...],          # Hardcoded source: should be target_types
        "benchmarked_values": [...],  # Inconsistent: should be benchmarked_columns
        "scaled_values": [...],       # Inconsistent: should be scaled_columns
    }
}
```

**Recommendation** (Source-Agnostic Configuration):
```python
VARIABLES = {
    "nuclear": {
        "label": "Nuclear",
        "kind": "atomic",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Nuclear"],           # Default: ENTSO-E columns
        "target_types": ["Kernkraft"],           # Default: SFOE columns
        
        # Source metadata (for tracking provenance)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names (generated by tool)
        "benchmarked_column": "nuclear_benchmarked_gwh",
        "scaled_column": "nuclear_scaled_gwh",
        "original_column": "nuclear_original_gwh",
        
        # File naming
        "output_filename_base": "nuclear_hourly",
    }
}
```

**Benefits**:
- Clear distinction between input (source data) and output (generated) columns
- Consistent `_types` suffix for source column lists
- Consistent `_column` suffix for single output column names
- Removes redundant `_values` arrays
- **Source-agnostic**: Column names don't hardcode data sources
- **Provenance tracking**: Metadata fields track actual sources used

---

## 5. Module Organization

### Current Structure Issues

```
src/energybench/
├── compare/              # Library functions
├── commands/compare/     # CLI commands (confusing overlap)
├── io/                   # Good: centralized I/O
├── models/               # Good: core algorithms
├── plots/                # Library functions
├── commands/plot/        # CLI commands (confusing overlap)
├── validate/             # Library functions
├── commands/validate/    # CLI commands (confusing overlap)
```

### Recommended Structure

```
src/energybench/
├── core/                 # Core library functions (NEW)
│   ├── metrics.py       # Comparison metrics (from compare/series.py)
│   ├── shape.py         # Shape analysis (from compare/shape.py)
│   ├── validation.py    # Validation logic (from validate/)
│   └── visualization.py # Plot functions (from plots/)
├── models/              # Keep: algorithms
│   ├── disaggregation.py
│   ├── scaling.py
│   └── kalman.py
├── io/                  # Keep: I/O operations
│   ├── input.py
│   ├── output.py
│   └── fetch.py
├── commands/            # Keep: CLI only
│   ├── benchmark/
│   ├── compare.py
│   ├── plot.py
│   ├── scale.py
│   └── validate.py
├── cli.py               # Keep: main entry
├── variables.py         # Keep: configuration
└── helpers.py           # Keep: utilities
```

**Benefits**:
- Clear separation: `core/` = library, `commands/` = CLI
- No more duplicate module names
- Easier to import library functions
- Clearer project structure

---

## 6. Output Management Consolidation

### Current State

✅ **Good**: Centralized output functions in `io/output.py`
- `save_dataframe()`
- `save_figure()`
- `save_text()`
- `build_filename()`

### Remaining Issues

Some commands still use direct `df.to_csv()` or `plt.savefig()` instead of centralized functions.

**Action**: Audit all commands and ensure they use `io/output.py` functions.

---

## 7. Implementation Priority

### Phase 1: Critical (High Impact, Low Risk)

1. **Merge duplicate helper functions** (`sum_columns` / `safe_sum_series`)
   - Impact: Reduces confusion, 21 call sites
   - Risk: Low (simple refactor)
   - Effort: 2 hours

2. **Standardize terminology in docstrings**
   - Impact: Immediate clarity improvement
   - Risk: None (documentation only)
   - Effort: 4 hours

3. **Rename `compare/series.py` → `compare/metrics.py`**
   - Impact: Reduces confusion with `commands/compare/series.py`
   - Risk: Low (update imports)
   - Effort: 1 hour

### Phase 2: Important (High Impact, Medium Risk)

4. **Harmonize parameter names** across core functions
   - Impact: Consistent API
   - Risk: Medium (breaks existing scripts)
   - Effort: 8 hours
   - Note: Provide deprecation warnings

5. **Refactor `variables.py` configuration**
   - Impact: Clearer configuration structure
   - Risk: Medium (affects all energy types)
   - Effort: 6 hours

### Phase 3: Structural (High Impact, High Risk)

6. **Reorganize module structure** (`core/` separation)
   - Impact: Much clearer architecture
   - Risk: High (major refactor)
   - Effort: 16 hours
   - Note: Do in separate branch with full testing

---

## 8. Backward Compatibility Strategy

### Deprecation Pattern

```python
# Example: helpers.py
def sum_columns(df, columns, output_name, factor=1.0, strict=False):
    """Unified column summing function."""
    # Implementation
    pass

def safe_sum_series(df, value_columns, series_name):
    """DEPRECATED: Use sum_columns() instead."""
    import warnings
    warnings.warn(
        "safe_sum_series() is deprecated, use sum_columns() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return sum_columns(df, value_columns, series_name)
```

### Version Strategy

- **v1.1.0**: Phase 1 changes (safe, backward compatible)
- **v1.2.0**: Phase 2 changes (deprecation warnings)
- **v2.0.0**: Phase 3 changes (breaking changes, remove deprecated)

---

## 9. Testing Requirements

### Before Refactoring

1. Create comprehensive test suite covering:
   - All energy types (nuclear, water, river, storage, solar, wind, thermal)
   - All commands (benchmark, scale, compare, validate, plot)
   - Edge cases (missing data, extreme values, date ranges)

2. Establish baseline outputs:
   - Run full pipeline on test data
   - Save outputs as reference
   - Compare after refactoring

### After Each Phase

1. Run full test suite
2. Compare outputs with baseline (should be identical)
3. Check for deprecation warnings
4. Update documentation

---

## 10. Documentation Updates Needed

### Code Documentation

- [ ] Update all docstrings with standardized terminology
- [ ] Add type hints to all public functions
- [ ] Document parameter naming conventions in AGENTS.md
- [ ] Create API reference documentation

### User Documentation

- [ ] Update README.md with new terminology
- [ ] Create migration guide for v2.0.0
- [ ] Add examples using new API
- [ ] Update CLI help text

### Developer Documentation

- [ ] Update AGENTS.md with new structure
- [ ] Document module organization rationale
- [ ] Add contribution guidelines
- [ ] Create architecture diagram

---

## 11. Quick Wins (Immediate Actions)

These can be done immediately without breaking changes:

1. **Add terminology glossary to README.md**
   ```markdown
   ## Terminology
   
   - **Indicator**: High-frequency time series (e.g., ENTSO-E hourly, Swissgrid 15-min)
   - **Target**: Low-frequency reference values (e.g., SFOE daily)
   - **Benchmarked**: Output after temporal disaggregation
   - **Original**: Unadjusted indicator values
   - **Scaled**: Output after scaling operations
   
   Note: The tool is designed to be source-agnostic. While examples use ENTSO-E 
   and SFOE data, any high-frequency indicator and low-frequency target sources 
   can be used.
   ```

2. **Add type hints to core functions**
   - Improves IDE support
   - Catches errors early
   - Self-documenting

3. **Consolidate output directory structure**
   ```
   output/
   ├── nuclear/
   │   ├── nuclear_hourly_benchmarked_2025.csv
   │   ├── nuclear_hourly_scaled_2025.csv
   │   └── plots/
   ├── river/
   └── ...
   ```

4. **Create `CHANGELOG.md`**
   - Track all changes
   - Document breaking changes
   - Help users migrate

---

## 12. Summary of Key Recommendations

### Terminology
✅ Standardize on: `indicator`, `target`, `benchmarked`, `original`, `scaled`
✅ **Source-agnostic**: Terms work for any data source, not just ENTSO-E/SFOE

### Functions
✅ Merge `sum_columns` and `safe_sum_series` into single function
✅ Rename `compare/series.py` → `compare/metrics.py`

### Parameters
✅ Use consistent naming: `indicator_csv`, `target_csv`, `indicator_series`, `target_series`
✅ **Add source parameters**: `indicator_source`, `target_source` for provenance tracking

### Configuration
✅ Refactor `variables.py` with clear input/output distinction
✅ **Remove hardcoded sources**: Replace `entsoe_types`/`sfoe_types` with generic `indicator_types`/`target_types`
✅ **Add metadata fields**: `default_indicator_source`, `default_target_source`

### Structure
✅ Separate library (`core/`) from CLI (`commands/`)

### Design Principles
✅ **Generic & Extensible**: Support any high-frequency/low-frequency time series sources
✅ **Provenance Tracking**: Always record data sources in outputs
✅ **Future-Proof**: Easy to add new data sources without code changes

### Priority
1. Phase 1: Terminology + helper merge + source-agnostic terminology (safe, quick wins)
2. Phase 2: Parameter harmonization + source parameters (with deprecation)
3. Phase 3: Structural refactor + full source-agnostic implementation (major version bump)

---

## Appendix A: Affected Files by Phase

### Phase 1 (21 files)
- `helpers.py` (merge functions)
- All files importing `sum_columns` or `safe_sum_series` (21 call sites)
- `compare/series.py` → `compare/metrics.py` (rename)
- Documentation files (terminology updates)

### Phase 2 (35+ files)
- `benchmark.py` (parameter names)
- `variables.py` (configuration keys)
- All `commands/benchmark/*.py` (7 files)
- All `commands/scale/*.py` (2 files)
- All `models/*.py` (3 files)
- All files calling these functions

### Phase 3 (55+ files)
- All files in `compare/`, `plots/`, `validate/` (move to `core/`)
- All files in `commands/` (update imports)
- All test files (update imports)

---

## Appendix B: Migration Checklist

- [ ] Create feature branch `refactor/consolidation`
- [ ] Phase 1: Merge helper functions
- [ ] Phase 1: Rename compare/series.py
- [ ] Phase 1: Update terminology in docstrings
- [ ] Phase 1: Add glossary to README
- [ ] Phase 1: Run tests, verify outputs
- [ ] Phase 1: Merge to main, tag v1.1.0
- [ ] Phase 2: Harmonize parameter names
- [ ] Phase 2: Refactor variables.py
- [ ] Phase 2: Add deprecation warnings
- [ ] Phase 2: Update documentation
- [ ] Phase 2: Run tests, verify outputs
- [ ] Phase 2: Merge to main, tag v1.2.0
- [ ] Phase 3: Create core/ module
- [ ] Phase 3: Move library functions
- [ ] Phase 3: Update all imports
- [ ] Phase 3: Remove deprecated functions
- [ ] Phase 3: Full test suite
- [ ] Phase 3: Update all documentation
- [ ] Phase 3: Merge to main, tag v2.0.0

---

**End of Document**
