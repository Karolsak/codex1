# Advanced Transformer Analysis & Dynamic Simulation Tool

A comprehensive Python application for transformer analysis, dynamic simulation, and visualization with a modern GUI interface.

## Features

### 1. **Steady-State Analysis**
- **Efficiency Calculation**: Compute transformer efficiency at any load and power factor
- **Voltage Regulation**: Calculate voltage regulation with impedance modeling
- **Loss Calculation**: Determine core losses and copper losses from efficiency data
- **Performance Metrics**: Full-load parameters, rated currents, and power calculations

### 2. **Dynamic Simulation**
- **Real-time ODE Solvers**:
  - Runge-Kutta 4th Order (RK4/RK45) - High accuracy
  - Euler Method - Fast computation
- **Transient Analysis**: Simulate transformer behavior during switching and load changes
- **State Variables**: Track flux, current, voltage, and power in real-time
- **Differential Equations**: Physics-based modeling of transformer dynamics

### 3. **Interactive GUI (Tkinter)**
- **Parameter Sliders**: Adjust all transformer parameters in real-time
  - Rating (kVA)
  - Primary/Secondary Voltages
  - Frequency
  - Maximum Efficiency
  - Impedance
  - Power Factor
  - Simulation Speed
- **Control Buttons**: Start, Stop, Reset simulation
- **Auto-scaling**: Responsive layout that adapts to window size
- **Dark Theme**: Professional appearance optimized for engineering applications

### 4. **Visualization**
- **Multiple Plots**:
  - Current vs Time
  - Voltage vs Time
  - Power vs Time
- **Real-time Updates**: Live plotting during simulation
- **Matplotlib Integration**: High-quality, publication-ready graphics

## Problem Solution

The application solves the following transformer problem:

**Given:**
- Rating: 500 kVA, 3300/500 V, 50 Hz, single-phase
- Maximum efficiency: 97% at 75% full-load, unity power factor
- Impedance: 10%

**Find:**
- Voltage regulation at full-load, 0.8 power factor lagging

**Results:**
```
Core Loss (constant): 5.799 kW
Full Load Copper Loss: 10.309 kW
Voltage Regulation at Full Load (0.8 pf lagging): 7.132%
Full Load Efficiency (0.8 pf): 96.129%
```

## File Structure

```
.
├── transformer_analysis_app.py      # Main GUI application (requires tkinter + matplotlib)
├── transformer_core.py              # Core calculation module (pure Python)
├── test_transformer_calculations.py # Test script with problem solution
└── TRANSFORMER_README.md            # This file
```

## Installation

### Requirements

**For GUI Application:**
```bash
# Python packages
pip install matplotlib numpy

# System packages (for Tkinter)
# Ubuntu/Debian:
sudo apt-get install python3-tk

# Fedora/RHEL:
sudo dnf install python3-tkinter

# macOS (via Homebrew):
brew install python-tk
```

**For Core Calculations Only:**
- Pure Python 3.6+ (no external dependencies)

## Usage

### Running the Full GUI Application

```bash
python3 transformer_analysis_app.py
```

**Features in GUI:**
1. Adjust parameters using sliders in the left panel
2. Select ODE solver method (RK45 or Euler) from the top menu
3. Click "Start" to begin dynamic simulation
4. Watch real-time plots update in the right panel
5. View steady-state results in the bottom panel
6. Click "Stop" to pause, "Reset" to clear and restart

### Running the Problem Solution

```bash
python3 test_transformer_calculations.py
```

This will output the complete solution with step-by-step calculations.

### Using the Core Module in Your Code

```python
from transformer_core import TransformerCalculator, TransformerDynamicModel, ODESolver

# Calculate losses
core_loss, copper_loss = TransformerCalculator.calculate_losses(
    rating_kva=500,
    max_efficiency=0.97,
    load_fraction=0.75
)

# Calculate regulation
regulation = TransformerCalculator.calculate_regulation(
    v2_rated=500,
    impedance_percent=10,
    power_factor=0.8,
    load_fraction=1.0
)

# Calculate efficiency
efficiency = TransformerCalculator.calculate_efficiency(
    core_loss=5.799,
    copper_loss_full=10.309,
    load_fraction=1.0,
    power_factor=0.8,
    rating_kva=500
)

print(f"Regulation: {regulation:.2f}%")
print(f"Efficiency: {efficiency*100:.2f}%")
```

