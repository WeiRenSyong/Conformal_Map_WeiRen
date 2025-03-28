# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize as opt
from scipy.interpolate import interp1d
# %% Define Some Useful Functions
######################################
#### Input:                       ####
#### (Column 1: Time)             ####
#### Column 1: Frequency in Hz    ####
#### Column 2: Magnitude in dB    ####
#### Column 3: Phase in degrees   ####
######################################
#### Output:                      ####
#### Column 1 : freq_Hz           ####
#### Column 2 : complex S21       ####
######################################
print(f"Define Organize_Date function...")
def Organize_Data(raw_data):
    # Ensure the input is a NumPy array
    raw_data = np.array(raw_data, dtype=str)

    # Check if the raw_data has an extra time column (4 columns instead of 3)
    if raw_data.shape[1] == 3:
        print('The raw data are Nx3 matrix.')
    elif raw_data.shape[1] == 4:
        print('The raw data are Nx4 matrix.')
        raw_data = raw_data[:, 1:]  # Ignore the first column (time column)
    else:
        print('Please check the raw data due to worng format.')
    
    # Convert each column to numeric values, removing non-numeric rows
    freq, mag, phase = [], [], []
    for column in raw_data:
        try:
            f = float(column[0])
            m = float(column[1])
            p = float(column[2])
            freq.append(f)
            mag.append(m)
            phase.append(p)
        except ValueError:
            continue  # Skip rows with non-numeric entries
    freq = np.array(freq)
    mag = np.array(mag)
    phase = np.array(phase)

    # Convert frequency to Hz if given in GHz
    if np.max(freq) < 1e9:  # Assuming min frequency is 1 GHz
        freq_Hz = freq * 1e9
    else:
        freq_Hz = freq

    # Convert magnitude from dB to linear scale
    if np.min(mag) < 0: # If min mag < 0, assume dB
        mag_lin = 10 ** (mag / 20)   # The reading of the VNA is a ratio of voltage, so 20 is here
    else:
        mag_lin = mag

    # Convert phase to radians if in degrees
    if np.max(np.abs(phase)) > 2 * np.pi:  # If max phase > 2π, assume degrees
        phase_rad = np.deg2rad(phase)
    else:
        phase_rad = phase

    S21 = mag_lin * np.exp(1j * phase_rad)

    # Stack the processed data
    organized_data = np.column_stack((freq_Hz, S21))

    return organized_data

# %% (1) Cable Delay Removed - fit_cable_delay, fit_alpha
#######################################
#### Input:                        ####
#### para 1 : organized_data       ####
#######################################
#### Output:                       ####
#### para 1 : cable_delay(tau)     ####
#### para 2 : phase offset (alpha) ####
#######################################
print(f"Define fit_cable_delay function...")
def fit_cable_delay(organized_data):
    # Extract values for plotting
    freq_Hz = organized_data[:, 0]
    mag_lin = organized_data[:, 1]
    phase_rad = organized_data[:, 2]

    # Unwrap phase to prevent discontinuities
    phase_rad = np.unwrap(phase_rad)  

    # Select the wings first and last few points
    num_points = 2  # Number of points to use from each wing
    freq_bg = np. concatenate((freq_Hz[:num_points], freq_Hz[-num_points:]))
    phase_bg = np.concatenate((phase_rad[:num_points], phase_rad[-num_points:]))

    # Perform linear fit to get A(slope) and B (offset)
    minus_two_pi_tau, alpha = np.polyfit(freq_bg, phase_bg, 1)    # Linear fit (degree = 1)

    tau = minus_two_pi_tau / (-2 * np.pi)
    print(f"cable_delay (tau) is {tau * 1e9:.2f} ns")
    print(f"phase offset (alpha) is {np.rad2deg(alpha):.2f} deg")

    return tau, alpha

