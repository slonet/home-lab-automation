import serial
import time

def configure_prologix_adapter(addr):
	global gpib_usb

	gpib_usb = serial.Serial(
		port = '/dev/cu.usbserial-PXBF0MG0',
		baudrate = 19200,
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
	gpib_usb.write(b'++eos 0\n')		# appends CR+LF to the end of all GPIB commands
	addr_command = f'++addr {addr}\n'
	gpib_usb.write(addr_command.encode("utf-8"))  # sets the address

	return gpib_usb

def close_dcs():
	gpib_usb.close()

	return 1

def read_dcs():
	line = gpib_usb.readline().decode("utf-8")
	
	return line

def write_dcs(command):
	gpib_usb.write((command + '\n').encode("utf-8")) # add termination character and encode in utf-8 bytes

	return 1

def query_dcs(query):
	gpib_usb.write((query + '\n').encode("utf-8"))
	gpib_usb.write(b'++read eoi\n')
	
	line = gpib_usb.readline().decode("utf-8").replace('\r\n','') # read and decode serial data into string format. Remove CRLF.

	return line

# reset_dcs(): resets the supply and then does some serial buffer magic to get the next query to work
def reset_dcs():
	write_dcs('*RST')
	time.sleep(0.1)
	write_dcs('*CLS')
	query_dcs('')
	read_dcs()

	return 1

def set_output(output_state):
	write_dcs(f'OUTP:STAT {output_state}')
	
	return 1


def set_output_voltage(voltage):
	write_dcs(f'SOUR:VOLT {voltage}')
	
	return 1

def set_output_current(current):
	write_dcs(f'SOUR:CURR {current}')
	
	return 1

def set_ovp_threshold(voltage):
	if voltage >= 0:
		write_dcs(f'SOUR:VOLT:PROT {voltage}')
	else:
		return -1

	return 1

def set_voltage_limit(voltage):
	if voltage >= 0:
		write_dcs(f'SOUR:VOLT:LIM {voltage}')
	else:
		return -1

	return 1

def set_current_limit(current):
	if current >= 0:
		write_dcs(f'SOUR:CURR:LIM {current}')
	else:
		return -1

	return 1

def set_voltage_avg(avg):
	if avg >= 1 and avg <= 5:
		write_dcs(f'MEAS:VOLT:AVE {avg}')
	else:
		return -1
	
	return 1

def set_current_avg(avg):
	if avg >= 1 and avg <= 5:
		write_dcs(f'MEAS:CURR:AVE {avg}')
	else:
		return -1
	
	return 1

# get_id(): returns a list of strings representing
#  0: MANUFACTURER
#  1: MODEL
#  2: SERIAL NO.
#  3: DCI FW VERSION
#  4: AI FW VERSION
def get_id():
	instrument_id = query_dcs('*IDN?').split(', ')

	return instrument_id

def get_output_state():
	state = int(query_dcs('OUTP:STAT?'))

	return state

def get_meas_voltage():
	meas_voltage = float(query_dcs('MEAS:VOLT?'))

	return meas_voltage

def get_meas_current():
	meas_current = float(query_dcs('MEAS:CURR?'))

	return meas_current

def get_voltage_avg():
	avg = int(query_dcs('MEAS:VOLT:AVE?'))
	
	return avg

def get_current_avg():
	avg = int(query_dcs('MEAS:CURR:AVE?'))
	
	return avg

def get_ovp_threshold():
	voltage = float(query_dcs('SOUR:VOLT:PROT?'))
	
	return voltage

def get_voltage_limit():
	voltage = float(query_dcs('SOUR:VOLT:LIM?'))
	
	return voltage

def get_current_limit():
	current = float(query_dcs('SOUR:CURR:LIM?'))

	return current

######### SANDBOX

configure_prologix_adapter(19)
reset_dcs()

close_dcs()