### Dynamic Simulation Example

```python
from transformer_core import TransformerDynamicModel

# Create model
model = TransformerDynamicModel(
    rating_kva=500,
    v1_rated=3300,
    v2_rated=500,
    frequency=50,
    core_loss=5.799,
    copper_loss_full=10.309,
    impedance_percent=10
)

# Simulate for 100 steps
dt = 0.001  # 1 ms time step
for i in range(100):
    model.step(dt, method='rk45')
    values = model.get_instantaneous_values()
    print(f"t={values['time']:.4f}s, I={values['current']:.2f}A, V={values['voltage']:.2f}V")
```

## Mathematical Background

### Efficiency Calculation

At maximum efficiency, core loss equals copper loss:
```
P_core = P_copper = (P_total_loss) / 2
P_copper_full = P_core / (load_fraction²)
```

### Voltage Regulation

```
Regulation = (V_no_load - V_full_load) / V_full_load × 100%
         ≈ load_fraction × (R×cos(φ) + X×sin(φ)) × 100%
```

Where:
- R = resistance component of impedance
- X = reactance component of impedance
- φ = power factor angle

### Differential Equations

The dynamic model uses the following state equations:

```
dΦ/dt = V_primary/a - I×R_eq
dI/dt = (Φ - L_eq×I - V_sec) / L_eq
dV_sec/dt = (I×Z_load - V_sec) / τ_load
```

Where:
- Φ = flux linkage
- I = secondary current
- V_sec = secondary voltage
- a = turns ratio
- R_eq = equivalent resistance
- L_eq = equivalent inductance
- Z_load = load impedance
- τ_load = load time constant

## ODE Solvers

### Euler Method
Simple, fast, first-order accurate:
```
y(t+dt) = y(t) + dt × f(t, y)
```

### Runge-Kutta 4th Order (RK4)
Higher accuracy, fourth-order:
```
k1 = f(t, y)
k2 = f(t+dt/2, y+dt×k1/2)
k3 = f(t+dt/2, y+dt×k2/2)
k4 = f(t+dt, y+dt×k3)
y(t+dt) = y(t) + (dt/6) × (k1 + 2×k2 + 2×k3 + k4)
```

## Practical Applications in Electrical Engineering

1. **Transformer Design**: Optimize parameters for maximum efficiency
2. **Load Analysis**: Study transformer behavior under varying loads
3. **Protection Studies**: Analyze transient conditions during faults
4. **Energy Audits**: Calculate losses and efficiency for economic analysis
5. **Educational Tool**: Visualize transformer dynamics for teaching
6. **Maintenance Planning**: Predict performance degradation

## Advanced Features

### Auto-scaling
The GUI automatically adjusts plot sizes when the window is resized, ensuring optimal visibility at any screen resolution.

### Simulation Speed Control
Adjust the simulation speed from 0.1× to 5× to observe slow transients or quickly reach steady-state.

### Solver Comparison
Switch between RK45 and Euler methods to compare accuracy and computational speed.

### Data Windowing
The application maintains a rolling window of 1000 data points for smooth, responsive plotting.

## Technical Specifications

- **Language**: Python 3.6+
- **GUI Framework**: Tkinter (built-in)
- **Plotting**: Matplotlib
- **Numerical Methods**: Custom ODE solvers
- **Theme**: Dark mode optimized for engineering applications
- **Performance**: 20 FPS animation, 1 ms simulation time step

## Troubleshooting

### GUI doesn't start
- Ensure Tkinter is installed: `python3 -c "import tkinter"`
- Install system Tkinter package (see Installation section)

### Plots don't show
- Ensure Matplotlib is installed: `pip install matplotlib`

### Slow performance
- Reduce simulation speed slider
- Use Euler method instead of RK45
- Close other applications

## License

This educational tool is provided for learning and analysis purposes in electrical engineering.

## Author

Created for advanced transformer analysis and dynamic simulation studies.

## Version

Version 1.0 - Complete implementation with all requested features
