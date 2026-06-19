import pyvisa

rm = pyvisa.ResourceManager('@py')

resources = rm.list_resources()

print(resources)

## Configure serial port for GPIB
gpib_inst = rm.open_resource(
	'ASRL/dev/cu.usbserial-PXBF0MG0::INSTR',
	baud_rate = 19200,
	data_bits = 8,
	parity = pyvisa.constants.Parity.none,
	stop_bits = pyvisa.constants.StopBits.one,
	write_termination = '\n',
	read_termination = '\n',
	timeout = 1000
	)

## Configure prologix USB - GPIB adapter
gpib_inst.write('++mode 1')
gpib_inst.write('++auto 1')

ps_gpib_addr = 0
eload_gpib_addr = 0

while ps_gpib_addr <= 30:
	gpib_inst.write(f'++addr {ps_gpib_addr}')
	gpib_inst.write('*IDN?')
	#gpib_inst.write('++read eoi')

	try:
		idn = gpib_inst.read()
	except:
		print(f'address {ps_gpib_addr} is: nothing')
	else:
		print(f'address {ps_gpib_addr} is: ' + idn)

	ps_gpib_addr += 1