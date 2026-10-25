import serial
import time
import numpy as np
import matplotlib.pyplot as plt

import dcs_psu_driver_serial as dcs
import plz_eload_driver_serial as plz


plz_addr = 1
dcs_addr = 19
dcs_current_lim = 5
dcs_meas_avg = 2

vin_min = 6
vin_max = 14
vin_step = 1

iout_min = 1
iout_max = 5
iout_step = 1

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


###### SCRIPT

stim_vectors, meas_vectors = init_arrays()
init_instruments()
meas_vectors = sweep(stim_vectors, meas_vectors)
disable_instruments()

calc_vectors = ps_calcs(meas_vectors)
print(calc_vectors["eff_calc"])

plot_meas_3d(stim_vectors, meas_vectors, "vout_meas")



### Code outline

# loaded measurement
#    load on, supply on
#    sweep vin
#    measure vin, iin, vout, iout
#    step iout, repeat vin sweep

# save data, plot data