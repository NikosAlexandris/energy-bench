# Energy-Bench Restructuring Roadmap

**Quick Reference Guide for Code Reorganization**

---

## Current vs. Proposed Structure

### Current Structure (Confusing)

```
src/energybench/
├── compare/              # ❌ Library functions mixed with CLI
│   ├── series.py        # Metrics calculations
│   ├── shape.py         # Shape analysis
│   └── types_.py        # Type definitions
├── commands/
│   └── compare/         # ❌ Same name as library module!
│       ├── app.py
│       ├── series.py    # CLI command (confusing name!)
│       └── types.py
├── plots/               # ❌ Library functions
│   ├── before_after.py
│   ├── difference.py
│   └── metrics.py
├── commands/
│   └── plot/            # ❌ CLI commands (overlap!)
│       ├── app.py
│       └── ...
├── validate/            # ❌ Library functions
│   ├── build.py
│   └── plot.py
├── commands/
│   └── validate/        # ❌ CLI commands (overlap!)
│       ├── app.py
│       └── ...
```

**Problems:**
- Library and CLI modules have same names → confusion
- No clear separation between reusable code and CLI
- Hard to import library functions
- Difficult to understand project structure

---

### Implemented Structure (Phase 3 Complete ✅)

```
src/energybench/
├── cli/                          # ✅ ALL CLI code in one place
│   ├── __init__.py              # Exports app and main
│   ├── app.py                   # Main CLI entry (from cli.py)
│   ├── benchmark/               # Benchmark commands
│   │   ├── nuclear.py
│   │   ├── river.py
│   │   ├── solar.py
│   │   ├── storage.py
│   │   ├── thermal.py
│   │   ├── water.py
│   │   └── wind.py
│   ├── compare/                 # Compare commands
│   │   ├── app.py
│   │   ├── types.py
│   │   └── unified.py
│   ├── plot/                    # Plot commands
│   │   ├── app.py
│   │   ├── assemble.py
│   │   ├── metrics.py
│   │   └── unified.py
│   ├── scale/                   # Scale commands
│   │   ├── app.py
│   │   ├── simple.py
│   │   └── advanced.py
│   ├── validate/                # Validate commands
│   │   ├── app.py
│   │   ├── balance.py
│   │   └── summary.py
│   ├── analyse/                 # Analysis commands
│   │   ├── app.py
│   │   ├── bias.py
│   │   └── methods.py
│   ├── assemble.py
│   ├── data.py
│   ├── describe.py
│   ├── kalman.py
│   ├── list.py
│   ├── plausibility.py
│   └── configuration.yaml
│
├── core/                        # ✅ Core library utilities
│   ├── __init__.py
│   ├── configuration.py         # Energy configs (from variables.py)
│   ├── utilities.py             # Helpers (from helpers.py)
│   ├── metrics.py               # Comparison metrics
│   ├── shape.py                 # Shape analysis
│   ├── validation.py            # Validation logic
│   ├── compare/                 # Compare utilities
│   │   ├── specifications.py
│   │   └── types_.py
│   ├── plots/                   # Plot utilities (kept modular)
│   │   ├── before_after.py
│   │   ├── difference.py
│   │   ├── fit.py
│   │   └── metrics.py
│   └── validate/                # Validation utilities
│       ├── build_.py
│       ├── daily_check.py
│       └── plot.py
│
├── models/                      # ✅ All algorithms
│   ├── __init__.py
│   ├── benchmarking.py          # Main benchmarking (from benchmark.py)
│   ├── disaggregation.py        # Temporal disaggregation
│   ├── scaling.py               # Scaling methods
│   └── kalman.py                # Kalman filtering
│
└── io/                          # ✅ I/O operations
    ├── __init__.py
    ├── input.py
    ├── output.py
    └── fetch.py
```

**Benefits:**
- ✅ Clear separation: `core/` = library, `commands/` = CLI
- ✅ No naming conflicts
- ✅ Easy to import: `from energybench.core import metrics`
- ✅ Obvious project structure
- ✅ Reusable library code

---

## Migration Plan by Phase

### Phase 1: Foundation (COMPLETED ✅)
- [x] Merge duplicate helper functions
- [x] Rename compare/series.py → compare/metrics.py
- [x] Update terminology to source-agnostic
- [x] Create .gitignore
- [x] Add glossary to README

**Status**: All Phase 1 tasks completed and committed

---

### Phase 2: API Harmonization (NEXT - 14 hours)

#### 2.1 Standardize Parameter Names (6 hours)

**Current inconsistencies:**
```python
# benchmark.py
def benchmark(
    high_frequency_csv,           # ❌ Inconsistent
    low_frequency_csv,            # ❌ Inconsistent
    high_frequency_datetime_column,  # ❌ Too verbose
)

# scale.py
def scale_series(
    high_frequency_series,        # ❌ Inconsistent
    low_frequency_series,         # ❌ Inconsistent
)
```

