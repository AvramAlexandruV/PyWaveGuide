# optimizer.py
import materials
import waveguide_models as wm

def _create_component(comp_type, mat_name, wl):
    props = materials.get_properties(mat_name)
    if not props: return None
    
    if comp_type == "Straight Guide": return wm.StraightWaveguide(props, wl)
    elif comp_type == "S-Bend": return wm.SBendWaveguide(props, wl)
    elif comp_type == "Y-Branch": return wm.YBranch(props, wl)
    elif comp_type == "MMI (Splitter)": return wm.MMI(props, wl)
    elif comp_type == "Mirror": return wm.Mirror(props, wl)
    elif comp_type == "Grating (Bragg)": return wm.Grating(props, wl)
    return None

def run_simulation(params):
    comp = _create_component(params['type'], params['material'], float(params.get('wl', 1.55)))
    if not comp: return {"Error": "Unknown Component"}
    
    if params['type'] == "Straight Guide":
        return comp.design(float(params['len_um']), float(params.get('width_um', 2.0)))
    elif params['type'] == "S-Bend":
        return comp.design(float(params['offset_um']), float(params['len_um']))
    elif params['type'] == "Y-Branch":
        return comp.design(float(params['angle_deg']), float(params['len_um']))
    elif params['type'] == "MMI (Splitter)":
        return comp.design(float(params['width_um']), int(params['ports']))
    elif params['type'] == "Mirror":
        return comp.design(float(params['reflectivity']))
    elif params['type'] == "Grating (Bragg)":
        return comp.design(float(params['target_wl']))
    
    return {}

def generate_comparative_datasheet(params):
    mat_names = materials.get_material_names()
    start_wl = 0.38
    end_wl = 0.78
    step = 0.02
    spectral_rows = []
    
    curr_wl = start_wl
    while curr_wl <= end_wl + 0.001:
        row = {"Wavelength (um)": f"{curr_wl:.2f}"}
        for mat in mat_names:
            comp = _create_component(params['type'], mat, curr_wl)
            if comp:
                val = comp.analyze_spectrum(params, curr_wl)
                row[mat] = val
            else:
                row[mat] = "N/A"
        spectral_rows.append(row)
        curr_wl += step
        
    return mat_names, spectral_rows