# fdtd_sim.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def run_fdtd_demo(params):
    """
    Runs a 2D FDTD simulation respecting geometric parameters.
    """
    if isinstance(params, dict):
        guide_type = params['type']
        try:
            requested_ports = int(params.get('ports', 2))
        except:
            requested_ports = 2
    else:
        guide_type = params
        requested_ports = 2

    # --- 1. Grid Parameters ---
    size_x = 200        
    size_y = 120        
    steps = 1000         
    
    # Fields
    Ez = np.zeros((size_x, size_y))
    Hx = np.zeros((size_x, size_y))
    Hy = np.zeros((size_x, size_y))
    
    # Geometry (Epsilon)
    epsilon = np.ones((size_x, size_y)) * 1.0 
    mid_y = size_y // 2
    
    # Default locations
    src_x, src_y = 20, mid_y
    det_x, det_y = size_x - 20, mid_y 

    # --- DYNAMIC GEOMETRY CONSTRUCTION ---
    if guide_type == "Straight Guide":
        epsilon[:, mid_y-6:mid_y+6] = 2.25

    elif guide_type == "S-Bend":
        bend_len = 140
        offset = 30  
        start_x = 30
        
        epsilon[0:start_x, mid_y-6:mid_y+6] = 2.25
        
        for i in range(start_x, start_x + bend_len):
            if i >= size_x: break
            u = (i - start_x) / bend_len
            s_factor = 0.5 * (1 - np.cos(np.pi * u))
            center_curr = int(mid_y + s_factor * offset)
            epsilon[i, center_curr-6:center_curr+6] = 2.25
            
        end_x = start_x + bend_len
        final_center = mid_y + offset
        if end_x < size_x:
            epsilon[end_x:, final_center-6:final_center+6] = 2.25
        det_y = final_center

    elif guide_type == "Y-Branch":
        epsilon[0:50, mid_y-6:mid_y+6] = 2.25
        for i in range(50, size_x):
            shift = int((i - 50) * 0.3)
            if mid_y+6+shift < size_y: epsilon[i, mid_y-6+shift:mid_y+6+shift] = 2.25 
            if mid_y-6-shift > 0: epsilon[i, mid_y-6-shift:mid_y+6-shift] = 2.25
        # Detector on top arm
        det_y = mid_y + int((size_x - 20 - 50) * 0.3)

    elif guide_type == "MMI (Splitter)":
        n_ports = min(requested_ports, 4)
        if n_ports < 2: n_ports = 2 
        
        # 1. Input
        epsilon[0:40, mid_y-5:mid_y+5] = 2.25
        
        # 2. MMI Body
        mmi_width = 15 + (n_ports * 8)
        epsilon[40:140, mid_y-mmi_width:mid_y+mmi_width] = 2.25 
        
        # 3. Dynamic Outputs
        spacing = 16 
        start_y = mid_y - ((n_ports - 1) * spacing) / 2
        
        detector_placed = False
        
        for i in range(n_ports):
            y_pos = int(start_y + i * spacing)
            epsilon[140:, y_pos-5:y_pos+5] = 2.25
            
            # Place detector on first port
            if i == 0: 
                det_y = y_pos
                detector_placed = True

    elif guide_type == "Grating (Bragg)":
        epsilon[:, mid_y-6:mid_y+6] = 2.25
        for i in range(60, 160, 12):
            epsilon[i:i+6, mid_y-9:mid_y+9] = 2.25
            
    else:
        # Fallback Mirror or others
        epsilon[:, mid_y-6:mid_y+6] = 2.25

    # Coefficients
    C_inv = 0.5 / epsilon

    # History
    history_input = []
    history_output = []

    # --- GRAPHICS SETUP ---
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(Ez.T, cmap='RdBu', vmin=-0.2, vmax=0.2, origin='lower')
    ax.contour(epsilon.T, levels=[1.1], colors='black', linewidths=1.5, alpha=0.3)
    
    # Markers
    ax.plot(src_x, src_y, 'ro', label="Source")
    ax.text(src_x, src_y - 15, "IN", color='red', ha='center')
    
    ax.plot(det_x, det_y, 'go', label="Detector")
    ax.text(det_x, det_y - 15, "OUT", color='green', ha='center')
    
    title_extra = ""
    if guide_type == "MMI (Splitter)":
        title_extra = f"\n(Config: 1 x {min(requested_ports, 4)})"
        
    ax.set_title(f"FDTD Simulation: {guide_type}{title_extra}")
    ax.legend(loc='upper left')

    # Source
    t0 = 40
    spread = 12
    def source(t):
        return np.exp(-0.5 * ((t - t0) / spread) ** 2) * np.sin(2 * np.pi * t / 20)

    # Update Loop
    def update(t):
        nonlocal Ez, Hx, Hy
        Hx[:, :-1] -= 0.5 * (Ez[:, 1:] - Ez[:, :-1])
        Hy[:-1, :] += 0.5 * (Ez[1:, :] - Ez[:-1, :])
        Ez[1:, 1:] += C_inv[1:, 1:] * ((Hy[1:, 1:] - Hy[:-1, 1:]) - (Hx[1:, 1:] - Hx[1:, :-1]))
        
        src_val = source(t)
        Ez[src_x, src_y] += src_val
        det_val = Ez[det_x, det_y]
        
        history_input.append(abs(src_val))
        history_output.append(abs(det_val))
        
        im.set_array(Ez.T)
        return [im]

    ani = FuncAnimation(fig, update, frames=steps, interval=10, blit=False, repeat=False)
    plt.show()

    # --- FINAL PLOT ---
    plot_transmission(history_input, history_output, guide_type, requested_ports)

def plot_transmission(input_sig, output_sig, title, n_ports=1):
    plt.figure(figsize=(8, 5))
    plt.plot(input_sig, 'r-', label='Input (Source)', alpha=0.6)
    plt.plot(output_sig, 'g-', label='Output (Single Arm)', linewidth=2)
    plt.fill_between(range(len(output_sig)), output_sig, color='green', alpha=0.1)
    
    plt.title(f"Signal Analysis: {title}")
    plt.xlabel("Time Steps")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Efficiency
    max_in = np.max(input_sig) if np.max(input_sig) > 0 else 1
    max_out = np.max(output_sig)
    eff = (max_out / max_in) * 100
    
    # Note
    note = f"Transmission per arm: {eff:.1f}%"
    if title == "MMI (Splitter)":
        note += f"\n(Theoretical 1/{n_ports}: {100/n_ports:.1f}%)"
        
    plt.text(0.02, 0.90, note, transform=plt.gca().transAxes, 
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray'))
    
    plt.show()

if __name__ == "__main__":
    run_fdtd_demo({'type': 'MMI (Splitter)', 'ports': 4})