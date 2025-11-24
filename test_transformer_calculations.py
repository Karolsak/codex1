"""
Test script for transformer calculations
Solves the given problem:
- 500 kVA, 3300/500 V, 50 Hz, single phase transformer
- Maximum efficiency 97% at 75% full-load, unity power factor
- Impedance 10%
- Calculate regulation at full-load, power factor 0.8 lagging
"""

from transformer_core import TransformerCalculator

# Given parameters
rating_kva = 500
v1_rated = 3300
v2_rated = 500
frequency = 50
max_efficiency = 0.97
load_at_max_eff = 0.75
impedance_percent = 10
power_factor = 0.8

print("=" * 60)
print("TRANSFORMER ANALYSIS - PROBLEM SOLUTION")
print("=" * 60)
print("\nGiven Parameters:")
print(f"  Rating: {rating_kva} kVA")
print(f"  Primary Voltage: {v1_rated} V")
print(f"  Secondary Voltage: {v2_rated} V")
print(f"  Frequency: {frequency} Hz")
print(f"  Maximum Efficiency: {max_efficiency * 100}%")
print(f"  Load at Max Efficiency: {load_at_max_eff * 100}% of full load")
print(f"  Impedance: {impedance_percent}%")
print(f"  Full Load Power Factor: {power_factor} lagging")

# Calculate losses
print("\n" + "-" * 60)
print("STEP 1: Calculate Core and Copper Losses")
print("-" * 60)

core_loss, copper_loss_full = TransformerCalculator.calculate_losses(
    rating_kva, max_efficiency, load_at_max_eff
)

print(f"\nCore Loss (constant): {core_loss:.3f} kW")
print(f"Full Load Copper Loss: {copper_loss_full:.3f} kW")

# Calculate regulation
print("\n" + "-" * 60)
print("STEP 2: Calculate Voltage Regulation at Full Load")
print("-" * 60)

regulation = TransformerCalculator.calculate_regulation(
    v2_rated, impedance_percent, power_factor, 1.0
)

print(f"\nVoltage Regulation at Full Load (0.8 pf lagging): {regulation:.3f}%")

# Calculate full load efficiency
print("\n" + "-" * 60)
print("STEP 3: Calculate Full Load Efficiency")
print("-" * 60)

efficiency_fl = TransformerCalculator.calculate_efficiency(
    core_loss, copper_loss_full, 1.0, power_factor, rating_kva
)

print(f"\nFull Load Efficiency (0.8 pf): {efficiency_fl * 100:.3f}%")

# Verify maximum efficiency
print("\n" + "-" * 60)
print("STEP 4: Verify Maximum Efficiency")
print("-" * 60)

efficiency_at_75 = TransformerCalculator.calculate_efficiency(
    core_loss, copper_loss_full, load_at_max_eff, 1.0, rating_kva
)

print(f"\nEfficiency at 75% load (unity pf): {efficiency_at_75 * 100:.3f}%")
print(f"Given maximum efficiency: {max_efficiency * 100}%")
print(f"Difference: {abs(efficiency_at_75 - max_efficiency) * 100:.4f}%")

# Additional calculations
print("\n" + "-" * 60)
print("ADDITIONAL INFORMATION")
print("-" * 60)

# Rated current
i_rated_secondary = (rating_kva * 1000) / v2_rated
i_rated_primary = (rating_kva * 1000) / v1_rated

print(f"\nRated Secondary Current: {i_rated_secondary:.2f} A")
print(f"Rated Primary Current: {i_rated_primary:.2f} A")

# Total losses at full load
total_loss_fl = core_loss + copper_loss_full
print(f"\nTotal Losses at Full Load: {total_loss_fl:.3f} kW")

# Load kW at full load
load_kw_fl = rating_kva * power_factor
input_kw_fl = load_kw_fl + total_loss_fl

print(f"Output Power at Full Load: {load_kw_fl:.2f} kW")
print(f"Input Power at Full Load: {input_kw_fl:.2f} kW")

print("\n" + "=" * 60)
print("FINAL ANSWERS")
print("=" * 60)
print(f"\n1. Core Loss: {core_loss:.3f} kW")
print(f"2. Full Load Copper Loss: {copper_loss_full:.3f} kW")
print(f"3. Voltage Regulation at Full Load (0.8 pf lagging): {regulation:.3f}%")
print(f"4. Full Load Efficiency (0.8 pf): {efficiency_fl * 100:.3f}%")
print("\n" + "=" * 60)