#######################################
#### Input:                        ####
#### para 1 : organized_data       ####
#### para 2 : cable_delay(tau)     ####
#### para 3 : phase offset (alpha) ####
#######################################
#### Output:                       ####
#### reorganized_data              ####
#######################################
print(f"Define remove_cable_delay function...")
def remove_cable_delay(organized_data, tau, alpha):
    print(f"Preprocess the phase correction...")
    # Extract values for plotting
    freq_Hz = organized_data[:, 0]
    mag_lin = organized_data[:, 1]
    phase_rad = organized_data[:, 2]

    # Compute the background phase caused by cable delay
    phase_bg = -2 * np.pi * freq_Hz * tau + alpha # in rad

    z = mag_lin * np.exp(1j * phase_rad)
    # Remove the background phase
    z_corrected = z * np.exp(-1j * phase_bg)  # Multiply by exp(+j*phase) to correct

    # Arrange z_corrected     
    freq_Hz = freq_Hz
    mag_lin = np.abs(z_corrected)
    phase_rad = np.angle(z_corrected)

    # Stack the processed data
    reorganized_data = np.column_stack((freq_Hz, mag_lin, phase_rad))

    return reorganized_data

# %% (2) Centerd Data (z1)



# %% (3) Normalized Data (z2)
##########################################
#### Input:                           ####
#### para 1 : organized_data          ####
##########################################
#### Output:                          ####
#### reorganized_data: bg_mag_removal ####
##########################################
print(f"Define remove_mag_bg function...")
def remove_mag_bg(organized_data):
    print(f"Preprocess the background mag removal...")
    # Extract values for plotting
    freq_Hz = organized_data[:, 0]
    mag_lin = organized_data[:, 1]
    phase_rad = organized_data[:, 2]

    # Select the wings first and last few points
    num_points = 2  # Number of points to use from each wing
    freq_bg = np. concatenate((freq_Hz[:num_points], freq_Hz[-num_points:]))
    mag_bg = np.concatenate((mag_lin[:num_points], mag_lin[-num_points:]))

    # Perform linear fit to get A(slope) and B (offset)
    q = np.polyfit(freq_bg, mag_bg, 1)    # Linear fit (degree = 1)

    # Define the background to substrate (Ax + B)
    mag_bg = np.polyval(q, freq_Hz)

    z = mag_lin * np.exp(1j * phase_rad)
    # Remove the background mag
    z_corrected = z / mag_bg

    # Arrange z_corrected     
    freq_Hz = freq_Hz
    mag_lin = np.abs(z_corrected)
    phase_rad = np.angle(z_corrected)

    # Stack the processed data
    reorganized_data = np.column_stack((freq_Hz, mag_lin, phase_rad))

    return reorganized_data

# %% (4) Inverted Data (w)






# %% (5) Rotated, Inverted Data (w1)







# %% (6) Conformally Mapped Data (w2)





















































# %% Initial Guessing


# %% Set a Testing Point - Check if the initial guessings (fc, phi, Q, Qc) are found succuessfully.
##############################################
#### Use to be a Test Point               ####
#### 1. find resonance frequecny (fc)     ####
#### 2. find phase mismatch (phi)         ####
#### 3. find loaded quality factor (Q)    ####
#### 4. find coupling quality factor (Qc) ####
##############################################
# Define folder path and file name separately
folder_path = r"C:\Users\user\Documents\GitHub\Cooldown_56_Line_5-NW_Ta2O5_15nm_01\2024_10_18_Final_Organized_Data\All_csv_raw_data_and_fitting_results\Resonator_3_5p892GHz"
file_name = r"NW_Ta2O5_15nm_01_5p892GHz_-72dBm_-1000mK.csv"

# Combine folder path and file name
file_path = os.path.join(folder_path, file_name)

# Load data
raw_data = pd.read_csv(file_path)

# Print confirmation
print(f"In the folder: {folder_path}")
print(f"Load data from: {file_name}")

organized_data = Organize_Data(raw_data)
tau, alpha = fit_cable_delay(organized_data)
remove_cable_delay_data = remove_cable_delay(organized_data, tau, alpha)
reorganized_data = remove_mag_bg(remove_cable_delay_data)
Plot_Data(reorganized_data)

