import serial
import time

def configure_prologix_adapter(addr):
	global gpib_usb

	gpib_usb = serial.Serial(
		port = '/dev/cu.usbserial-PXBF0MG0',
		baudrate = 115200,
		bytesize = serial.EIGHTBITS,
		parity = serial.PARITY_NONE,
		stopbits = serial.STOPBITS_ONE,
		timeout = 1,
		xonxoff = False,
		rtscts = False,
		dsrdtr = False
	)

	gpib_usb.write(b'++mode 1\n')		# prologix GPIB-USB is a GPIB controller
	gpib_usb.write(b'++auto 0\n')		# auto mode is off requiring explicit read commands
	gpib_usb.write(b'++eoi 1\n')		# use EOI signal
	gpib_usb.write(b'++eos 0\n')		# appends CR+LF to the end of all GPIB commands
	addr_command = f'++addr {addr}\n'
	gpib_usb.write(addr_command.encode("utf-8"))  # sets the address

	return gpib_usb


def close_plz():
	gpib_usb.close()
	
	return 1

# reset_plz() sets all memory regisetrs to default settings and clears alarm and error registers
def reset_plz():
	write_plz('RCLALL 0')
	write_plz('RCLSET 0')
	write_plz('RCLMEM 0')
	write_plz('RESET')
	write_plz('ERR?')
	
	return 1

def read_plz():
	line = gpib_usb.readline().decode("utf-8")
	
	return line

def write_plz(command):
	gpib_usb.write((command + '\n').encode("utf-8")) # add termination character and encode in utf-8 bytes

	return 1

def query_plz(query):
	gpib_usb.write((query + '\n').encode("utf-8"))
	gpib_usb.write(b'++read eoi\n')
	
	line = gpib_usb.readline().decode("utf-8").replace('\r\n','') # read and decode serial data into string format. Remove CRLF.

	return line


########### SET FUNCTIONS


def set_load_state(state):
	write_plz(f'LOAD {state}')

	return 1

def set_load_mode(mode):
	if mode == 'CC':	# constant current mode
		write_plz('CCCR 1')
	elif mode == 'CR':	# constant resistance mode
		write_plz('CCCR 2')
	else:
		return -1

	return 1

def set_voltage_mode(mode):
	write_plz(f'CV {mode}')	# 0 = OFF, 1 = ON

	return 1

def set_load_voltage(voltage):
	write_plz(f'VSET {voltage}')

	return 1

def set_load_current(current):
	write_plz(f'ISET {current}')

	return 1

def set_load_resistance(resistance):
	write_plz(f'RSET {resistance}')

	return 1

def set_load_power(power):
	write_plz(f'PSET {power}')

	return 1

def set_current_range(cc_range):
	write_plz(f'CCRANGE {cc_range}')

	return 1

def set_resistance_range(cr_range):
	write_plz(f'CRRANGE {cr_range}')

	return 1

# set_rise_fall_time(trtf) sets the transition time between current or resistance setpoints.
# valid values for trtf are integers 0-7 which correspond to the following rise/fall times
#
# 0 = 50us
# 1 = 100us
# 2 = 200us
# 3 = 500us
# 4 = 1ms
# 5 = 2ms
# 6 = 5ms
# 7 = 10ms
#
def set_rise_fall_time(trtf):
	if trtf >= 0 and trtf <= 7:
		write_plz(f'TRTF {trtf}')
	else:
		return -1
	
	return 1

# set_soft_start_time(start_time) sets the transition time from load OFF to load ON in CC mode.
# valid values for start_time are integers 0-7 which correspond to the following soft start times
#
# 0 = 0ms
# 1 = 1ms
# 2 = 2ms
# 3 = 5ms
# 4 = 10ms
# 5 = 20ms
# 6 = 50ms
# 7 = 100ms
#
def set_soft_start_time(start_time):
	if start_time >= 0 and start_time <= 7:
		write_plz(f'STARTTIME {start_time}')
	else:
		return -1
	
	return 1

def set_short_state(state):
	write_plz(f'SHORT {state}')

	return 1

def set_current_trigger(current):
	write_plz(f'TRIGISET {current}')
	write_plz('TRG')

	return 1

def set_resistance_trigger(resistance):
	write_plz(f'TRIGRSET {resistance}')
	write_plz('TRG')

	return 1

def set_voltage_trigger(voltage):
	write_plz(f'TRIGRSET {voltage}')
	write_plz('TRG')

	return 1

def set_power_trigger(power)
	write_plz(f'TRIGPSET {power}')
	write_plz('TRG')

	return 1

def set_clear_trigger():
	write_plz('TRIGSTOP')

	return 1

########### GET FUNCTIONS


def get_id():
	instrument_id = query_plz('IDN?')

	return instrument_id

def get_load_state():
	state = int(query_plz('LOAD?').split(' ')[-1])

	return state

def get_load_mode():
	mode = int(query_plz('CCCR?').split(' ')[-1])

	if mode == 1:
		mode = 'CC'
	elif mode == 2:
		mode  = 'CR'
	else:
		mode = -1

	return mode

def get_voltage_mode():
	mode = int(query_plz('CV?').split(' ')[-1])

	return mode

def get_load_current():
	current = float(query_plz('ISET?').split(' ')[-1].replace('A', ''))

	return current

def get_load_resistance():
	resistance = float(query_plz('RSET?').split(' ')[-1].replace('OHM', ''))

	return resistance

def get_load_voltage():
	voltage = float(query_plz('VSET?').split(' ')[-1].replace('V', ''))

	return voltage

def get_load_power():
	power = float(query_plz('PSET?').split(' ')[-1].replace('W', ''))
	
	return power

def get_current_range():
	cc_range = int(query_plz('CCRANGE?').split(' ')[-1])

	return cc_range

def get_resistance_range():
	cr_range = int(query_plz('CRRANGE?').split(' ')[-1])

	return cr_range

def get_meas_current():
	current = float(query_plz('CURR?').split(' ')[-1].replace('A', ''))

	return current

def get_meas_voltage():
	voltage = float(query_plz('VOLT?').split(' ')[-1].replace('V', ''))
	
	return voltage

def get_meas_power():
	power = float(query_plz('POW?').split(' ')[-1].replace('W', ''))

	return power

def get_rise_fall_time():
	trtf = int(query_plz('TRTF?').split(' ')[-1])
	
	return trtf

def get_soft_start_time():
	start_time = int(query_plz('STARTTIME?').split(' ')[-1])

	return start_time

def get_short_state():
	state = int(query_plz('SHORT?').split(' ')[-1])

	return state


########### SANDBOX