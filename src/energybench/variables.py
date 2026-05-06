from enum import Enum


VARIABLES = {
    "water": {
        "label": "Water",
        "benchmark_value_columns": ["water_benchmarked_gwh"],
        "high_frequency_value_columns": [
            "Hydro Run-of-river and poundage",
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "low_frequency_columns": ["Flusskraft", "Speicherkraft"],
        "kind": "aggregate",
    },
    "nuclear": {
        "label": "Nuclear",
        "benchmark_value_columns": ["nuclear_benchmarked_gwh"],
        "high_frequency_value_columns": ["Nuclear"],
        "low_frequency_columns": ["Kernkraft"],
        "kind": "atomic",
    },
    "river": {
        "label": "River",
        "benchmark_value_columns": ["river_benchmarked_gwh"],
        "high_frequency_value_columns": ["Hydro Run-of-river and poundage"],
        "low_frequency_columns": ["Flusskraft"],
        "kind": "atomic",
    },
    "storage": {
        "label": "Storage",
        "benchmark_value_columns": ["storage_benchmarked_gwh"],
        "high_frequency_value_columns": ["Hydro Water Reservoir"],
        "low_frequency_columns": ["Speicherkraft"],
        "kind": "atomic",
    },
    "wind": {
        "label": "Wind",
        "benchmark_value_columns": ["wind_benchmarked_gwh"],
        "high_frequency_value_columns": ["Wind Onshore", "Wind Offshore"],
        "low_frequency_columns": ["Windkraft"],
        "kind": "aggregate",
    },
    "solar": {
        "label": "Solar",
        "benchmark_value_columns": ["solar_benchmarked_gwh"],
        "high_frequency_value_columns": ["Solar"],
        "low_frequency_columns": ["Solarenergie"],
        "kind": "atomic",
    },
    "thermal": {
        "label": "Thermal",
        "benchmark_value_columns": ["thermal_benchmarked_gwh"],
        "high_frequency_value_columns": [
            "Fossil Gas",
            "Fossil Hard coal",
            "Fossil Brown coal/Lignite",
            "Oil",
            "Other",
            "Waste",
        ],
        "low_frequency_columns": ["Thermische Erzeugung"],
        "kind": "aggregate",
    },
}


class Variable(str, Enum):
    water = "water"
    nuclear = "nuclear"
    river = "river"
    storage = "storage"
    wind = "wind"
    solar = "solar"
    thermal = "thermal"


def get_variable_config(
    variable: Variable
) -> dict:
    """
    """
    key = variable.lower()
    if key not in VARIABLES:
        raise ValueError(
            f"Unknown variable '{variable}'. Available: {', '.join(sorted(VARIABLES))}"
        )

    cfg = VARIABLES[key].copy()
    cfg["key"] = key
    cfg["target_columns"] = cfg.get("target_columns", cfg["low_frequency_columns"])
    cfg["indicator_columns"] = cfg.get("indicator_columns", cfg["high_frequency_value_columns"])
    cfg["output_column"] = cfg.get("output_column", cfg["benchmark_value_columns"][0])
    cfg["original_column"] = cfg.get("original_column", f"{key}_high_frequency_original_gwh")
    cfg["output_filename"] = cfg.get("output_filename", f"benchmarked_hourly_{key}.csv")

    return cfg
