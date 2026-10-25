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

iout_min = 0
iout_max = 0.06
iout_step = 0.01

csv_file_name = ""


# init_instruments() must be run before any other function so the instruments are set up and state cleared
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



# init_arrays() generates the stimulus and measurement arrays
def init_arrays():
	num_vin = int((vin_max - vin_min) / vin_step) + 1 # include start and stop values
	vect_vin = np.linspace(vin_min, vin_max, num = num_vin, endpoint = True)

	num_iout = int((iout_max - iout_min) / iout_step) + 1 # include start and stop values
	vect_iout = np.linspace(iout_min, iout_max, num = num_iout, endpoint = True)

	stim_vectors = {
		"vin": vect_vin,
		"iout": vect_iout
	}

	meas_vectors = {
		"vin_meas": np.zeros((num_vin, num_iout)),
		"iin_meas": np.zeros((num_vin, num_iout)),
		"vout_meas": np.zeros((num_vin, num_iout)),
		"iout_meas": np.zeros((num_vin, num_iout))
	}

	return stim_vectors, meas_vectors


def ps_calcs(meas_vectors):
	calc_vectors = {
		"pin_calc": meas_vectors["vin_meas"] * meas_vectors["iin_meas"],
		"pout_calc": meas_vectors["vout_meas"] * meas_vectors["iout_meas"],
		"eff_calc": (meas_vectors["vout_meas"] * meas_vectors["iout_meas"]) / (meas_vectors["vin_meas"] * meas_vectors["iin_meas"]),
		"heat_calc": (meas_vectors["vin_meas"] * meas_vectors["iin_meas"]) - meas_vectors["vout_meas"] * meas_vectors["iout_meas"]
	}

	return calc_vectors


def disable_instruments():
	dcs.configure_prologix_adapter(dcs_addr)
	dcs.soft_reset_dcs()
	dcs.set_output_voltage(0)

	plz.configure_prologix_adapter(plz_addr)
	plz.set_load_current(0)
	plz.set_load_state(0)


def sweep(stim_vectors, meas_vectors):
	i = 0 # voltage index
	j = 0 # current index

	plz.configure_prologix_adapter(plz_addr)
	plz.set_load_state(1)

	for stim_vin in stim_vectors.get("vin"):
		print(f"###### Vin stimulus = {stim_vin}")
		dcs.configure_prologix_adapter(dcs_addr)
		dcs.soft_reset_dcs()
		dcs.set_output_voltage(stim_vin)

		for stim_iout in stim_vectors.get("iout"):
			print(f"### Iout stimulus = {stim_iout}")
			plz.configure_prologix_adapter(plz_addr)
			plz.set_load_current(stim_iout)
			time.sleep(0.5) # wait 500ms for the measurement to settle

			meas_vectors["vout_meas"][i,j] = plz.get_meas_voltage()
			meas_vectors["iout_meas"][i,j] = plz.get_meas_current()

			dcs.configure_prologix_adapter(dcs_addr) # measure input voltage and current
			dcs.soft_reset_dcs()
			meas_vectors["vin_meas"][i,j] = dcs.get_meas_voltage()
			meas_vectors["iin_meas"][i,j] = dcs.get_meas_current()

			vin = meas_vectors["vin_meas"][i,j]
			iin = meas_vectors["iin_meas"][i,j]
			vout = meas_vectors["vout_meas"][i,j]
			iout = meas_vectors["iout_meas"][i,j]

			print(f"Vin = {vin} Volts")
			print(f"Iin = {iin} Amps")
			print(f"Vout = {vout} Volts")
			print(f"Iout = {iout} Amps")

			j += 1

		j = 0
		i += 1

	return meas_vectors