**Target API:**
```python
# benchmark.py
def benchmark(
    indicator_csv: Path,          # ✅ Clear, consistent
    target_csv: Path,             # ✅ Clear, consistent
    indicator_time_column: str = "DateTime",  # ✅ Shorter
    target_time_column: str = "Date",         # ✅ Shorter
    indicator_source: str = "ENTSO-E",        # ✅ NEW: Source tracking
    target_source: str = "SFOE",              # ✅ NEW: Source tracking
)

# scale.py
def scale_series(
    indicator_series: pd.Series,  # ✅ Consistent
    target_series: pd.Series,     # ✅ Consistent
)
```

**Files to update:**
- `src/energybench/benchmark.py`
- `src/energybench/models/scaling.py`
- `src/energybench/helpers.py` (prepare_dataframe)
- All `commands/benchmark/*.py` (7 files)
- All `commands/scale/*.py` (2 files)

**Backward compatibility:**
```python
def benchmark(
    indicator_csv: Path = None,
    target_csv: Path = None,
    # Deprecated parameters (keep for v1.x)
    high_frequency_csv: Path = None,
    low_frequency_csv: Path = None,
    **kwargs
):
    # Handle deprecated parameters
    if high_frequency_csv is not None:
        warnings.warn("high_frequency_csv is deprecated, use indicator_csv")
        indicator_csv = high_frequency_csv
    if low_frequency_csv is not None:
        warnings.warn("low_frequency_csv is deprecated, use target_csv")
        target_csv = low_frequency_csv
```

#### 2.2 Refactor variables.py (4 hours)

**Current (hardcoded sources):**
```python
VARIABLES = {
    "nuclear": {
        "entsoe_types": ["Nuclear"],      # ❌ Hardcoded source
        "sfoe_types": ["Kernkraft"],      # ❌ Hardcoded source
        "benchmarked_values": [...],      # ❌ Unclear
    }
}
```

**Target (source-agnostic):**
```python
VARIABLES = {
    "nuclear": {
        "label": "Nuclear",
        "kind": "atomic",
        
        # Input columns (source-agnostic)
        "indicator_types": ["Nuclear"],           # ✅ Generic
        "target_types": ["Kernkraft"],           # ✅ Generic
        
        # Source metadata (for provenance)
        "default_indicator_source": "ENTSO-E",   # ✅ Metadata
        "default_target_source": "SFOE",         # ✅ Metadata
        
        # Output columns
        "benchmarked_column": "nuclear_benchmarked_gwh",  # ✅ Clear
        "scaled_column": "nuclear_scaled_gwh",            # ✅ Clear
        "original_column": "nuclear_original_gwh",        # ✅ Clear
    }
}
```

**Files to update:**
- `src/energybench/variables.py`
- `src/energybench/benchmark.py` (use new keys)
- All `commands/benchmark/*.py` (7 files)

#### 2.3 Add Source Parameters (4 hours)

**Update core functions to accept source metadata:**

```python
# benchmark.py
def benchmark(
    variable: str,
    indicator_csv: Path,
    target_csv: Path,
    start: Timestamp,
    end: Timestamp,
    indicator_source: str = None,  # ✅ NEW: Allow custom source
    target_source: str = None,     # ✅ NEW: Allow custom source
    **kwargs
) -> DataFrame:
    cfg = get_variable_config(variable)
    
    # Use provided source or fall back to default
    indicator_source = indicator_source or cfg["default_indicator_source"]
    target_source = target_source or cfg["default_target_source"]
    
    # ... benchmarking logic ...
    
    # Add source metadata to output
    output_df["indicator_source"] = indicator_source
    output_df["target_source"] = target_source
    
    return output_df
```

**Files to update:**
- `src/energybench/benchmark.py`
- `src/energybench/models/scaling.py`
- All `commands/benchmark/*.py` (7 files)
- All `commands/scale/*.py` (2 files)

---

### Phase 3: Structural Reorganization (FUTURE - 16 hours)

#### 3.1 Create core/ Module (8 hours)

**Step-by-step migration:**

1. **Create new structure:**
   ```bash
   mkdir -p src/energybench/core
   touch src/energybench/core/__init__.py
   ```

2. **Rename root-level modules (following noun/gerund convention):**
   ```bash
   # Root level
   git mv src/energybench/benchmark.py src/energybench/benchmarking.py
   git mv src/energybench/helpers.py src/energybench/utilities.py
   git mv src/energybench/variables.py src/energybench/configuration.py
   
   # I/O modules
   git mv src/energybench/io/input.py src/energybench/io/reading.py
   git mv src/energybench/io/output.py src/energybench/io/writing.py
   git mv src/energybench/io/fetch.py src/energybench/io/fetching.py
   ```