guess_fc = find_fc(reorganized_data)
guess_phi = find_phi(reorganized_data)
guess_Q = find_Q(reorganized_data, plot=False)
guess_Qc = find_Qc(reorganized_data)
print(f"Initial guess Q: {guess_Q/1e6:.4f} × 10\u2076")
print(f"The infered internal quality factor (Qi): {(1 / guess_Q - 1 / guess_Qc) **(-1) / 1e6:.4f} x 10\u2076")
print(f"Initial guess |Qc|: {guess_Qc/1e6:.4f} x 10\u2076")
print(f"Initial guess phi: {np.rad2deg(-guess_phi):.4f} deg")
print(f"Initial guess fc: {guess_fc / 1e9:.9f} GHz")
  
# %% Doing the Monte Carlo to Adjust the Fit Parameters
guess_fc = find_fc(reorganized_data)
guess_Qc = find_Qc(reorganized_data)
guess_Q = find_Q(reorganized_data, plot=False)
guess_phi = find_phi(reorganized_data)

freq_Hz = reorganized_data[:, 0]
mag_lin = reorganized_data[:, 1]
phase_rad = reorganized_data[:, 2]
S21_data = mag_lin * np.exp(1j * phase_rad)

# Define Theoretical S21 Model
def S21_model(freq, fc, phi, Q, Qc):
    return 1 - (Q / Qc) * np.exp(1j * phi) / (1 + 2j * Q * (freq / fc - 1))

def Monte_Carlo_fit_complex_circle(freq, S21_data, guess_fc, guess_phi, guess_Q, guess_Qc, num_samples=10):
    
    test_S21_data = S21_model(freq, guess_fc, guess_phi, guess_Q, guess_Qc)
    best_cost = np.sum(np.abs(S21_data - test_S21_data) ** 2)

    best_Qc, best_Q, best_phi, best_fc = guess_Qc, guess_Q, guess_phi, guess_fc

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(10, 5))
    ax1, ax2, ax3, ax4 = axes.flatten()

    # Labels for axes
    ax1.set_title("Qc Evolution")
    ax2.set_title("Q Evolution")
    ax3.set_title("phi Evolution")
    ax4.set_title("fc Evolution")

    for i in range(num_samples):
        # Propose new parameter values
        param_Qc = np.random.normal(best_Qc, 5e4)
        param_Q = np.random.normal(best_Q, 1e4)
        param_phi = np.random.normal(best_phi, 0.002)
        param_fc = np.random.normal(best_fc, 10)

        # Evaluate cost for new parameter set
        test_S21_data = S21_model(freq, param_fc, param_phi, param_Q, param_Qc)
        cost_S21_data = np.sum(np.abs(S21_data - test_S21_data) ** 2)

        # Accept if cost is lower
        if cost_S21_data < best_cost:
            best_cost = cost_S21_data
            best_Qc, best_Q, best_phi, best_fc = param_Qc, param_Q, param_phi, param_fc

        # Scatter plot updates
        ax1.scatter(i, best_Qc, color='black', s=50, marker='o', alpha=0.7)
        ax2.scatter(i, best_Q, color='red', s=50, marker='o', alpha=0.7)
        ax3.scatter(i, best_phi, color='green', s=50, marker='o', alpha=0.7)
        ax4.scatter(i, best_fc, color='blue', s=50, marker='o', alpha=0.7)

    plt.tight_layout()
    plt.show()

    return best_fc, best_phi, best_Q, best_Qc

best_fc, best_phi, best_Q, best_Qc = Monte_Carlo_fit_complex_circle(freq_Hz, S21_data, guess_fc, guess_phi, guess_Q, guess_Qc, num_samples=500)

print(f"Final Q: {best_Q/1e6:.4f} × 10\u2076")
print(f"The infered internal quality factor (Qi): {(1 / best_Q - 1 / best_Qc) **(-1) / 1e6:.4f} x 10\u2076")
print(f"Final guess |Qc|: {best_Qc/1e6:.4f} x 10\u2076")
print(f"Final guess phi: {np.rad2deg(-best_phi):.4f} deg")
print(f"Final guess fc: {best_fc / 1e9:.9f} GHz")

