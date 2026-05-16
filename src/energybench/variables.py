from enum import Enum


VARIABLES = {
    "nuclear": {
        "label": "Nuclear",
        "benchmarked_values": ["nuclear_benchmarked_gwh"],
        "scaled_values": ["nuclear_scaled_gwh"],
        "scaled_per_day_values": ["nuclear_scaled_per_day_gwh"],
        "entsoe_types": ["Nuclear"],
        "sfoe_types": ["Kernkraft"],
        "kind": "atomic",
    },
    "water": {
        "label": "Water",
        "benchmarked_values": ["water_benchmarked_gwh"],
        "scaled_values": ["water_scaled_gwh"],
        "scaled_per_day_values": ["water_scaled_per_day_gwh"],
        "entsoe_types": [
            "Hydro Run-of-river and poundage",
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "sfoe_types": ["Flusskraft", "Speicherkraft"],
        "kind": "aggregate",
    },
    "storage": {
        "label": "Storage",
        "benchmarked_values": ["storage_benchmarked_gwh"],
        "scaled_values": ["storage_scaled_gwh"],
        "scaled_per_day_values": ["storage_scaled_per_day_gwh"],
        "entsoe_types": ["Hydro Water Reservoir", "Hydro Pumped Storage"],
        "sfoe_types": ["Speicherkraft"],
        "kind": "atomic",
    },
    "river": {
        "label": "River",
        "benchmarked_values": ["river_benchmarked_gwh"],
        "scaled_values": ["river_scaled_gwh"],
        "scaled_per_day_values": ["river_scaled_per_day_gwh"],
        "entsoe_types": ["Hydro Run-of-river and poundage"],
        "sfoe_types": ["Flusskraft"],
        "kind": "atomic",
    },
    "solar": {
        "label": "Solar",
        "benchmarked_values": ["solar_benchmarked_gwh"],
        "scaled_values": ["solar_scaled_gwh"],
        "scaled_per_day_values": ["solar_scaled_per_day_gwh"],
        "entsoe_types": ["Solar"],
        "sfoe_types": ["Photovoltaik"],
        "kind": "atomic",
    },
    "wind": {
        "label": "Wind",
        "benchmarked_values": ["wind_benchmarked_gwh"],
        "scaled_values": ["wind_scaled_gwh"],
        "scaled_per_day_values": ["wind_scaled_per_day_gwh"],
        "entsoe_types": ["Wind Onshore", "Wind Offshore"],
        "sfoe_types": ["Wind"],
        "kind": "aggregate",
    },
    "thermal": {
        "label": "Thermal",
        "benchmarked_values": ["thermal_benchmarked_gwh"],
        "scaled_values": ["thermal_scaled_gwh"],
        "scaled_per_day_values": ["thermal_scaled_per_day_gwh"],
        "entsoe_types": [
            "Fossil Gas",
            "Fossil Hard coal",
            "Fossil Brown coal/Lignite",
            "Oil",
            "Other",
            "Waste",
        ],
        "sfoe_types": ["Thermische Erzeugung"],
        "kind": "aggregate",
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
    high_frequency_types: list[str] | None = None,
    low_frequency_types: list[str] | None = None,
    strict: bool = True,
) -> dict:
    """ """
    key = variable.lower()
    if key not in VARIABLES:
        raise ValueError(
            f"Unknown variable '{variable}'. Available: {', '.join(sorted(VARIABLES))}"
        )

    cfg = VARIABLES[key].copy()
    cfg["key"] = key

    cfg["target_type"] = list(cfg.get("target_type", cfg["sfoe_types"]))
    cfg["indicator_type"] = list(cfg.get("indicator_type", cfg["entsoe_types"]))
    cfg["output_column"] = cfg.get(
        "output_column",
        cfg["benchmarked_values"][0],
    )
    cfg["scaled_output_column"] = cfg.get(
        "scaled_output_column",
        cfg["scaled_values"][0],
    )
    cfg["scaled_advanced_output_column"] = cfg.get(
        "scaled_advanced_output_column",
        cfg["scaled_per_day_values"][0],
    )
    cfg["original_column"] = cfg.get(
        "original_column",
        f"{key}_gwh",
    )
    cfg["output_filename"] = cfg.get(
        "output_filename",
        f"{key}_hourly_benchmarked",
    )
    cfg["scaled_output_filename"] = cfg.get(
        "scaled_output_filename",
        f"{key}_hourly_scaled",
    )
    cfg["scaled_advanced_output_filename"] = cfg.get(
        "scaled_advanced_output_filename",
        f"{key}_hourly_scaled_advanced",
    )

    if low_frequency_types is not None:
        cfg["target_types_present"] = [c for c in cfg["target_type"] if c in low_frequency_types]
        cfg["target_types_missing"] = [
            c for c in cfg["target_type"] if c not in low_frequency_types
        ]
    else:
        cfg["target_types_present"] = cfg["target_type"]
        cfg["target_types_missing"] = []

    if high_frequency_types is not None:
        cfg["indicator_types_present"] = [
            c for c in cfg["indicator_type"] if c in high_frequency_types
        ]
        cfg["indicator_types_missing"] = [
            c for c in cfg["indicator_type"] if c not in high_frequency_types
        ]
    else:
        cfg["indicator_types_present"] = cfg["indicator_type"]
        cfg["indicator_types_missing"] = []

    if strict:
        if not cfg["target_types_present"]:
            raise ValueError(
                f"No target columns found for '{key}'. Expected one of: {cfg['target_type']}"
            )
        if not cfg["indicator_types_present"]:
            raise ValueError(
                f"No indicator columns found for '{key}'. Expected one of: {cfg['indicator_type']}"
            )

    return cfg