def plot_meas_3d(stim_vectors, meas_vectors, meas_key,
                 x_key="vin", y_key="iout",
                 plot_type="surface"):
    x = stim_vectors[x_key]
    y = stim_vectors[y_key]
    z = meas_vectors[meas_key]

    X, Y = np.meshgrid(x, y, indexing="ij")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    if plot_type == "surface":
        ax.plot_surface(X, Y, z, cmap="viridis", edgecolor="k", linewidth=0.3)
    elif plot_type == "scatter":
        ax.scatter(X, Y, z, c=z, cmap="viridis")
    else:
        raise ValueError("plot_type must be 'surface' or 'scatter'")

    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)
    ax.set_zlabel(meas_key)
    ax.set_title(f"{meas_key} vs {x_key}, {y_key}")

    plt.tight_layout()
    plt.show()


# plot_vin_vout_2d() plots input voltage (x) vs output voltage (y), one series per output current step
# use_measured=True plots measured Vin on the x-axis; False plots the Vin stimulus values
def plot_vin_vout_2d(stim_vectors, meas_vectors, use_measured=True,
		title="Input Voltage vs. Output Voltage by Load Current",
		save_path=None):
	vect_iout = stim_vectors["iout"]
	num_series = len(vect_iout)

	# distinct color per series (tab10 for up to 10 series, otherwise sample a continuous map)
	if num_series <= 10:
		colors = plt.cm.tab10(np.arange(num_series))
	else:
		colors = plt.cm.turbo(np.linspace(0, 1, num_series))

	fig, ax = plt.subplots(figsize=(12, 6))

	for j, iout in enumerate(vect_iout):
		if use_measured:
			x = meas_vectors["vin_meas"][:, j]
		else:
			x = stim_vectors["vin"]
		y = meas_vectors["vout_meas"][:, j]

		ax.plot(x, y, color=colors[j], marker="o", markersize=5,
			linewidth=1.8, label=f"{iout * 1000:g} mA")

	ax.set_title(title, loc="left", fontsize=16, color="dimgray")
	ax.set_xlabel("Input Voltage (V)")
	ax.set_ylabel("Output Voltage (V)")
	ax.set_xlim(left=min(0, np.min(stim_vectors["vin"])))
	ax.set_ylim(bottom=0)
	ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
	ax.grid(True, color="lightgray")
	ax.set_axisbelow(True)
	for side in ("top", "right"):
		ax.spines[side].set_visible(False)

	# series name table (legend) to the right of the plot
	ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False,
		handlelength=1.2, markerscale=1.6)

	plt.tight_layout()
	if save_path:
		fig.savefig(save_path, dpi=150, bbox_inches="tight")
	plt.show()


# save_csv() writes one row per (vin, iout) sweep point with stimulus, measured, and optional calculated values
# if file_name is empty, a timestamped name is generated (dc_eff_sweep_YYYYMMDD_HHMMSS.csv)
def save_csv(stim_vectors, meas_vectors, calc_vectors, file_name="5V Linear Regulator IV Sweep"):
	if not file_name:
		file_name = datetime.datetime.now().strftime("dc_eff_sweep_%Y%m%d_%H%M%S.csv")
	if not file_name.lower().endswith(".csv"):
		file_name += ".csv"

	meas_keys = list(meas_vectors.keys())
	calc_keys = list(calc_vectors.keys()) if calc_vectors else []
	header = ["vin_stim", "iout_stim"] + meas_keys + calc_keys

	with open(file_name, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(header)
		for i, stim_vin in enumerate(stim_vectors["vin"]):
			for j, stim_iout in enumerate(stim_vectors["iout"]):
				row = [stim_vin, stim_iout]
				row += [meas_vectors[k][i, j] for k in meas_keys]
				row += [calc_vectors[k][i, j] for k in calc_keys]
				writer.writerow(row)

	print(f"Saved sweep data to {file_name}")
	return file_name


###### SCRIPT

stim_vectors, meas_vectors = init_arrays()
init_instruments()
meas_vectors = sweep(stim_vectors, meas_vectors)
disable_instruments()

calc_vectors = ps_calcs(meas_vectors)
print(calc_vectors["eff_calc"])

save_csv(stim_vectors, meas_vectors, calc_vectors, csv_file_name)

plot_vin_vout_2d(stim_vectors, meas_vectors)



### Code outline

# loaded measurement
#    load on, supply on
#    sweep vin
#    measure vin, iin, vout, iout
#    step iout, repeat vin sweep

# save data, plot data