# %% Function to plot final results
def Plot_Final_Fit_Data(organized_data, fc, phi, Q, Qc):
    freq_Hz = organized_data[:, 0]  
    mag_lin = organized_data[:, 1] 
    phase_rad = organized_data[:, 2] 

    S21 = mag_lin * np.exp(1j * phase_rad)
    S21_real = np.real(S21)
    S21_imag = np.imag(S21)

    freq_GHz = freq_Hz / 1e9
    mag_dB = 20 * np.log10(mag_lin) 
    phase_deg = np.rad2deg(phase_rad)

    # Use the S21 model for the final fit
    S21_final_fit = S21_model(freq_Hz, fc, phi, Q, Qc)
    mag_lin_final_fit = np.abs(S21_final_fit)
    mag_dB_final_fit = 20 * np.log10(mag_lin_final_fit)
    phase_deg_final_fit = np.rad2deg(np.angle(S21_final_fit))
    S21_real_final_fit = np.real(S21_final_fit)
    S21_imag_final_fit = np.imag(S21_final_fit)
    
    fc_GHz = fc / 1e9
    
    # Find the closest frequency point to fc
    closest_index = np.argmin(np.abs(freq_Hz - fc))
    mag_dB_fc_final_fit = mag_dB[closest_index]
    phase_deg_fc_final_fit = phase_deg[closest_index]
    z_fc_final_fit = S21_real[closest_index] + 1j * S21_imag[closest_index]

    # Create figure
    fig = plt.figure(figsize=(10, 5))

    # Plot Frequency vs Magnitude (dB)
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.scatter(freq_GHz, mag_dB, color='blue', s=50, marker='o', label="Measured Mag", alpha=1)
    ax1.scatter(fc_GHz, mag_dB_fc_final_fit, color='red', s=500, marker='*', zorder=5, label="Resonance")
    ax1.plot(freq_GHz, mag_dB_final_fit, label="Fitted Mag", color="green")
    ax1.set_xlabel("Freq (GHz)")
    ax1.set_ylabel("Mag (dB)")
    ax1.set_title("Freq vs Mag")
    ax1.grid(True)
    ax1.legend()
    
    # Plot Frequency vs Phase (degrees)
    ax2 = fig.add_subplot(2, 2, 3)
    ax2.scatter(freq_GHz, phase_deg, color='orange', s=50, marker='o', label="Measured Phase", alpha=1)
    ax2.scatter(fc_GHz, phase_deg_fc_final_fit, color='red', s=500, marker='*', zorder=5, label="Resonance")
    ax2.plot(freq_GHz, phase_deg_final_fit, label="Fitted Phase", color="green")
    ax2.set_xlabel("Freq (GHz)")
    ax2.set_ylabel("Phase (deg)")
    ax2.set_title("Freq vs Phase")
    ax2.grid(True)
    ax2.legend()

    # Plot Real(S21) vs Imag(S21)
    ax3 = fig.add_subplot(1, 2, 2)
    ax3.scatter(S21_real, S21_imag, color='green', s=50, marker='o', label="Measured Data", alpha=1)
    ax3.scatter(np.real(z_fc_final_fit), np.imag(z_fc_final_fit), color='red', s=500, marker='*', zorder=5, label="Resonance")
    ax3.plot(S21_real_final_fit, S21_imag_final_fit, label="Fitted Circle", color="green")
    ax3.axvline(x=1, color='black', linestyle='--', label=None)
    ax3.axhline(y=0, color='black', linestyle='--', label=None)
    ax3.plot([np.real(z_fc_final_fit), 1], [np.imag(z_fc_final_fit), 0], color='red', linestyle='-', linewidth=2, label=None)
    ax3.set_xlabel("Real(S21)")
    ax3.set_ylabel("Imag(S21)")
    ax3.set_title("S21 Complex Plane")
    ax3.grid(True)
    ax3.legend()

    plt.tight_layout()
    plt.show()

Plot_Final_Fit_Data(reorganized_data, best_fc, best_phi, best_Q, best_Qc)