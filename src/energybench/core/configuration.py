from enum import Enum


VARIABLES = {
    "nuclear": {
        "label": "Nuclear",
        "kind": "atomic",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Nuclear"],
        "target_types": ["Kernkraft"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "nuclear_benchmarked_gwh",
        "scaled_column": "nuclear_scaled_gwh",
        "original_column": "nuclear_gwh",
        
        # Output filename bases
        "benchmarked_filename": "nuclear_hourly_benchmarked",
        "scaled_filename": "nuclear_hourly_scaled",
    },
    "water": {
        "label": "Water",
        "kind": "aggregate",
        
        # Input column names (source-agnostic)
        "indicator_types": [
            "Hydro Run-of-river and poundage",
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "target_types": ["Flusskraft", "Speicherkraft"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "water_benchmarked_gwh",
        "scaled_column": "water_scaled_gwh",
        "original_column": "water_gwh",
        
        # Output filename bases
        "benchmarked_filename": "water_hourly_benchmarked",
        "scaled_filename": "water_hourly_scaled",
    },
    "storage": {
        "label": "Storage",
        "kind": "atomic",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Hydro Water Reservoir", "Hydro Pumped Storage"],
        "target_types": ["Speicherkraft"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "storage_benchmarked_gwh",
        "scaled_column": "storage_scaled_gwh",
        "original_column": "storage_gwh",
        
        # Output filename bases
        "benchmarked_filename": "storage_hourly_benchmarked",
        "scaled_filename": "storage_hourly_scaled",
    },
    "river": {
        "label": "River",
        "kind": "atomic",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Hydro Run-of-river and poundage"],
        "target_types": ["Flusskraft"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "river_benchmarked_gwh",
        "scaled_column": "river_scaled_gwh",
        "original_column": "river_gwh",
        
        # Output filename bases
        "benchmarked_filename": "river_hourly_benchmarked",
        "scaled_filename": "river_hourly_scaled",
    },
    "solar": {
        "label": "Solar",
        "kind": "atomic",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Solar"],
        "target_types": ["Photovoltaik"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "solar_benchmarked_gwh",
        "scaled_column": "solar_scaled_gwh",
        "original_column": "solar_gwh",
        
        # Output filename bases
        "benchmarked_filename": "solar_hourly_benchmarked",
        "scaled_filename": "solar_hourly_scaled",
    },
    "wind": {
        "label": "Wind",
        "kind": "aggregate",
        
        # Input column names (source-agnostic)
        "indicator_types": ["Wind Onshore", "Wind Offshore"],
        "target_types": ["Wind"],
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "wind_benchmarked_gwh",
        "scaled_column": "wind_scaled_gwh",
        "original_column": "wind_gwh",
        
        # Output filename bases
        "benchmarked_filename": "wind_hourly_benchmarked",
        "scaled_filename": "wind_hourly_scaled",
    },
    "thermal": {
        "label": "Thermal",
        "kind": "aggregate",
        
        # Input column names (source-agnostic)
        "indicator_types": [
            "Fossil Gas",
            "Fossil Hard coal",
            "Fossil Brown coal/Lignite",
            "Oil",
            "Other",
            "Waste",
        ],
        "target_types": ["Thermische"],  # Erzeugung
        
        # Source metadata (for provenance tracking)
        "default_indicator_source": "ENTSO-E",
        "default_target_source": "SFOE",
        
        # Output column names
        "benchmarked_column": "thermal_benchmarked_gwh",
        "scaled_column": "thermal_scaled_gwh",
        "original_column": "thermal_gwh",
        
        # Output filename bases
        "benchmarked_filename": "thermal_hourly_benchmarked",
        "scaled_filename": "thermal_hourly_scaled",
    },
}


class Variable(str, Enum):
    nuclear = "nuclear"
    water = "water"
    storage = "storage"
    river = "river"
    solar = "solar"
    wind = "wind"
    thermal = "thermal"


def get_variable_config(
    variable: Variable,
    indicator_columns: list[str] | None = None,
    target_columns: list[str] | None = None,
    strict: bool = True,
) -> dict:
    """
    Get configuration for a specific energy variable.
    
    Args:
        variable: Energy type (e.g., "nuclear", "river", "solar")
        indicator_columns: Available columns in indicator data (for validation)
        target_columns: Available columns in target data (for validation)
        strict: If True, raise error when required columns are missing
        
    Returns:
        Configuration dictionary with all settings for the variable
    """
    key = variable.lower()
    if key not in VARIABLES:
        raise ValueError(
            f"Unknown variable '{variable}'. Available: {', '.join(sorted(VARIABLES))}"
        )

    cfg = VARIABLES[key].copy()
    cfg["key"] = key

    # Ensure backward compatibility: create aliases for old code
    cfg["target_type"] = cfg["target_types"]
    cfg["indicator_type"] = cfg["indicator_types"]
    cfg["output_column"] = cfg["benchmarked_column"]
    cfg["scaled_output_column"] = cfg["scaled_column"]
    cfg["output_filename"] = cfg["benchmarked_filename"]
    cfg["scaled_output_filename"] = cfg["scaled_filename"]

    # Validate which columns are present/missing
    if target_columns is not None:
        cfg["target_types_present"] = [c for c in cfg["target_types"] if c in target_columns]
        cfg["target_types_missing"] = [c for c in cfg["target_types"] if c not in target_columns]
    else:
        cfg["target_types_present"] = cfg["target_types"]
        cfg["target_types_missing"] = []

    if indicator_columns is not None:
        cfg["indicator_types_present"] = [c for c in cfg["indicator_types"] if c in indicator_columns]
        cfg["indicator_types_missing"] = [c for c in cfg["indicator_types"] if c not in indicator_columns]
    else:
        cfg["indicator_types_present"] = cfg["indicator_types"]
        cfg["indicator_types_missing"] = []

    if strict:
        if not cfg["target_types_present"]:
            raise ValueError(
                f"No target columns found for '{key}'. Expected one of: {cfg['target_types']}"
            )
        if not cfg["indicator_types_present"]:
            raise ValueError(
                f"No indicator columns found for '{key}'. Expected one of: {cfg['indicator_types']}"
            )

    return cfg


VARIABLE_ORDER = ["nuclear", "water", "storage", "river", "solar", "wind", "thermal"]
