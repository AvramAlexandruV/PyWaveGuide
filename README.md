# PyWaveGuide

**PyWaveGuide** is a desktop application for designing and simulating integrated optical components. 

It combines two things:
1.  **Design Tools:** Instantly calculates the correct sizes for components like waveguides, splitters, and bends.
2.  **Simulation Engine:** Visualizes how light moves through these shapes using a physics algorithm called FDTD (Finite-Difference Time-Domain).

## What It Does

* **Design & Analyze:** Create Straight Waveguides, S-Bends, Y-Branches, and MMI Splitters.
* **Visualize Physics:** Watch real-time animations of light pulses propagating through your design.
* **Material Library:** Choose between real-world materials (Silicon, Silicon Nitride, Indium Phosphide) to see how they affect performance.
* **Compare Results:** Generate datasheets to compare transparency and costs across different materials.

## Setup

1.  **Clone the repo**
    ```bash
    git clone https://github.com/AvramAlexandruV/PyWaveGuide
    cd PyWaveGuide
    ```

2.  **Install requirements**
    ```bash
    pip install numpy matplotlib
    ```

3.  **Run the App**
    ```bash
    python gui_app.py
    ```

## Built With

* **Python 3**
* **Tkinter** (User Interface)
* **NumPy** (High-performance physics calculations)
* **Matplotlib** (Plotting and Animation)

---
*Created as a personal project to explore optical engineering and software simulation.*
