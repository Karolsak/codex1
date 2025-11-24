"""
Advanced Transformer Analysis and Dynamic Simulation Tool
Features:
- Transformer efficiency and regulation calculations
- Dynamic simulation with ODE solvers (RK45 and Euler)
- Real-time visualization
- Auto-scaling GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math


class TransformerCalculator:
    """Calculate transformer parameters and performance"""

    @staticmethod
    def calculate_losses(rating_kva, max_efficiency, load_fraction):
        """
        Calculate core and copper losses from efficiency data

        Args:
            rating_kva: Transformer rating in kVA
            max_efficiency: Maximum efficiency (decimal)
            load_fraction: Load fraction at max efficiency

        Returns:
            tuple: (core_loss_kw, copper_loss_full_kw)
        """
        # At maximum efficiency: copper loss = core loss
        # Total loss at max efficiency = rating * load_fraction * (1 - efficiency) / efficiency
        rating_kw = rating_kva  # Assuming unity power factor
        output_at_max_eff = rating_kw * load_fraction
        total_loss_at_max_eff = output_at_max_eff * (1 - max_efficiency) / max_efficiency

        # At max efficiency: P_core = P_copper
        # P_copper = load_fraction^2 * P_copper_full
        # Total loss = P_core + load_fraction^2 * P_copper_full
        # At max efficiency: P_core = load_fraction^2 * P_copper_full
        # So: P_copper_full = P_core / load_fraction^2

        core_loss = total_loss_at_max_eff / 2
        copper_loss_full = core_loss / (load_fraction ** 2)

        return core_loss, copper_loss_full

    @staticmethod
    def calculate_regulation(v2_rated, impedance_percent, power_factor, load_fraction=1.0):
        """
        Calculate voltage regulation

        Args:
            v2_rated: Rated secondary voltage
            impedance_percent: Percentage impedance
            power_factor: Load power factor
            load_fraction: Load fraction (0-1)

        Returns:
            float: Regulation percentage
        """
        # Impedance per unit
        z_pu = impedance_percent / 100

        # Assume X/R ratio typical for power transformers (approximately 5-10)
        # For 10% impedance, typical split: R ≈ 1-2%, X ≈ 8-9%
        # We'll use R = 0.015 pu, X = 0.09926 pu to get Z = 0.1 pu
        r_pu = 0.015
        x_pu = math.sqrt(z_pu**2 - r_pu**2)

        # Power factor angle
        cos_phi = power_factor
        sin_phi = math.sqrt(1 - cos_phi**2)

        # Regulation formula (approximate)
        regulation = load_fraction * (r_pu * cos_phi + x_pu * sin_phi) * 100

        return regulation

    @staticmethod
    def calculate_efficiency(core_loss, copper_loss_full, load_fraction, power_factor, rating_kva):
        """
        Calculate efficiency at given load

        Args:
            core_loss: Core loss in kW
            copper_loss_full: Full load copper loss in kW
            load_fraction: Load fraction (0-1)
            power_factor: Power factor
            rating_kva: Transformer rating in kVA

        Returns:
            float: Efficiency (decimal)
        """
        output_kw = rating_kva * load_fraction * power_factor
        copper_loss = copper_loss_full * (load_fraction ** 2)
        total_loss = core_loss + copper_loss
        input_kw = output_kw + total_loss

        if input_kw == 0:
            return 0

        efficiency = output_kw / input_kw
        return efficiency


class ODESolver:
    """ODE Solvers for dynamic simulation"""

    @staticmethod
    def euler_step(f, t, y, dt):
        """
        Euler method step

        Args:
            f: Function dy/dt = f(t, y)
            t: Current time
            y: Current state
            dt: Time step

        Returns:
            tuple: (t_new, y_new)
        """
        y_new = y + dt * f(t, y)
        return t + dt, y_new

    @staticmethod
    def rk45_step(f, t, y, dt):
        """
        Runge-Kutta 4th order (RK4) step - simplified version of RK45

        Args:
            f: Function dy/dt = f(t, y)
            t: Current time
            y: Current state
            dt: Time step

        Returns:
            tuple: (t_new, y_new)
        """
        k1 = f(t, y)
        k2 = f(t + dt/2, y + dt*k1/2)
        k3 = f(t + dt/2, y + dt*k2/2)
        k4 = f(t + dt, y + dt*k3)

        y_new = y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
        return t + dt, y_new


class TransformerDynamicModel:
    """Dynamic transformer model with transient behavior"""

    def __init__(self, rating_kva, v1_rated, v2_rated, frequency,
                 core_loss, copper_loss_full, impedance_percent):
        self.rating_kva = rating_kva
        self.v1_rated = v1_rated
        self.v2_rated = v2_rated
        self.frequency = frequency
        self.core_loss = core_loss
        self.copper_loss_full = copper_loss_full
        self.impedance_percent = impedance_percent

        # Calculate transformer parameters
        self.omega = 2 * math.pi * frequency
        self.i_rated = rating_kva * 1000 / v2_rated

        # Equivalent circuit parameters (per phase)
        z_pu = impedance_percent / 100
        z_base = v2_rated**2 / (rating_kva * 1000)
        self.r_eq = 0.015 * z_base  # Equivalent resistance
        self.l_eq = math.sqrt((z_pu * z_base)**2 - self.r_eq**2) / self.omega  # Equivalent inductance

        # State variables: [flux, current, voltage]
        self.state = np.array([0.0, 0.0, 0.0])
        self.time = 0.0

    def differential_equation(self, t, state):
        """
        Transformer differential equations

        State variables:
        - state[0]: Flux linkage (Wb)
        - state[1]: Secondary current (A)
        - state[2]: Secondary voltage (V)

        Returns:
            np.array: State derivatives
        """
        flux, current, v_sec = state

        # Primary voltage (sinusoidal)
        v_prim = self.v1_rated * math.sqrt(2) * math.sin(self.omega * t)

        # Transformer turns ratio
        a = self.v1_rated / self.v2_rated

        # Reflected primary voltage
        v_reflected = v_prim / a

        # Load impedance (variable based on time for simulation)
        z_load = self.v2_rated / (self.i_rated * (0.5 + 0.5 * math.sin(0.5 * t)))

        # Differential equations
        # dFlux/dt = v_reflected - i*R_eq
        d_flux = v_reflected - current * self.r_eq

        # di/dt = (Flux - L_eq * i - v_sec) / L_eq
        d_current = (flux - self.l_eq * current - v_sec) / (self.l_eq + 1e-9)

        # dv_sec/dt = (current * z_load - v_sec) / (C_load)
        # Simplified: voltage follows current with some lag
        tau_load = 0.01  # Time constant
        d_v_sec = (current * z_load - v_sec) / tau_load

        return np.array([d_flux, d_current, d_v_sec])

    def step(self, dt, method='rk45'):
        """
        Advance simulation by one time step

        Args:
            dt: Time step
            method: 'euler' or 'rk45'
        """
        if method == 'euler':
            self.time, self.state = ODESolver.euler_step(
                self.differential_equation, self.time, self.state, dt
            )
        else:  # rk45
            self.time, self.state = ODESolver.rk45_step(
                self.differential_equation, self.time, self.state, dt
            )

    def get_instantaneous_values(self):
        """Get current instantaneous values"""
        return {
            'time': self.time,
            'flux': self.state[0],
            'current': self.state[1],
            'voltage': self.state[2],
            'power': self.state[1] * self.state[2]
        }

    def reset(self):
        """Reset simulation"""
        self.state = np.array([0.0, 0.0, 0.0])
        self.time = 0.0


class TransformerApp:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Transformer Analysis & Simulation Tool")
        self.root.geometry("1400x900")

        # Simulation control
        self.is_running = False
        self.simulation_speed = 1.0
        self.solver_method = 'rk45'

        # Data storage
        self.time_data = []
        self.current_data = []
        self.voltage_data = []
        self.power_data = []
        self.flux_data = []

        # Default transformer parameters
        self.default_params = {
            'rating_kva': 500,
            'v1_rated': 3300,
            'v2_rated': 500,
            'frequency': 50,
            'max_efficiency': 0.97,
            'load_at_max_eff': 0.75,
            'impedance_percent': 10,
            'power_factor': 0.8
        }

        # Calculate losses
        core_loss, copper_loss_full = TransformerCalculator.calculate_losses(
            self.default_params['rating_kva'],
            self.default_params['max_efficiency'],
            self.default_params['load_at_max_eff']
        )

        # Initialize transformer model
        self.transformer_model = TransformerDynamicModel(
            rating_kva=self.default_params['rating_kva'],
            v1_rated=self.default_params['v1_rated'],
            v2_rated=self.default_params['v2_rated'],
            frequency=self.default_params['frequency'],
            core_loss=core_loss,
            copper_loss_full=copper_loss_full,
            impedance_percent=self.default_params['impedance_percent']
        )

        # Setup GUI
        self.setup_ui()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Calculate initial values
        self.calculate_steady_state()

        # Animation timer
        self.animation_id = None

    def setup_ui(self):
        """Setup user interface"""
        # Create main container with grid
        self.main_container = tk.Frame(self.root, bg='#2b2b2b')
        self.main_container.grid(row=0, column=0, sticky='nsew')

        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure main container grid
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Top menu bar
        self.create_menu_bar()

        # Left panel - Controls
        self.create_control_panel()

        # Right panel - Visualization
        self.create_visualization_panel()

        # Bottom panel - Results
        self.create_results_panel()

    def create_menu_bar(self):
        """Create top menu bar"""
        menu_frame = tk.Frame(self.main_container, bg='#1e1e1e', height=40)
        menu_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
        menu_frame.grid_propagate(False)

        title_label = tk.Label(
            menu_frame,
            text="⚡ Advanced Transformer Analysis Tool",
            font=('Arial', 16, 'bold'),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        title_label.pack(side='left', padx=20, pady=5)

        # Solver method selector
        solver_label = tk.Label(
            menu_frame,
            text="ODE Solver:",
            font=('Arial', 10),
            bg='#1e1e1e',
            fg='white'
        )
        solver_label.pack(side='right', padx=5)

        self.solver_var = tk.StringVar(value='rk45')
        solver_combo = ttk.Combobox(
            menu_frame,
            textvariable=self.solver_var,
            values=['rk45', 'euler'],
            state='readonly',
            width=10
        )
        solver_combo.pack(side='right', padx=5)
        solver_combo.bind('<<ComboboxSelected>>', self.on_solver_change)

    def create_control_panel(self):
        """Create left control panel"""
        control_frame = tk.Frame(self.main_container, bg='#2b2b2b', width=400)
        control_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        control_frame.grid_propagate(False)

        # Configure grid
        control_frame.grid_rowconfigure(1, weight=1)

        # Title
        title = tk.Label(
            control_frame,
            text="Control Panel",
            font=('Arial', 14, 'bold'),
            bg='#2b2b2b',
            fg='#00ff00'
        )
        title.grid(row=0, column=0, pady=10, sticky='w', padx=10)

        # Scrollable frame for parameters
        canvas = tk.Canvas(control_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky='nsew', padx=5)
        scrollbar.grid(row=1, column=1, sticky='ns')

        # Parameter sliders
        self.sliders = {}
        parameters = [
            ('Rating (kVA)', 'rating_kva', 100, 2000, 500),
            ('Primary Voltage (V)', 'v1_rated', 1000, 10000, 3300),
            ('Secondary Voltage (V)', 'v2_rated', 100, 1000, 500),
            ('Frequency (Hz)', 'frequency', 25, 100, 50),
            ('Max Efficiency (%)', 'max_efficiency', 90, 99, 97),
            ('Load at Max Eff (%)', 'load_at_max_eff', 50, 100, 75),
            ('Impedance (%)', 'impedance_percent', 1, 20, 10),
            ('Power Factor', 'power_factor', 0.5, 1.0, 0.8),
            ('Simulation Speed', 'sim_speed', 0.1, 5.0, 1.0)
        ]

        for idx, (label, key, min_val, max_val, default) in enumerate(parameters):
            self.create_slider(scrollable_frame, label, key, min_val, max_val, default, idx)

        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#2b2b2b')
        button_frame.grid(row=2, column=0, columnspan=2, pady=20, padx=10, sticky='ew')

        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start",
            command=self.start_simulation,
            bg='#00aa00',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=3
        )
        self.start_btn.pack(side='left', expand=True, fill='x', padx=5)

        self.stop_btn = tk.Button(
            button_frame,
            text="⏸ Stop",
            command=self.stop_simulation,
            bg='#aa0000',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=3,
            state='disabled'
        )
        self.stop_btn.pack(side='left', expand=True, fill='x', padx=5)

        self.reset_btn = tk.Button(
            button_frame,
            text="⟲ Reset",
            command=self.reset_simulation,
            bg='#0066aa',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=3
        )
        self.reset_btn.pack(side='left', expand=True, fill='x', padx=5)

    def create_slider(self, parent, label, key, min_val, max_val, default, row):
        """Create a parameter slider"""
        frame = tk.Frame(parent, bg='#2b2b2b')
        frame.grid(row=row, column=0, sticky='ew', pady=5, padx=10)

        # Label
        lbl = tk.Label(
            frame,
            text=label,
            font=('Arial', 10),
            bg='#2b2b2b',
            fg='white',
            anchor='w'
        )
        lbl.pack(fill='x')

        # Value display
        value_var = tk.StringVar(value=f"{default:.2f}")
        value_label = tk.Label(
            frame,
            textvariable=value_var,
            font=('Arial', 9, 'bold'),
            bg='#1e1e1e',
            fg='#00ff00',
            width=10,
            relief='sunken'
        )
        value_label.pack(side='right', padx=5)

        # Slider
        slider = tk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            resolution=(max_val - min_val) / 100,
            orient='horizontal',
            bg='#3b3b3b',
            fg='white',
            highlightbackground='#2b2b2b',
            troughcolor='#1e1e1e',
            activebackground='#00aa00',
            showvalue=False,
            command=lambda val, k=key, vv=value_var: self.on_slider_change(k, val, vv)
        )
        slider.set(default)
        slider.pack(fill='x', expand=True)

        self.sliders[key] = {'slider': slider, 'value_var': value_var}

    def create_visualization_panel(self):
        """Create right visualization panel"""
        viz_frame = tk.Frame(self.main_container, bg='#2b2b2b')
        viz_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        # Configure grid
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8), facecolor='#2b2b2b')

        # Create subplots
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        self.ax3 = self.fig.add_subplot(3, 1, 3)

        # Style subplots
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('#00ff00')
            ax.grid(True, alpha=0.3, color='gray')

        self.ax1.set_title('Current vs Time', fontweight='bold')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (A)')

        self.ax2.set_title('Voltage vs Time', fontweight='bold')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Voltage (V)')

        self.ax3.set_title('Power vs Time', fontweight='bold')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.set_ylabel('Power (W)')

        self.fig.tight_layout()

        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

    def create_results_panel(self):
        """Create bottom results panel"""
        results_frame = tk.Frame(self.main_container, bg='#1e1e1e', height=150)
        results_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        results_frame.grid_propagate(False)

        title = tk.Label(
            results_frame,
            text="Steady-State Analysis Results",
            font=('Arial', 12, 'bold'),
            bg='#1e1e1e',
            fg='#00ff00'
        )
        title.pack(pady=5)

        # Results grid
        results_grid = tk.Frame(results_frame, bg='#1e1e1e')
        results_grid.pack(fill='both', expand=True, padx=10, pady=5)

        # Configure grid columns
        for i in range(4):
            results_grid.grid_columnconfigure(i, weight=1)

        self.result_labels = {}
        results = [
            ('Core Loss (kW)', 'core_loss'),
            ('Copper Loss FL (kW)', 'copper_loss'),
            ('Efficiency FL (%)', 'efficiency'),
            ('Regulation FL (%)', 'regulation'),
            ('Max Current (A)', 'max_current'),
            ('Max Voltage (V)', 'max_voltage'),
            ('Avg Power (kW)', 'avg_power'),
            ('Simulation Time (s)', 'sim_time')
        ]

        for idx, (label, key) in enumerate(results):
            row = idx // 4
            col = idx % 4

            frame = tk.Frame(results_grid, bg='#2b2b2b', relief='ridge', bd=2)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

            lbl = tk.Label(
                frame,
                text=label,
                font=('Arial', 9),
                bg='#2b2b2b',
                fg='white'
            )
            lbl.pack(pady=2)

            value_label = tk.Label(
                frame,
                text="0.00",
                font=('Arial', 11, 'bold'),
                bg='#2b2b2b',
                fg='#00ff00'
            )
            value_label.pack(pady=2)

            self.result_labels[key] = value_label

    def on_slider_change(self, key, value, value_var):
        """Handle slider value change"""
        value_var.set(f"{float(value):.2f}")

        # Update simulation parameters
        if key == 'sim_speed':
            self.simulation_speed = float(value)
        else:
            # Recalculate steady state
            self.calculate_steady_state()

    def on_solver_change(self, event=None):
        """Handle solver method change"""
        self.solver_method = self.solver_var.get()

    def calculate_steady_state(self):
        """Calculate steady-state parameters"""
        # Get current slider values
        rating_kva = self.sliders['rating_kva']['slider'].get()
        v1_rated = self.sliders['v1_rated']['slider'].get()
        v2_rated = self.sliders['v2_rated']['slider'].get()
        max_eff = self.sliders['max_efficiency']['slider'].get() / 100
        load_at_max_eff = self.sliders['load_at_max_eff']['slider'].get() / 100
        impedance = self.sliders['impedance_percent']['slider'].get()
        pf = self.sliders['power_factor']['slider'].get()

        # Calculate losses
        core_loss, copper_loss_full = TransformerCalculator.calculate_losses(
            rating_kva, max_eff, load_at_max_eff
        )

        # Calculate regulation
        regulation = TransformerCalculator.calculate_regulation(
            v2_rated, impedance, pf, 1.0
        )

        # Calculate full load efficiency
        efficiency_fl = TransformerCalculator.calculate_efficiency(
            core_loss, copper_loss_full, 1.0, pf, rating_kva
        ) * 100

        # Calculate currents
        i_rated = rating_kva * 1000 / v2_rated

        # Update results
        self.result_labels['core_loss'].config(text=f"{core_loss:.2f}")
        self.result_labels['copper_loss'].config(text=f"{copper_loss_full:.2f}")
        self.result_labels['efficiency'].config(text=f"{efficiency_fl:.2f}")
        self.result_labels['regulation'].config(text=f"{regulation:.2f}")
        self.result_labels['max_current'].config(text=f"{i_rated:.2f}")
        self.result_labels['max_voltage'].config(text=f"{v2_rated:.2f}")

        # Update transformer model
        frequency = self.sliders['frequency']['slider'].get()
        self.transformer_model = TransformerDynamicModel(
            rating_kva=rating_kva,
            v1_rated=v1_rated,
            v2_rated=v2_rated,
            frequency=frequency,
            core_loss=core_loss,
            copper_loss_full=copper_loss_full,
            impedance_percent=impedance
        )

    def start_simulation(self):
        """Start dynamic simulation"""
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.animate()

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        if self.animation_id:
            self.root.after_cancel(self.animation_id)

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()

        # Reset transformer model
        self.transformer_model.reset()

        # Clear data
        self.time_data = []
        self.current_data = []
        self.voltage_data = []
        self.power_data = []
        self.flux_data = []

        # Clear plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Reset plot styles
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('#00ff00')
            ax.grid(True, alpha=0.3, color='gray')

        self.ax1.set_title('Current vs Time', fontweight='bold')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (A)')

        self.ax2.set_title('Voltage vs Time', fontweight='bold')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Voltage (V)')

        self.ax3.set_title('Power vs Time', fontweight='bold')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.set_ylabel('Power (W)')

        self.canvas.draw()

        # Reset results
        self.result_labels['avg_power'].config(text="0.00")
        self.result_labels['sim_time'].config(text="0.00")

        # Recalculate steady state
        self.calculate_steady_state()

    def animate(self):
        """Animation loop for simulation"""
        if not self.is_running:
            return

        # Time step
        dt = 0.001 * self.simulation_speed  # 1 ms per step, scaled by speed

        # Run multiple steps for smoother animation
        steps_per_frame = max(1, int(10 * self.simulation_speed))

        for _ in range(steps_per_frame):
            self.transformer_model.step(dt, method=self.solver_method)

        # Get values
        values = self.transformer_model.get_instantaneous_values()

        # Store data
        self.time_data.append(values['time'])
        self.current_data.append(values['current'])
        self.voltage_data.append(values['voltage'])
        self.power_data.append(values['power'])

        # Limit data points
        max_points = 1000
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.current_data = self.current_data[-max_points:]
            self.voltage_data = self.voltage_data[-max_points:]
            self.power_data = self.power_data[-max_points:]

        # Update plots every 10 frames
        if len(self.time_data) % 10 == 0:
            self.update_plots()

        # Update results
        if len(self.power_data) > 0:
            avg_power = np.mean(np.abs(self.power_data[-100:])) / 1000  # kW
            self.result_labels['avg_power'].config(text=f"{avg_power:.2f}")
        self.result_labels['sim_time'].config(text=f"{values['time']:.3f}")

        # Schedule next frame
        self.animation_id = self.root.after(50, self.animate)  # 50 ms = 20 FPS

    def update_plots(self):
        """Update visualization plots"""
        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Plot data
        if len(self.time_data) > 0:
            self.ax1.plot(self.time_data, self.current_data, 'cyan', linewidth=1.5)
            self.ax2.plot(self.time_data, self.voltage_data, 'lime', linewidth=1.5)
            self.ax3.plot(self.time_data, self.power_data, 'yellow', linewidth=1.5)

        # Restore plot styles
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('#00ff00')
            ax.grid(True, alpha=0.3, color='gray')

        self.ax1.set_title('Current vs Time', fontweight='bold')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (A)')

        self.ax2.set_title('Voltage vs Time', fontweight='bold')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Voltage (V)')

        self.ax3.set_title('Power vs Time', fontweight='bold')
        self.ax3.set_xlabel('Time (s)')
        self.ax3.set_ylabel('Power (W)')

        # Auto-scale
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.relim()
            ax.autoscale_view()

        self.fig.tight_layout()
        self.canvas.draw()

    def on_window_resize(self, event):
        """Handle window resize event"""
        if event.widget == self.root:
            # Redraw canvas with new size
            try:
                self.fig.tight_layout()
                self.canvas.draw()
            except:
                pass


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TransformerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
