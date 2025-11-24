"""
Core Transformer Calculation Module
No GUI dependencies - pure calculation module
"""

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
    def _list_add(a, b):
        """Add two lists element-wise"""
        return [a[i] + b[i] for i in range(len(a))]

    @staticmethod
    def _list_scale(scalar, lst):
        """Multiply a list by a scalar"""
        return [scalar * x for x in lst]

    @staticmethod
    def euler_step(f, t, y, dt):
        """
        Euler method step

        Args:
            f: Function dy/dt = f(t, y)
            t: Current time
            y: Current state (list)
            dt: Time step

        Returns:
            tuple: (t_new, y_new)
        """
        dy = f(t, y)
        y_new = ODESolver._list_add(y, ODESolver._list_scale(dt, dy))
        return t + dt, y_new

    @staticmethod
    def rk45_step(f, t, y, dt):
        """
        Runge-Kutta 4th order (RK4) step - simplified version of RK45

        Args:
            f: Function dy/dt = f(t, y)
            t: Current time
            y: Current state (list)
            dt: Time step

        Returns:
            tuple: (t_new, y_new)
        """
        k1 = f(t, y)

        y_temp = ODESolver._list_add(y, ODESolver._list_scale(dt/2, k1))
        k2 = f(t + dt/2, y_temp)

        y_temp = ODESolver._list_add(y, ODESolver._list_scale(dt/2, k2))
        k3 = f(t + dt/2, y_temp)

        y_temp = ODESolver._list_add(y, ODESolver._list_scale(dt, k3))
        k4 = f(t + dt, y_temp)

        # Combine: y_new = y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
        k_combined = []
        for i in range(len(k1)):
            k_combined.append(k1[i] + 2*k2[i] + 2*k3[i] + k4[i])

        y_new = ODESolver._list_add(y, ODESolver._list_scale(dt/6, k_combined))
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
        self.state = [0.0, 0.0, 0.0]
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

        return [d_flux, d_current, d_v_sec]

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
        self.state = [0.0, 0.0, 0.0]
        self.time = 0.0


if __name__ == "__main__":
    # Test the calculator
    print("Testing Transformer Calculator Module")
    print("=" * 60)

    rating_kva = 500
    max_eff = 0.97
    load_at_max = 0.75

    core_loss, copper_loss = TransformerCalculator.calculate_losses(
        rating_kva, max_eff, load_at_max
    )

    print(f"Core Loss: {core_loss:.3f} kW")
    print(f"Copper Loss (Full Load): {copper_loss:.3f} kW")

    regulation = TransformerCalculator.calculate_regulation(500, 10, 0.8)
    print(f"Regulation at Full Load (0.8 pf): {regulation:.3f}%")
