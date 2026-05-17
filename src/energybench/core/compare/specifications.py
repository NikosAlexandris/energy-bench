COMPARISON_SPECS = [
    {
        "key": "nuclear",
        "label_daily": "Test Nuclear",
        "label_shape": "Nuclear intra-day shape",
        "hf_columns": ["Nuclear"],
        "lf_columns": ["Kernkraft"],
    },
    {
        "key": "hydro_power",
        "label_daily": "Compare series for Hydro Power",
        "label_shape": "Test Hydro Power intra-day shape",
        "hf_columns": [
            "Hydro Run-of-river and poundage",
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "lf_columns": ["Flusskraft", "Speicherkraft"],
    },
    {
        "key": "hydro_storage",
        "label_daily": "Compare series for Hydro Storage",
        "label_shape": "Test Hydro Storage intra-day shape",
        "hf_columns": [
            "Hydro Water Reservoir",
            "Hydro Pumped Storage",
        ],
        "lf_columns": ["Speicherkraft"],
    },
    {
        "key": "hydro_river",
        "label_daily": "Compare series for Hydro River",
        "label_shape": "Test Hydro River intra-day shape",
        "hf_columns": ["Hydro Run-of-river and poundage"],
        "lf_columns": ["Flusskraft"],
    },
    {
        "key": "solar",
        "label_daily": "Test Solar",
        "label_shape": "Solar intra-day shape",
        "hf_columns": ["Solar"],
        "lf_columns": ["Photovoltaik"],
    },
    {
        "key": "wind",
        "label_daily": "Test Wind",
        "label_shape": "Wind intra-day shape",
        "hf_columns": ["Wind Onshore"],
        "lf_columns": ["Wind"],
    },
]