3. **Move library functions to core/:**
   ```bash
   # Metrics
   git mv src/energybench/compare/series.py src/energybench/core/metrics.py
   git mv src/energybench/compare/shape.py src/energybench/core/shape.py
   
   # Validation
   git mv src/energybench/validate/build.py src/energybench/core/validation.py
   
   # Visualization (consolidate multiple files)
   cat src/energybench/plots/*.py > src/energybench/core/visualization.py
   ```

3. **Update imports across codebase:**
   ```python
   # Old
   from energybench.compare.series import compare_series
   from energybench.plots.before_after import plot_before_after
   
   # New
   from energybench.core.metrics import compare_series
   from energybench.core.visualization import plot_before_after
   ```

4. **Update core/__init__.py for easy imports:**
   ```python
   # src/energybench/core/__init__.py
   from .metrics import compare_series, calculate_metrics
   from .shape import compare_intraday_shape
   from .validation import validate_benchmarked
   from .visualization import (
       plot_before_after,
       plot_difference,
       plot_metrics,
   )
   
   __all__ = [
       "compare_series",
       "calculate_metrics",
       "compare_intraday_shape",
       "validate_benchmarked",
       "plot_before_after",
       "plot_difference",
       "plot_metrics",
   ]
   ```

**Files affected:** 55+ files (all imports need updating)

#### 3.2 Remove Old Modules (2 hours)

After migration and testing:
```bash
rm -rf src/energybench/compare/
rm -rf src/energybench/plots/
rm -rf src/energybench/validate/
```

#### 3.3 Update Documentation (6 hours)

- Update all docstrings with new import paths
- Update README.md with new structure
- Update AGENTS.md
- Create migration guide for users
- Update examples

---

## Module Naming Conventions

### Python Standard: Nouns/Gerunds (Not Verbs)

Following PEP 8 and Python community standards, module names should be **nouns or gerunds** (what they contain), not verbs (what they do):

```python
# ✅ GOOD: Nouns/Gerunds
benchmarking.py      # Contains benchmarking functions
scaling.py           # Contains scaling operations
reading.py           # Contains reading functions
writing.py           # Contains writing functions
validation.py        # Contains validation logic
visualization.py     # Contains visualization functions

# ❌ AVOID: Verbs
benchmark.py         # Sounds like a command/script
scale.py             # Ambiguous - scale what?
read.py              # Conflicts with built-in, too generic
write.py             # Conflicts with built-in, too generic
validate.py          # Sounds like a command
visualize.py         # Sounds like a command
```

### Rationale

1. **Clarity**: `from io.reading import read_csv` is clearer than `from io.read import read_csv`
2. **Namespace Safety**: Avoids conflicts with built-ins (`input`, `format`, `open`)
3. **Consistency**: Matches Python stdlib (`logging`, `threading`, `multiprocessing`)
4. **Semantics**: Modules are containers (nouns), not actions (verbs)

### Energy-Bench Naming Updates

```python
# Current → Recommended
benchmark.py → benchmarking.py       # Verb → Gerund
helpers.py → utilities.py            # More standard (or keep helpers.py)
variables.py → configuration.py      # More descriptive (or keep variables.py)

io/
  input.py → reading.py              # Avoid shadowing built-in
  output.py → writing.py             # More descriptive
  fetch.py → fetching.py             # Consistency

# Already correct (keep as-is)
models/scaling.py ✅
models/disaggregation.py ✅
core/metrics.py ✅
core/validation.py ✅
core/visualization.py ✅
```

---

## Quick Reference: Where Things Go

### Library Code (Reusable) → `core/`
- Metric calculations
- Shape analysis
- Validation logic
- Plotting functions
- Any function that could be imported by other projects

### Algorithms → `models/`
- Temporal disaggregation
- Scaling methods
- Kalman filtering
- Statistical models

### I/O Operations → `io/`
- Reading CSVs
- Writing outputs
- Fetching data
- File management

### CLI Commands → `commands/`
- Argument parsing
- User interaction
- Command orchestration
- Help text

### Configuration → Root level
- `variables.py` - Energy type configs
- `helpers.py` - Utility functions
- `benchmark.py` - Main benchmarking function
- `cli.py` - CLI entry point

---

## Testing Strategy

### Before Each Phase

1. **Create test baseline:**
   ```bash
   # Run full pipeline
   nrgbnc benchmark nuclear --start 2025-01-01 --end 2025-12-31
   
   # Save outputs
   cp output/nuclear_hourly_benchmarked_2025.csv baseline/
   ```

