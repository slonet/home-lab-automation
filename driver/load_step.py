import serial
import time
import csv
import datetime
import numpy as np
import matplotlib.pyplot as plt

import dcs_psu_driver_serial as dcs
import plz_eload_driver_serial as plz


plz_addr = 1
dcs_addr = 19
dcs_current_lim = 0.1
dcs_meas_avg = 2

vin_min = 0
vin_max = 25
vin_step = 1

iout_low = 0.01
iout_high = 0.06
rise_fall_time = 1 #see PLZ driver (must be integer from 0-7) 
low_pulse_time_sec = 2
high_pulse_time_sec = 0.1
num_steps = 100

csv_file_name = ""

# SUMMARY

# This script performs num_steps load steps between iout_low and iout_high.
# It repeats the steps at each input voltage step as specified by vin_min, vin_max, and vin_step
# The timing of each step is defined by low_pulse_time and high_pulse_time.
# The PLZ hardware trigger output is used to trigger the MSO-X oscilloscope

# Set up instruments 
#
# Initial safe state
#
# Outer loop: Voltage Sweep
#    Inner loop: Current Pulses, Trig output
#
# Final safe state
# 
# Process Data
# Save Data
# Plot Data

# Stretch goal is to automate the MSO-X to capture trace data

def init_instruments():
	dcs.configure_prologix_adapter(dcs_addr)
	dcs.hard_reset_dcs()
	dcs.set_output_current(dcs_current_lim)
	dcs.set_voltage_avg(dcs_meas_avg)
	dcs.set_current_avg(dcs_meas_avg)

	plz.configure_prologix_adapter(plz_addr)
	plz.reset_plz()
	plz.set_load_mode("CC")
	time.sleep(0.1)

def init_arrays():
	num_vin = int((vin_max - vin_min) / vin_step) + 1
	vect_vin = np.linspace(vin_min, vin_max, num = num_vin, endpoint = True)

	vect_steps = np.linspace(0, num_steps - 1, num_steps, endpoint = True) # index at 0

	stim_vectors = {
		"vin": vect_vin
	}

	meas_vectors = {
		"vin_meas": np.zeros((num_vin, num_iout)),
		"iin_meas": np.zeros((num_vin, num_iout)),
		"vout_meas": np.zeros((num_vin, num_iout)),
		"iout_meas": np.zeros((num_vin, num_iout))
	}

	return stim_vectors, meas_vectors

def disable_instruments():
	dcs.configure_prologix_adapter(dcs_addr)
	dcs.soft_reset_dcs()
	dcs.set_output_voltage(0)

	plz.configure_prologix_adapter(plz_addr)
	plz.set_load_current(0)
	plz.set_load_state(0)

def sweep(stim_vectors, meas_vectors):

	#TODO: finish this function