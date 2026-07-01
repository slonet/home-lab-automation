import pyvisa
import time


def config_pyvisa():
	rm = pyvisa.ResourceManager('@py') # use pyvisa-py backend
	resources = rm.list_resources()

	gpib_usb = None
	i = 0

	for resource in resources:
		if "cu.usbserial-PXBF0MG0" in resource:
			gpib_usb = rm.open_resource(resource)

	return gpib_usb

def config_prologix(addr, gpib_usb):
	gpib_usb.baud_rate = 19200
	gpib_usb.data_bits = 8
	gpib_usb.stop_bits = pyvisa.constants.StopBits.one
	gpib_usb.parity = pyvisa.constants.Parity.none
	gpib_usb.timeout = 1000
	gpib_usb.write_termination = '\n'
	gpib_usb.read_termination = '\n'

	gpib_usb.write('++mode 1')		# controller mode
	gpib_usb.write('++auto 0') 		# polling mode
	gpib_usb.write('++eoi 1') 		# use the EOI signal
	gpib_usb.write('++eos 0') 		# append CR+LF to end of commands
	gpib_usb.write(f'++addr {addr}')# set the GPIB address of the instrument


def read_dcs():
	return

def write_dcs(command):
	return

def query_dcs(query):
	return

def reset_dcs():
	return

def set_output(output_state):
	return

def set_output_voltage(voltage):
	return

def set_output_current(current):
	return

def set_ovp_threshold(voltage):
	return

def set_ocp_threshold(current):
	return


# get_id(): returns a list of strings representing
#  0: MANUFACTURER
#  1: MODEL
#  2: SERIAL NO.
#  3: DCI FW VERSION
#  4: AI FW VERSION
def get_id():
	return

def get_output_state():
	return

def get_meas_voltage():
	return

def get_meas_current():
	return

#TODO: Write close function

#################### SANDBOX - MAKE SHIT WORK

gpib_usb = config_pyvisa()
print(gpib_usb)

config_prologix(19, gpib_usb)

print(gpib_usb.query('*IDN?'))