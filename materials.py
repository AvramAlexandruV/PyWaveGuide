# materials.py

# Optical materials database
# Properties:
# n: Refractive index at 1550nm
# alpha: Estimated attenuation (dB/cm)
# min_bend_radius: Minimum bend radius (um) before significant loss
# cost_base: Fixed startup cost ($)
# cost_factor: Variable cost per unit ($)
# min_wl / max_wl: Transparency range (um)

MATERIALS_DB = {
    "SiO2 (Silica/PLC)": {
        "n": 1.457,
        "alpha": 0.05,
        "min_bend_radius": 5000, 
        "cost_base": 10.0,
        "cost_factor": 1.5,
        "min_wl": 0.2, "max_wl": 2.5,
        "description": "Low loss, cheap, but requires large footprint."
    },
    "Si (Silicon-on-Insulator)": {
        "n": 3.47,
        "alpha": 1.5,
        "min_bend_radius": 5, 
        "cost_base": 50.0,
        "cost_factor": 5.0,
        "min_wl": 1.1, "max_wl": 4.0, # Opaque in visible light (< 1.1 um)
        "description": "Extreme miniaturization, moderate cost."
    },
    "Si3N4 (Silicon Nitride)": {
        "n": 1.99,
        "alpha": 0.1,
        "min_bend_radius": 50,
        "cost_base": 40.0,
        "cost_factor": 4.0,
        "min_wl": 0.4, "max_wl": 2.0,
        "description": "Good for high power and broad spectrum."
    },
    "InP (Indium Phosphide)": {
        "n": 3.17,
        "alpha": 2.0,
        "min_bend_radius": 100,
        "cost_base": 100.0,
        "cost_factor": 20.0,
        "min_wl": 0.92, "max_wl": 3.0,
        "description": "Expensive, essential for active components (lasers)."
    },
    "LiNbO3 (Lithium Niobate)": {
        "n": 2.21,
        "alpha": 0.2,
        "min_bend_radius": 1000,
        "cost_base": 80.0,
        "cost_factor": 15.0,
        "min_wl": 0.35, "max_wl": 4.0,
        "description": "Excellent for modulators."
    },
    "Polymer (PMMA/Su8)": {
        "n": 1.49,
        "alpha": 0.5,
        "min_bend_radius": 2000,
        "cost_base": 5.0,
        "cost_factor": 1.0,
        "min_wl": 0.3, "max_wl": 1.6,
        "description": "Cheapest, rapid prototyping."
    }
}

def get_material_names():
    return list(MATERIALS_DB.keys())

def get_properties(name):
    return MATERIALS_DB.get(name, None)