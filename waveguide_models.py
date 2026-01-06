# waveguide_models.py
import math

class GenericComponent:
    def __init__(self, material_props, wavelength_um=1.55):
        self.props = material_props
        self.wl = float(wavelength_um)
        self.n_core = self.props["n"]
        # Cladding approximation (Air or SiO2)
        self.n_clad = 1.444 if self.n_core > 1.45 else 1.0
        self.n_eff = self.n_core * 0.95 
        
        try:
            self.NA = math.sqrt(self.n_core**2 - self.n_clad**2)
        except:
            self.NA = 0.1

    def is_transparent(self, wl_um):
        return self.props["min_wl"] <= wl_um <= self.props["max_wl"]

    def calculate_cost(self, dimension_metric):
        base = self.props["cost_base"]
        var = self.props["cost_factor"] * dimension_metric
        return round(base + var, 2)
    
    def get_V_number(self, width_um, wl_um):
        return (2 * math.pi * (width_um/2) / wl_um) * self.NA

    def get_cutoff_wl(self, width_um):
        return (2 * math.pi * (width_um/2) * self.NA) / 2.405

# --- 1. STRAIGHT WAVEGUIDE ---
class StraightWaveguide(GenericComponent):
    def design(self, length_um, width_um):
        if not self.is_transparent(self.wl):
            return {"Status": "OPAQUE", "Transmittance (%)": 0.0, "Cost ($)": 0}

        # Convert um to cm for loss calculation
        length_cm = length_um / 10000.0
        loss_db = self.props["alpha"] * length_cm
        transmittance = 10 ** (-loss_db / 10)
        
        V = self.get_V_number(width_um, self.wl)
        wl_cutoff = self.get_cutoff_wl(width_um)
        
        return {
            "Parameter": "Straight Guide",
            "Loss (dB)": round(loss_db, 4),
            "Transmittance (%)": round(transmittance * 100, 2),
            "V-number": round(V, 3),
            "Regime": "Single-mode" if V < 2.405 else "Multi-mode",
            "Cost ($)": self.calculate_cost(length_cm)
        }

    def analyze_spectrum(self, fixed_params, test_wl):
        if not self.is_transparent(test_wl): return 0.0
        L_cm = float(fixed_params['len_um']) / 10000.0
        loss = self.props["alpha"] * L_cm
        trans = 10 ** (-loss / 10)
        return round(trans * 100, 2)

# --- 2. S-BEND ---
class SBendWaveguide(GenericComponent):
    def design(self, offset_um, length_um):
        if not self.is_transparent(self.wl): return {"Status": "OPAQUE", "Transmittance (%)": 0}
        
        if offset_um == 0: R_eff = 999999
        else: R_eff = (length_um**2) / (4 * offset_um)
        
        R_critical = self.props["min_bend_radius"]
        loss_bend_db = 0.5 * ((R_critical / (R_eff + 0.1)) ** 2) if R_eff < R_critical else 0.01
        
        length_cm = length_um / 10000.0
        loss_prop = self.props["alpha"] * length_cm
        total_loss = loss_bend_db + loss_prop
        trans = 10 ** (-total_loss / 10)
        
        return {
            "Bend Radius (um)": round(R_eff, 1),
            "Total Loss (dB)": round(total_loss, 3),
            "Transmittance (%)": round(trans * 100, 2),
            "Status": "OK" if R_eff > R_critical else "CRITICAL RADIUS"
        }

    def analyze_spectrum(self, p, wl):
        if not self.is_transparent(wl): return 0.0
        return 95.0

# --- 3. Y-BRANCH ---
class YBranch(GenericComponent):
    def design(self, angle_deg, length_um):
        if not self.is_transparent(self.wl): return {"Status": "OPAQUE", "Transmittance (%)": 0}
        loss_excess = 0.1 * (angle_deg ** 2)
        total_loss = 3.01 + loss_excess
        trans = 10 ** (-total_loss / 10)
        
        return {
            "Type": "Splitter 1x2",
            "Total Loss (dB)": round(total_loss, 3),
            "Transmittance/port (%)": round(trans * 100, 2)
        }
    
    def analyze_spectrum(self, fixed_params, test_wl):
        if not self.is_transparent(test_wl): return 0.0
        return 49.5

# --- 4. MMI (Splitter) ---
class MMI(GenericComponent):
    def design(self, width_um, ports_out):
        if not self.is_transparent(self.wl): return {"Status": "OPAQUE", "Transmittance (%)": 0}
        
        L_pi = (4 * self.n_eff * (width_um**2)) / (3 * self.wl)
        L_opt = (3 * L_pi / 8) if ports_out == 2 else (L_pi / ports_out)
        
        loss_ideal = 10 * math.log10(ports_out)
        trans = 10 ** (-loss_ideal / 10)

        return {
            "L_beat (um)": round(L_pi, 1),
            "Device Length (um)": round(L_opt, 1),
            "Transmittance/port (%)": round(trans * 100, 2)
        }

    def analyze_spectrum(self, fixed_params, test_wl):
        if not self.is_transparent(test_wl): return 0.0
        W = float(fixed_params['width_um'])
        N = int(fixed_params['ports'])
        L_pi_design = (4 * self.n_eff * (W**2)) / (3 * 1.55)
        L_dev_fixed = (3 * L_pi_design / 8) if N == 2 else (L_pi_design / N)
        L_pi_new = (4 * self.n_eff * (W**2)) / (3 * test_wl)
        L_opt_new = (3 * L_pi_new / 8) if N == 2 else (L_pi_new / N)
        ratio = L_dev_fixed / L_opt_new
        efficiency = math.sin( (math.pi/2) * ratio ) ** 2
        return round((1.0/N) * efficiency * 100, 2)

# --- 5. MIRROR & 6. GRATING ---
class Mirror(GenericComponent):
    def design(self, reflectivity):
        R = float(reflectivity)
        return {"Reflectivity (%)": R*100, "Transmittance (%)": round((1-R)*100, 1)}
    def analyze_spectrum(self, p, wl): return 0.0 

class Grating(GenericComponent):
    def design(self, target_wl):
        period = (target_wl) / (2 * self.n_eff)
        return {"Period (nm)": round(period*1000, 1), "Bragg Wavelength": target_wl}
    def analyze_spectrum(self, p, wl): return 0.0