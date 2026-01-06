# gui_app.py
import tkinter as tk
from tkinter import ttk, messagebox
import optimizer
import materials
import fdtd_sim

class OpticalDesignApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyWaveGuide - Integrated Optical Design Suite")
        self.root.geometry("1000x700") 
        
        # --- LAYOUT ---
        left_panel = tk.Frame(root, width=380, bg="#f5f5f5", padx=10, pady=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        right_panel = tk.Frame(root, bg="white", padx=10, pady=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # === CONTROLS (LEFT) ===
        tk.Label(left_panel, text="Component Configuration", font=("Segoe UI", 12, "bold"), bg="#f5f5f5").pack(pady=10)
        
        # 1. Type
        tk.Label(left_panel, text="Component Type:", bg="#f5f5f5", anchor="w").pack(fill=tk.X)
        self.comp_type_var = tk.StringVar()
        self.combo_comp = ttk.Combobox(left_panel, textvariable=self.comp_type_var, state="readonly")
        self.combo_comp['values'] = ("Straight Guide", "S-Bend", "Y-Branch", "MMI (Splitter)", "Mirror", "Grating (Bragg)")
        self.combo_comp.current(0)
        self.combo_comp.pack(fill=tk.X, pady=(0, 15))
        self.combo_comp.bind("<<ComboboxSelected>>", self.on_comp_change)

        # 2. Material
        tk.Label(left_panel, text="Core Material:", bg="#f5f5f5", anchor="w").pack(fill=tk.X)
        self.mat_var = tk.StringVar()
        self.combo_mat = ttk.Combobox(left_panel, textvariable=self.mat_var, state="readonly")
        self.combo_mat['values'] = materials.get_material_names()
        self.combo_mat.current(0)
        self.combo_mat.pack(fill=tk.X, pady=(0, 15))

        # 3. Polarization
        tk.Label(left_panel, text="Polarization Mode (Calculation):", bg="#f5f5f5", anchor="w").pack(fill=tk.X)
        self.pol_var = tk.StringVar()
        self.combo_pol = ttk.Combobox(left_panel, textvariable=self.pol_var, state="readonly")
        self.combo_pol['values'] = ("TM Mode (Transverse Magnetic)", "TE Mode (Transverse Electric)")
        self.combo_pol.current(0)
        self.combo_pol.pack(fill=tk.X, pady=(0, 15))

        # 4. Dynamic Params
        self.dynamic_frame = tk.Frame(left_panel, bg="#f5f5f5")
        self.dynamic_frame.pack(fill=tk.X, pady=10)
        self.entries = {}
        
        # 5. Buttons
        btn_frame = tk.Frame(left_panel, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(btn_frame, text="CALCULATE DESIGN", command=self.run_calc, 
                  bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"), height=2).pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(btn_frame, text="GENERATE DATASHEET (COMPARE)", command=self.open_datasheet, 
                  bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), height=2).pack(fill=tk.X, pady=(0, 10))

        tk.Button(btn_frame, text="▶ RUN FDTD SIMULATION", command=self.ask_simulation_mode, 
                  bg="#D32F2F", fg="white", font=("Segoe UI", 10, "bold"), height=2).pack(fill=tk.X)

        # === VISUALIZATION (RIGHT) ===
        tk.Label(right_panel, text="Schematic Preview", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.canvas = tk.Canvas(right_panel, width=500, height=250, bg="#FAFAFA", bd=1, relief="solid")
        self.canvas.pack(pady=(5, 20))
        
        tk.Label(right_panel, text="Calculated Parameters:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.result_text = tk.Text(right_panel, height=14, bg="#E8F5E9", font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.on_comp_change(None)

    def on_comp_change(self, event):
        comp = self.comp_type_var.get()
        for widget in self.dynamic_frame.winfo_children(): widget.destroy()
        self.entries = {}
        
        self.add_entry("wavelength", "Wavelength (um):", "1.55")
        
        if comp == "Straight Guide":
            self.add_entry("len_um", "Length (um):", "1000.0") 
            self.add_entry("width_um", "Waveguide Width (um):", "2.0")
        elif comp == "S-Bend":
            self.add_entry("offset_um", "Offset (um):", "50")
            self.add_entry("len_um", "Length (um):", "200")
        elif comp == "Y-Branch":
            self.add_entry("angle_deg", "Angle (deg):", "2.0")
            self.add_entry("len_um", "Length (um):", "100")
        elif comp == "MMI (Splitter)":
            self.add_entry("width_um", "MMI Width (um):", "6.0")
            self.add_entry("ports", "Ports (Max 4 for FDTD):", "2")
        elif comp == "Mirror":
            self.add_entry("reflectivity", "Reflectivity (0-1):", "0.9")
        elif comp == "Grating (Bragg)":
            self.add_entry("target_wl", "Bragg Lambda (um):", "1.55")
            
        self.draw_schematic(comp)

    def add_entry(self, key, label, val):
        tk.Label(self.dynamic_frame, text=label, bg="#f5f5f5").pack(anchor="w")
        e = tk.Entry(self.dynamic_frame); e.insert(0, val); e.pack(fill=tk.X)
        self.entries[key] = e

    def get_params(self):
        p = {'type': self.comp_type_var.get(), 'material': self.mat_var.get()}
        p['wl'] = self.entries['wavelength'].get()
        p['polarization'] = "TM" if "TM" in self.pol_var.get() else "TE"
        for k, e in self.entries.items(): 
            if k!='wavelength': p[k] = e.get()
        return p

    def draw_schematic(self, comp_type):
        self.canvas.delete("all")
        W, H = 500, 250
        cx, cy = W/2, H/2
        
        self.canvas.create_text(30, 20, text=comp_type, anchor="w", fill="#CCC", font=("Arial", 14, "bold"))
        
        if comp_type == "Straight Guide":
            self.canvas.create_rectangle(50, cy-15, 450, cy+15, fill="#2196F3", outline="black")
            self.canvas.create_text(cx, cy+35, text="Length L", fill="black")
            self.canvas.create_line(50, cy+25, 450, cy+25, arrow=tk.BOTH)
        elif comp_type == "S-Bend":
            coords = [50, cy+40, 200, cy+40, 300, cy-40, 450, cy-40]
            self.canvas.create_line(coords, smooth=True, width=20, fill="#2196F3", capstyle=tk.ROUND)
            self.canvas.create_line(470, cy-40, 470, cy+40, arrow=tk.BOTH, fill="red")
            self.canvas.create_text(485, cy, text="Off", fill="red")
        elif comp_type == "Y-Branch":
            self.canvas.create_line(50, cy, 200, cy, width=20, fill="#2196F3", capstyle=tk.ROUND)
            self.canvas.create_line(200, cy, 400, cy-60, width=15, fill="#2196F3", capstyle=tk.ROUND)
            self.canvas.create_line(200, cy, 400, cy+60, width=15, fill="#2196F3", capstyle=tk.ROUND)
            self.canvas.create_arc(230, cy-40, 270, cy+40, start=-30, extent=60, style=tk.ARC, outline="red", width=2)
            self.canvas.create_text(290, cy, text="Angle", fill="red")
        elif comp_type == "MMI (Splitter)":
            self.canvas.create_line(50, cy, 150, cy, width=10, fill="#2196F3")
            self.canvas.create_rectangle(150, cy-40, 350, cy+40, fill="#1976D2", outline="black")
            self.canvas.create_text(250, cy, text="Multimode\nInterference", fill="white", justify=tk.CENTER)
            self.canvas.create_line(350, cy-20, 450, cy-20, width=10, fill="#2196F3")
            self.canvas.create_line(350, cy+20, 450, cy+20, width=10, fill="#2196F3")
        elif comp_type == "Mirror":
            self.canvas.create_line(50, cy, 400, cy, width=20, fill="#2196F3")
            self.canvas.create_rectangle(400, cy-30, 410, cy+30, fill="silver", outline="black")
            self.canvas.create_line(400, cy, 300, cy-50, arrow=tk.LAST, fill="red", width=2, dash=(4,2))
            self.canvas.create_text(320, cy-60, text="R", fill="red")
        elif comp_type == "Grating (Bragg)":
            self.canvas.create_rectangle(50, cy-15, 450, cy+15, fill="#BBDEFB", outline="")
            for x in range(100, 400, 20):
                self.canvas.create_rectangle(x, cy-15, x+10, cy+15, fill="#1565C0", outline="")
            self.canvas.create_text(cx, cy+40, text="Period", fill="blue")

    def run_calc(self):
        try:
            res = optimizer.run_simulation(self.get_params())
            self.result_text.delete(1.0, tk.END)
            txt = f"SIMULATION RESULTS ({self.comp_type_var.get()})\n"
            txt += "=" * 40 + "\n"
            for k, v in res.items(): txt += f"{k:30} : {v}\n"
            self.result_text.insert(tk.END, txt)
        except Exception as e: messagebox.showerror("Err", str(e))

    def open_datasheet(self):
        try:
            params = self.get_params()
            mat_names, spectral_data = optimizer.generate_comparative_datasheet(params)
            ds_win = tk.Toplevel(self.root)
            ds_win.title(f"Comparative Study: {params['type']}")
            ds_win.geometry("1100x600")
            tk.Label(ds_win, text="TRANSMITTANCE (%) IN VISIBLE (380-780nm)", font=("Arial", 12, "bold"), pady=10).pack()
            columns = ["Wavelength (um)"] + mat_names
            tree = ttk.Treeview(ds_win, columns=columns, show='headings')
            scr = ttk.Scrollbar(ds_win, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scr.set); scr.pack(side=tk.RIGHT, fill=tk.Y)
            tree.heading("Wavelength (um)", text="Wavelength (um)"); tree.column("Wavelength (um)", width=120, anchor="center")
            for m in mat_names: tree.heading(m, text=m); tree.column(m, width=100, anchor="center")
            for row in spectral_data:
                vals = [row["Wavelength (um)"]]
                for m in mat_names: vals.append(row[m])
                tree.insert("", tk.END, values=vals)
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        except Exception as e: messagebox.showerror("Err", str(e))

    def ask_simulation_mode(self):
        popup = tk.Toplevel(self.root)
        popup.title("Select View")
        popup.geometry("400x180")
        popup.resizable(False, False)
        tk.Label(popup, text="Select Simulation View Mode:", font=("Segoe UI", 11, "bold")).pack(pady=15)
        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        def run_2d():
            popup.destroy()
            self.launch_fdtd("2D")
        def run_3d():
            popup.destroy()
            self.launch_fdtd("3D")

        tk.Button(btn_frame, text="2D VIEW\n(Top Down)", command=run_2d, 
                  bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"), height=3).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Button(btn_frame, text="3D VIEW\n(Surface Plot)", command=run_3d, 
                  bg="#673AB7", fg="white", font=("Segoe UI", 10, "bold"), height=3).pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    def launch_fdtd(self, view_mode):
        params = self.get_params()
        params['view_mode'] = view_mode
        try:
            # We removed the messagebox that was blocking execution
            fdtd_sim.run_fdtd_demo(params)
        except Exception as e:
            messagebox.showerror("FDTD Error", f"Simulation failed:\n{e}")
            
if __name__ == "__main__":
    root = tk.Tk()
    app = OpticalDesignApp(root)
    root.mainloop()