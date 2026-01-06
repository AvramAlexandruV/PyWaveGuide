# fdtd_sim.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D 
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime

class FDTDWindow(tk.Toplevel):
    def __init__(self, parent, params):
        super().__init__(parent)
        self.title(f"FDTD Simulation Lab - {params.get('type', 'Custom')}")
        
        # --- FIX 1: Wider window by 50px (1250 vs 1200) ---
        self.geometry("1250x900")
        
        # --- FIX MEMORY LEAK: Handle window close ---
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- INTERNAL STATE ---
        self.params = params
        self.detectors = [] 
        self.detector_counter = 1
        self.is_placing_detector = False
        self.simulation_running = False
        self.ani = None
        
        # Physical Parameters
        self.parse_params()
        
        # --- LAYOUT ---
        # 1. Plot Area (Top)
        self.plot_frame = tk.Frame(self, bg="white")
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)

        # 2. Controls Area (Bottom)
        self.ctrl_frame = tk.Frame(self, bg="#f0f0f0", bd=2, relief=tk.RAISED, pady=10)
        self.ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.create_controls()
        
        # 3. Initialize Simulation
        self.reset_simulation_data()
        self.draw_geometry_preview()

    def on_close(self):
        """ Cleans up Matplotlib memory on window close """
        if self.ani and self.ani.event_source:
            self.ani.event_source.stop()
        plt.close(self.fig) # Fixes RuntimeWarning
        self.destroy()

    def parse_params(self):
        p = self.params
        self.guide_type = p['type']
        self.pol_mode = p.get('polarization', 'TM')
        self.view_mode = p.get('view_mode', '2D')
        self.real_width = float(p.get('width_um', 2.0))
        self.real_angle = float(p.get('angle_deg', 2.0))
        self.real_offset = float(p.get('offset_um', 5.0))
        self.n_ports = int(p.get('ports', 2))
        
        self.size_x = 300
        self.size_y = 200
        self.default_steps = int(self.size_x * 5)
        
        self.mid_y = self.size_y // 2
        self.src_x, self.src_y = 30, self.mid_y
        self.def_out_x, self.def_out_y = self.size_x - 30, self.mid_y 

    def create_controls(self):
        # --- Section 1: Simulation Control (Always Visible) ---
        frm_sim = tk.LabelFrame(self.ctrl_frame, text="Simulation Control", padx=10, pady=5)
        frm_sim.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        tk.Label(frm_sim, text="Steps:").pack(side=tk.LEFT)
        self.ent_steps = tk.Entry(frm_sim, width=8)
        self.ent_steps.insert(0, str(self.default_steps))
        self.ent_steps.pack(side=tk.LEFT, padx=5)
        
        tk.Button(frm_sim, text="▶ START / RESTART", bg="#4CAF50", fg="white", command=self.start_simulation).pack(side=tk.LEFT, padx=5)

        # Analysis options only for 2D
        if self.view_mode == '2D':
            # --- Section 2: Detector Management ---
            frm_det = tk.LabelFrame(self.ctrl_frame, text="Detector Management", padx=10, pady=5)
            frm_det.pack(side=tk.LEFT, padx=10, fill=tk.Y)
            
            self.btn_add_det = tk.Button(frm_det, text="+ Add Detector", command=self.toggle_add_detector)
            self.btn_add_det.pack(side=tk.LEFT, padx=5)
            
            # Save original color
            self.default_btn_bg = self.btn_add_det.cget('bg') 
            
            tk.Button(frm_det, text="⚙ Edit Detectors", command=self.open_detector_manager).pack(side=tk.LEFT, padx=5)

            # --- Section 3: Results Analysis (Unified) ---
            frm_res = tk.LabelFrame(self.ctrl_frame, text="Result Analysis", padx=10, pady=5)
            frm_res.pack(side=tk.LEFT, padx=10, fill=tk.Y)
            
            tk.Label(frm_res, text="Select Source:").pack(side=tk.LEFT, padx=5)
            
            # Unified Combobox
            self.combo_dets = ttk.Combobox(frm_res, state="readonly", width=20)
            self.combo_dets.pack(side=tk.LEFT, padx=5)
            
            # Dynamic Button
            self.btn_show_res = tk.Button(frm_res, text="View Results", bg="#2196F3", fg="white", command=self.on_show_results_click)
            self.btn_show_res.pack(side=tk.LEFT, padx=5)
            
            self.combo_dets.bind("<<ComboboxSelected>>", self.update_result_button_text)
            
            self.update_combo_detectors()
        else:
            tk.Label(self.ctrl_frame, text="[3D Mode: Numerical analysis disabled]", fg="gray", font=("Arial", 10, "italic")).pack(side=tk.LEFT, padx=20)

    def update_result_button_text(self, event=None):
        selection = self.combo_dets.get()
        if selection:
            short_name = selection.split('(')[0].strip()
            self.btn_show_res.config(text=f"Results: {short_name}")

    def on_show_results_click(self):
        selection = self.combo_dets.get()
        if selection:
            self.show_results(selection)

    def toggle_add_detector(self):
        self.is_placing_detector = not self.is_placing_detector
        if self.is_placing_detector:
            self.btn_add_det.config(bg="orange", text=f"Click on graph (D{self.detector_counter})")
        else:
            self.btn_add_det.config(bg=self.default_btn_bg, text="+ Add Detector")

    def on_canvas_click(self, event):
        if self.view_mode == '3D': return

        if self.is_placing_detector and event.xdata and event.ydata:
            x, y = int(event.xdata), int(event.ydata)
            
            if 0 <= x < self.size_x and 0 <= y < self.size_y:
                label = f"D{self.detector_counter}"
                self.detectors.append({
                    'id': self.detector_counter,
                    'label': label,
                    'x': x, 'y': y,
                    'active': True,
                    'data': []
                })
                self.detector_counter += 1
                self.toggle_add_detector() 
                self.update_combo_detectors()
                self.draw_geometry_preview()
            else:
                messagebox.showwarning("Warning", "Click outside the grid!")

    def update_combo_detectors(self):
        items = ["Output Port (Main)"]
        for d in self.detectors:
            items.append(f"{d['label']} (Detector)")
            
        self.combo_dets['values'] = items
        if items: 
            self.combo_dets.current(len(items)-1)
            self.update_result_button_text()

    def open_detector_manager(self):
        mgr = tk.Toplevel(self)
        mgr.title("Edit Detectors")
        mgr.geometry("400x300")
        
        tk.Label(mgr, text="Detector List", font=("Arial", 10, "bold")).pack(pady=5)
        
        frame_list = tk.Frame(mgr)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)
        
        canvas = tk.Canvas(frame_list)
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not self.detectors:
            tk.Label(scrollable_frame, text="No custom detectors added.").pack()

        for det in self.detectors:
            row = tk.Frame(scrollable_frame, pady=2)
            row.pack(fill=tk.X)
            
            var = tk.BooleanVar(value=det['active'])
            
            def toggle(d=det, v=var):
                d['active'] = v.get()
                self.draw_geometry_preview() 
                
            cb = tk.Checkbutton(row, text=f"{det['label']} (x={det['x']}, y={det['y']})", variable=var, command=toggle)
            cb.pack(side=tk.LEFT)
            
            def delete(d=det, r=row):
                self.detectors.remove(d)
                r.destroy()
                self.update_combo_detectors()
                self.draw_geometry_preview()
                
            btn_del = tk.Button(row, text="-", fg="red", font=("Arial", 8, "bold"), width=3, command=delete)
            btn_del.pack(side=tk.RIGHT, padx=5)

    # --- FDTD SIMULATION ---

    def reset_simulation_data(self):
        self.MainField = np.zeros((self.size_x, self.size_y))
        self.Comp1 = np.zeros((self.size_x, self.size_y))
        self.Comp2 = np.zeros((self.size_x, self.size_y))
        
        self.epsilon = np.ones((self.size_x, self.size_y)) * 1.0
        self.build_geometry()
        self.C_inv = 0.5 / self.epsilon
        
        self.history_input = []
        self.history_out_default = []
        for d in self.detectors:
            d['data'] = []

    def build_geometry(self):
        SCALE = 10.0
        p_width = self.real_width
        sim_epsilon_val = 2.25
        
        if p_width < 1.5: sim_epsilon_val = 1.05 + (p_width / 1.5)
        self.loss_factor = 1.0
        if self.guide_type == "S-Bend" and self.real_offset > 20: self.loss_factor = 0.995
        if self.guide_type == "Y-Branch" and self.real_angle > 10: self.loss_factor = 0.995

        def draw_rect(y, w, start=0, end=None):
            if end is None: end = self.size_x
            self.epsilon[start:end, y-w:y+w] = sim_epsilon_val

        w_px = 6 

        if self.guide_type == "Straight Guide":
            draw_rect(self.mid_y, w_px)

        elif self.guide_type == "S-Bend":
            bend_len = 120; offset = 30; start_x = 30
            draw_rect(self.mid_y, w_px, 0, start_x)
            for i in range(start_x, start_x + bend_len):
                if i >= self.size_x: break
                u = (i - start_x) / bend_len
                s = 0.5 * (1 - np.cos(np.pi * u))
                cy = int(self.mid_y + s * offset)
                self.epsilon[i, cy-w_px:cy+w_px] = sim_epsilon_val
            draw_rect(self.mid_y+offset, w_px, start_x+bend_len, self.size_x)
            self.def_out_y = self.mid_y + offset

        elif self.guide_type == "Y-Branch":
            draw_rect(self.mid_y, w_px, 0, 50)
            slope = 0.3
            for i in range(50, self.size_x):
                shift = int((i - 50) * slope)
                if self.mid_y+shift+6 < self.size_y: self.epsilon[i, self.mid_y+shift-6:self.mid_y+shift+6] = sim_epsilon_val
                if self.mid_y-shift-6 > 0:      self.epsilon[i, self.mid_y-shift-6:self.mid_y-shift+6] = sim_epsilon_val
            self.def_out_y = self.mid_y + int((self.size_x - 70) * slope)

        elif self.guide_type == "MMI (Splitter)":
            draw_rect(self.mid_y, 5, 0, 40)
            vis_w = 20 if self.n_ports > 2 else 12
            draw_rect(self.mid_y, vis_w, 40, 140)
            out_spacing = 15
            start_y_out = self.mid_y - ((self.n_ports-1) * out_spacing)/2
            for k in range(self.n_ports):
                oy = int(start_y_out + k * out_spacing)
                self.epsilon[140:, oy-5:oy+5] = sim_epsilon_val
                if k==0: self.def_out_y = oy
        
        elif self.guide_type == "Grating (Bragg)":
            draw_rect(self.mid_y, w_px)
            for i in range(60, 160, 15):
                self.epsilon[i:i+6, self.mid_y-9:self.mid_y+9] = sim_epsilon_val
        else:
            draw_rect(self.mid_y, w_px)

    def draw_geometry_preview(self):
        self.ax.clear()
        if self.view_mode == '2D':
            if isinstance(self.ax, Axes3D):
                 self.ax.remove()
                 self.ax = self.fig.add_subplot(111)

            self.ax.imshow(np.zeros((self.size_y, self.size_x)), cmap='magma', vmin=0, vmax=0.15, origin='lower')
            self.ax.contour(self.epsilon.T, levels=[1.1], colors='cyan', linewidths=1.0, alpha=0.5)
            
            self.ax.plot(self.src_x, self.src_y, 'wo'); self.ax.text(self.src_x, self.src_y - 15, "IN", color='white')
            
            self.ax.plot(self.def_out_x, self.def_out_y, 'go', markersize=8, markeredgecolor='white')
            self.ax.text(self.def_out_x, self.def_out_y - 15, "OUT", color='lime', fontweight='bold')
            
            for d in self.detectors:
                if d['active']:
                    self.ax.plot(d['x'], d['y'], 'yo', markersize=6)
                    self.ax.text(d['x'], d['y'] + 10, d['label'], color='yellow', fontsize=8)
            
            self.ax.set_title(f"Configuration: {self.guide_type} [{self.pol_mode}]")
        
        elif self.view_mode == '3D':
            if not isinstance(self.ax, Axes3D):
                self.ax.remove()
                self.ax = self.fig.add_subplot(111, projection='3d')
            
            X, Y = np.meshgrid(np.arange(self.size_y), np.arange(self.size_x))
            self.ax.plot_surface(X, Y, np.zeros((self.size_x, self.size_y)), cmap='magma')
            self.ax.set_title("3D Preview")

        self.canvas.draw()

    def start_simulation(self):
        if self.ani and self.ani.event_source:
            self.ani.event_source.stop()
        
        self.reset_simulation_data()
        
        try:
            self.total_steps = int(self.ent_steps.get())
        except:
            self.total_steps = self.default_steps
            
        steps_per_frame = 5
        self.n_frames = self.total_steps // steps_per_frame
        
        self.X, self.Y = np.meshgrid(np.arange(self.size_y), np.arange(self.size_x))
        
        self.ax.clear()
        if self.view_mode == '3D':
             if not isinstance(self.ax, Axes3D): 
                self.ax.remove()
                self.ax = self.fig.add_subplot(111, projection='3d')
             self.surf = self.ax.plot_surface(self.X, self.Y, np.abs(self.MainField), cmap='magma', vmin=0, vmax=0.15)
             self.ax.set_zlim(0, 0.2)
        else:
             if isinstance(self.ax, Axes3D):
                 self.ax.remove()
                 self.ax = self.fig.add_subplot(111)
             self.im = self.ax.imshow(np.abs(self.MainField.T), cmap='magma', vmin=0, vmax=0.15, origin='lower')
             self.ax.contour(self.epsilon.T, levels=[1.1], colors='cyan', linewidths=1.0, alpha=0.5)
             
             self.ax.plot(self.src_x, self.src_y, 'wo')
             self.ax.plot(self.def_out_x, self.def_out_y, 'go')
             for d in self.detectors:
                 if d['active']:
                     self.ax.plot(d['x'], d['y'], 'yo', markersize=5)
                     self.ax.text(d['x'], d['y']+5, d['label'], color='yellow', fontsize=8)

        t0 = 40; spread = 12
        def source(t):
            return np.exp(-0.5 * ((t - t0) / spread) ** 2) * np.sin(2 * np.pi * t / 20)

        def update(frame):
            for _ in range(steps_per_frame):
                t = frame * steps_per_frame + _
                
                if self.pol_mode == 'TM':
                    self.Comp1[:, :-1] -= 0.5 * (self.MainField[:, 1:] - self.MainField[:, :-1])
                    self.Comp2[:-1, :] += 0.5 * (self.MainField[1:, :] - self.MainField[:-1, :])
                    self.MainField[1:, 1:] += self.C_inv[1:, 1:] * ((self.Comp2[1:, 1:] - self.Comp2[:-1, 1:]) - (self.Comp1[1:, 1:] - self.Comp1[1:, :-1]))
                else: # TE
                    self.Comp1[:, 1:] += self.C_inv[:, 1:] * (self.MainField[:, 1:] - self.MainField[:, :-1])
                    self.Comp2[1:, :] -= self.C_inv[1:, :] * (self.MainField[1:, :] - self.MainField[:-1, :])
                    self.MainField[:-1, :-1] += 0.5 * ((self.Comp1[:-1, 1:] - self.Comp1[:-1, :-1]) - (self.Comp2[1:, :-1] - self.Comp2[:-1, :-1]))

                src_val = source(t)
                self.MainField[self.src_x, self.src_y] += src_val
                if self.loss_factor < 1.0: self.MainField *= self.loss_factor

                self.history_input.append(abs(src_val))
                self.history_out_default.append(abs(self.MainField[self.def_out_x, self.def_out_y]))
                
                for d in self.detectors:
                    if d['active']:
                        d['data'].append(abs(self.MainField[d['x'], d['y']]))

            mag_field = np.abs(self.MainField)
            if self.view_mode == '3D':
                self.ax.clear()
                self.ax.set_zlim(0, 0.2)
                self.ax.plot_surface(self.X, self.Y, mag_field, cmap='magma', vmin=0, vmax=0.15, rstride=5, cstride=5, shade=False)
                self.ax.set_title(f"3D Simulation (Step {t})")
            else:
                self.im.set_array(mag_field.T)
                self.ax.set_title(f"FDTD Simulation (Step {t}/{self.total_steps})")
                return [self.im]

        self.ani = FuncAnimation(self.fig, update, frames=self.n_frames, interval=1, blit=False, repeat=False)
        self.canvas.draw()

    def show_results(self, selection_str):
        if not self.history_input:
            messagebox.showinfo("Info", "Run simulation first!")
            return

        target_label = selection_str.split('(')[0].strip()
        
        if "Output Port" in selection_str:
            data = self.history_out_default
            display_name = "Output Port (Main)"
        else:
            det = next((d for d in self.detectors if d['label'] == target_label), None)
            if not det: 
                messagebox.showerror("Error", "Detector not found.")
                return
            if not det['data']: 
                messagebox.showwarning("Warn", f"Detector {target_label} has no recorded data.")
                return
            data = det['data']
            display_name = f"Detector {target_label}"

        res_win = tk.Toplevel(self)
        res_win.title(f"Results: {display_name}")
        res_win.geometry("800x500")
        
        # --- FIX MEMORY LEAK: Explicitly close figure ---
        def on_res_close():
            plt.close(fig_res)
            res_win.destroy()
        res_win.protocol("WM_DELETE_WINDOW", on_res_close)

        fig_res, ax_res = plt.subplots(figsize=(8, 4))
        
        ax_res.plot(self.history_input, 'r-', label='Input Pulse', alpha=0.5)
        ax_res.plot(data, 'g-', label=f'{display_name} Signal', linewidth=2)
        ax_res.fill_between(range(len(data)), data, color='green', alpha=0.1)
        
        max_in = np.max(self.history_input) if np.max(self.history_input) > 0 else 1
        max_out = np.max(data)
        eff = (max_out/max_in)*100
        
        ax_res.set_title(f"Signal Analysis - {display_name} (Transmission: {eff:.2f}%)")
        ax_res.legend()
        ax_res.grid(True, alpha=0.3)

        canvas_res = FigureCanvasTkAgg(fig_res, master=res_win)
        canvas_res.draw()
        canvas_res.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        btn_exp = tk.Button(res_win, text="Export Data (.csv)", bg="#FF9800", fg="white",
                           command=lambda: self.export_data(display_name, data, eff))
        btn_exp.pack(pady=10)

    def export_data(self, label, data, eff):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(f"# Export Data - {label}\n")
                    f.write(f"# Date: {timestamp}\n")
                    f.write(f"# Efficiency: {eff:.4f}%\n")
                    f.write("TimeStep,Input,Output\n")
                    for t, (i, o) in enumerate(zip(self.history_input, data)):
                        f.write(f"{t},{i:.6f},{o:.6f}\n")
                messagebox.showinfo("Success", "Data saved!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

def run_fdtd_demo(params):
    win = FDTDWindow(None, params)