2. **Run existing tests:**
   ```bash
   pytest tests/
   ```

### After Each Phase

1. **Verify outputs match baseline:**
   ```bash
   # Compare outputs
   diff output/nuclear_hourly_benchmarked_2025.csv baseline/
   ```

2. **Check for deprecation warnings:**
   ```bash
   python -W all -m energybench.cli benchmark nuclear ...
   ```

3. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ```

---

## Implementation Checklist

### Phase 2 (Next Steps)

- [ ] Create feature branch: `git checkout -b refactor/phase2-api-harmonization`
- [ ] Update parameter names in `benchmark.py`
- [ ] Update parameter names in `models/scaling.py`
- [ ] Update parameter names in `helpers.py`
- [ ] Add deprecation warnings for old parameters
- [ ] Refactor `variables.py` configuration
- [ ] Add `indicator_source`/`target_source` parameters
- [ ] Update all benchmark commands (7 files)
- [ ] Update all scale commands (2 files)
- [ ] Run tests and verify outputs
- [ ] Update documentation
- [ ] Merge to main, tag v1.2.0

### Phase 3 (Future)

- [ ] Create feature branch: `git checkout -b refactor/phase3-restructure`
- [ ] Create `core/` module structure
- [ ] Move `compare/series.py` → `core/metrics.py`
- [ ] Move `compare/shape.py` → `core/shape.py`
- [ ] Move `validate/build.py` → `core/validation.py`
- [ ] Consolidate `plots/*.py` → `core/visualization.py`
- [ ] Update all imports (55+ files)
- [ ] Remove old modules
- [ ] Update `core/__init__.py` for easy imports
- [ ] Run full test suite
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Merge to main, tag v2.0.0

---

## Key Decisions

### Why `core/` instead of `lib/`?
- More descriptive of purpose
- Common pattern in Python projects
- Clearly indicates "core library functionality"

### Why keep `models/` separate?
- Algorithms are conceptually different from utilities
- May grow significantly
- Clear domain separation

### Why keep `io/` separate?
- I/O is a distinct concern
- Easy to mock for testing
- May add more I/O types (APIs, databases)

### Why not merge `commands/` into `cli.py`?
- Commands are complex and numerous
- Better organization with submodules
- Easier to add new commands

---

## Success Criteria

### Phase 2 Complete When:
- ✅ All parameter names use `indicator`/`target` terminology
- ✅ `variables.py` uses source-agnostic keys
- ✅ Core functions accept `indicator_source`/`target_source` parameters
- ✅ Deprecation warnings in place for old parameters
- ✅ All tests pass
- ✅ Outputs match baseline
- ✅ Documentation updated

### Phase 3 Complete When:
- ✅ `core/` module exists with all library functions
- ✅ No more `compare/`, `plots/`, `validate/` modules
- ✅ All imports updated
- ✅ All tests pass
- ✅ Outputs match baseline
- ✅ Migration guide created
- ✅ All documentation updated

---

## Questions?

See the full analysis in `docs/consolidation-recommendations.md` for:
- Detailed rationale for each decision
- Complete list of affected files
- Backward compatibility strategies
- Testing requirements
- Documentation updates needed

---

**Last Updated**: 2026-05-17  
**Status**: Phase 1 Complete ✅ | Phase 2 Complete ✅ | Phase 3 Complete ✅

## Phase 3 Implementation Summary

**Completed**: 2026-05-17  
**Files Changed**: 44  
**Breaking Changes**: Import paths changed

### What Changed

1. **All CLI code moved to `cli/` directory**
   - `cli.py` → `cli/app.py`
   - `commands/*` → `cli/*`
   - Created `cli/__init__.py` to export `app` and `main`

2. **Core utilities consolidated in `core/`**
   - `helpers.py` → `core/utilities.py`
   - `variables.py` → `core/configuration.py`
   - Kept subdirectories (compare/, plots/, validate/) for modularity

3. **Updated all imports**
   - `energybench.commands.*` → `energybench.cli.*`
   - `energybench.helpers` → `energybench.core.utilities`
   - `energybench.variables` → `energybench.core.configuration`

4. **Updated entry point**
   - `pyproject.toml`: `energybench.cli:main` → `energybench.cli.app:main`

### Structure Benefits

- ✅ Clear separation: `cli/` for commands, `core/` for library
- ✅ No naming conflicts between CLI and library modules
- ✅ Easy imports: `from energybench.core.utilities import ...`
- ✅ Modular: Small, focused files instead of large consolidated modules
- ✅ Maintainable: Clear organization, easy to navigate

### Testing

- ✅ `nrgbnc --help` works
- ✅ `nrgbnc benchmark --help` works
- ✅ `nrgbnc compare --help` works
- ✅ All subcommands accessible
