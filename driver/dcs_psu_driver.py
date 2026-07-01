import serial
import time

gpib = serial.Serial(
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

def configure_prologix_adapter(addr):
	gpib.write(b'++mode 1\n')
	gpib.write(b'++auto 0\n')
	gpib.write(b'++read_tmo_ms 200\n')
	gpib.write(b'++addr {addr}\n')



def read_dcs():
	line = gpib.readline().decode("ascii")
	return line

def write_dcs(command):
	gpib.write((command + '\n').encode("ascii")) # add termination character and encode in ASCII bytes

	return 1

def query_dcs(query):
	gpib.write((query + '\n').encode("ascii"))
	gpib.write(b'++read eoi')

	line = gpib.readline().decode("ascii").replace('\r\n','') # read and decode serial data into string format. Remove CRLF.

	return line

def reset_dcs():
	write_dcs('*RST')
	time.sleep(0.2)
	write_dcs('*CLS')
	return

def set_output(output_state):

	return 1


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
	id = query_dcs('*IDN?').split(', ')

	return id

def get_output_state():
	return

def get_meas_voltage():
	meas_voltage = query_dcs('MEAS:VOLT?')

	return meas_voltage

def get_meas_current(avg):
	return


configure_prologix_adapter(19)

print(query_dcs('OUT?'))
print(query_dcs('OUT?'))
print(query_dcs('OUT?'))
print(query_dcs('*IDN?'))
print(query_dcs('MEAS:VOLT?'))



gpib.close()