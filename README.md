# PyWaveGuide

PyWaveGuide is a desktop application designed for the engineering and simulation of integrated optical components. It serves as a dual-purpose tool: a calculator for sizing photonic structures based on physical theory, and a numerical simulator using the Finite-Difference Time-Domain (FDTD) method to visualize electromagnetic wave propagation.

## Functionality Overview

The application is split into two main operational modes: Analytical Design and Numerical Simulation.

### 1. Component Design
The main interface allows users to configure specific geometric parameters for various optical components. All dimensions are specified in micrometers (um).

* **Straight Waveguide:** Calculates mode regimes (V-number) and cut-off wavelengths based on width and core material.
* **S-Bend:** Estimates radiation losses based on the offset and effective bend radius.
* **Y-Branch:** Models a 1x2 splitter, calculating losses based on the branching angle.
* **MMI Splitter:** Uses Multimode Interference theory to calculate the optimal length ($L_\pi$) for $1 \times N$ splitters.
* **Bragg Grating:** Calculates the required grating period for a specific target wavelength.

**Material Database:** Users can select from real-world materials (Silicon, Silica, Silicon Nitride, Indium Phosphide), which automatically updates refractive indices and loss coefficients used in calculations.

### 2. FDTD Simulation Laboratory
The application includes a comprehensive FDTD engine that simulates light propagation through the designed component.

**Simulation Features:**
* **Polarization Control:** Users can switch between Transverse Magnetic (TM) and Transverse Electric (TE) modes. This alters the Maxwell equations used in the update loop, affecting how the field interacts with boundaries and bends.
* **2D & 3D Visualization:** * **2D View:** A top-down intensity map showing the wave propagation.
    * **3D View:** A surface elevation plot representing the field magnitude in real-time.
* **Interactive Detectors:** Users can place custom measurement points (detectors) anywhere on the simulation grid to analyze the field at specific locations (e.g., measuring leakage or signal measuring at specific output ports).

## How to Use the Simulation

When you click "Run FDTD Simulation," a dedicated laboratory window opens.

### Controls
* **Steps:** Defines the duration of the simulation. The default value is calculated automatically based on the grid size to ensure the pulse reaches the output. You can increase this value for longer structures or to observe reflections.
* **Add Detector:** Click this button to enter placement mode. Clicking anywhere on the simulation grid will place a yellow detector labeled D1, D2, etc.
* **Edit Detectors:** Opens a manager window where you can toggle detectors on/off or delete them. Disabling a detector removes it from the visualization immediately.
* **Start/Restart:** Begins the time-domain simulation.

### Data Analysis and Export
After the simulation concludes, you can analyze the signal data:
1.  **Select Source:** Choose between the default "Output Port (Main)" or any custom detector (D1, D2...) from the dropdown list.
2.  **View Results:** Opens a detailed graph for the selected measurement point.
3.  **Export Data:** Saves the simulation data to a `.csv` file. The file includes a header with metadata (efficiency, parameters, timestamp) followed by columns for Time Step, Input Signal, and Output Signal.

## Interpreting the Graphs

The result graphs display **Signal Amplitude vs. Time Steps**.

* **Red Line (Input Pulse):** Represents the Gaussian pulse injected at the source. This is the reference signal.
* **Green Line (Output Signal):** Represents the electromagnetic field magnitude measured at the selected detector location.

**Understanding the Data:**
* **Time Delay:** The gap between the red pulse and the green pulse represents the time of flight—how long it took light to travel through the component.
* **Amplitude Reduction:** If the green peak is lower than the red peak, it indicates loss. This loss comes from material absorption, radiation at bends, or insertion loss (coupling inefficiency).
* **Transmission Efficiency:** Displayed in the graph title. This is the ratio of the maximum output amplitude to the maximum input amplitude.
    * *Note:* A simulation efficiency of ~20-40% is common for straight waveguides in raw FDTD because it simulates the physical coupling of a point source into a waveguide, where significant energy is lost at the interface (insertion loss). This differs from the analytical "Design" tab, which assumes ideal conditions (100% internal transmission).

## Installation and Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/AvramAlexandruV/PyWaveGuide](https://github.com/AvramAlexandruV/PyWaveGuide)
    cd PyWaveGuide
    ```

2.  **Install dependencies**
    The project requires `numpy` for matrix calculations and `matplotlib` for visualization.
    ```bash
    pip install numpy matplotlib
    ```

3.  **Run the Application**
    ```bash
    python gui_app.py
    ```

## Technical Architecture

* **Language:** Python 3
* **GUI Framework:** Tkinter (Standard library)
* **Physics Engine:** NumPy (Vectorized operations for performance)
* **Visualization:** Matplotlib (Animation and Plotting) using the `FigureCanvasTkAgg` backend for integration.

---
*Created as a personal project to explore optical engineering and computational electromagnetics.*