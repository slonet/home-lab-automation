from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Tuple, Union

try:
    import serial
    from serial import Serial
except Exception:  # pragma: no cover
    serial = None
    Serial = object

Number = Union[int, float]


class PLZ603WError(Exception):
    pass


class PLZ603WCommunicationError(PLZ603WError):
    pass


class PLZ603WInstrumentError(PLZ603WError):
    ERROR_CODES = {
        0: "No error",
        1: "Syntax Error",
        2: "Argument Error",
        14: "Memory Full",
        15: "Diff. Mode",
        16: "Warning Data",
        21: "SW State",
        22: "SEQ State",
        23: "SHORT State",
        24: "Alarm State",
        25: "SLAVE State",
        26: "CV OFF",
        27: "EXECUTE0",
        28: "Invalidity",
    }

    def __init__(self, code: int):
        self.code = int(code)
        msg = self.ERROR_CODES.get(self.code, f"Unknown instrument error {self.code}")
        super().__init__(f"PLZ603W error {self.code}: {msg}")


@dataclass
class Measurement:
    current_a: float
    voltage_v: float
    power_w: float


class KikusuiPLZ603W:
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        write_timeout: float = 1.0,
        terminator: str = "\r\n",
        auto_open: bool = True,
    ) -> None:
        if serial is None:
            raise ImportError("pyserial is required: pip install pyserial")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.terminator = terminator
        self._ser: Optional[Serial] = None
        if auto_open:
            self.open()

    def open(self) -> None:
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=self.timeout,
            write_timeout=self.write_timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()

    def __enter__(self) -> "KikusuiPLZ603W":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return bool(self._ser and self._ser.is_open)

    def _require_open(self) -> Serial:
        if not self._ser or not self._ser.is_open:
            raise PLZ603WCommunicationError("Serial port is not open")
        return self._ser

    def write_raw(self, command: str) -> None:
        ser = self._require_open()
        payload = (command + self.terminator).encode("ascii")
        ser.write(payload)
        ser.flush()

    def read_raw(self) -> str:
        ser = self._require_open()
        data = ser.readline()
        if not data:
            raise PLZ603WCommunicationError("Timeout waiting for response")
        return data.decode("ascii", errors="replace").strip()

    def write(self, command: str, check_error: bool = True) -> None:
        self.write_raw(command)
        if check_error:
            self.check_error()

    def query(self, command: str, check_error: bool = True) -> str:
        self.write_raw(command)
        response = self.read_raw()
        if check_error:
            self.check_error()
        return response

    def check_error(self) -> int:
        code = int(self.query_no_check("ERR?"))
        if code != 0:
            raise PLZ603WInstrumentError(code)
        return code

    def query_no_check(self, command: str) -> str:
        self.write_raw(command)
        return self.read_raw()

    def identify(self) -> str:
        return self.query("IDN?", check_error=False)

    def reset_alarm(self) -> None:
        self.write("RESET", check_error=False)

    def set_remote_defaults(self) -> None:
        self.write("TERM 0", check_error=False)
        self.write("HEAD 0", check_error=False)

    def set_load(self, on: bool) -> None:
        self.write(f"LOAD {1 if on else 0}")

    def load_on(self) -> None:
        self.set_load(True)

    def load_off(self) -> None:
        self.set_load(False)

    def get_load(self) -> bool:
        return bool(int(self.query("LOAD?")))

    def set_mode_cc(self) -> None:
        self.write("CCCR 1")

    def set_mode_cr(self) -> None:
        self.write("CCCR 2")

    def set_cv_enabled(self, enabled: bool) -> None:
        self.write(f"CV {1 if enabled else 0}")

    def set_cc_range_high(self, high: bool = True) -> None:
        self.write(f"CCRANGE {1 if high else 0}")

    def set_cr_range_high(self, high: bool = True) -> None:
        self.write(f"CRRANGE {1 if high else 0}")

    def set_current(self, amps: Number) -> None:
        self.write(f"ISET {float(amps):.6f}A")

    def get_current_setting(self) -> float:
        return float(self.query("ISET?"))

    def set_resistance(self, ohms: Number) -> None:
        self.write(f"RSET {float(ohms):.6f}OHM")

    def get_resistance_setting(self) -> float:
        return float(self.query("RSET?"))

    def set_voltage(self, volts: Number) -> None:
        self.write(f"VSET {float(volts):.6f}V")

    def get_voltage_setting(self) -> float:
        return float(self.query("VSET?"))

    def set_power(self, watts: Number) -> None:
        self.write(f"PSET {float(watts):.6f}W")

    def get_power_setting(self) -> float:
        return float(self.query("PSET?"))

    def measure_current(self) -> float:
        return float(self.query("CURR?"))

    def measure_voltage(self) -> float:
        return float(self.query("VOLT?"))

    def measure_power(self) -> float:
        return float(self.query("POW?"))

    def measure_all(self) -> Measurement:
        return Measurement(
            current_a=self.measure_current(),
            voltage_v=self.measure_voltage(),
            power_w=self.measure_power(),
        )

    def get_status_byte(self) -> int:
        return int(self.query("STB?", check_error=False))

    def get_status_register(self) -> int:
        return int(self.query("STS?", check_error=False))

    def get_fault_register(self) -> int:
        return int(self.query("FAU?", check_error=False))

    def trigger_current(self, amps: Number) -> None:
        self.write_raw(f"TRIGISET {float(amps):.6f}A")
        self.write("TRIG", check_error=False)
        self.check_error()

    def trigger_voltage(self, volts: Number) -> None:
        self.write_raw(f"TRIGVSET {float(volts):.6f}V")
        self.write("TRIG", check_error=False)
        self.check_error()

    def trigger_power(self, watts: Number) -> None:
        self.write_raw(f"TRIGPSET {float(watts):.6f}W")
        self.write("TRIG", check_error=False)
        self.check_error()

    def trigger_resistance(self, ohms: Number) -> None:
        self.write_raw(f"TRIGRSET {float(ohms):.6f}OHM")
        self.write("TRIG", check_error=False)
        self.check_error()

    def local(self) -> None:
        self.write_raw("LOCAL")

    def poll_until(
        self,
        predicate,
        timeout: float = 5.0,
        interval: float = 0.05,
    ):
        t0 = time.time()
        while True:
            value = predicate()
            if value:
                return value
            if time.time() - t0 > timeout:
                raise TimeoutError("Timeout waiting for PLZ603W condition")
            time.sleep(interval)

    def configure_cc(self, current_a: Number, load_on: bool = False, high_range: bool = True) -> None:
        self.set_mode_cc()
        self.set_cc_range_high(high_range)
        self.set_current(current_a)
        self.set_load(load_on)

    def configure_cr(self, resistance_ohm: Number, load_on: bool = False, high_range: bool = True) -> None:
        self.set_mode_cr()
        self.set_cr_range_high(high_range)
        self.set_resistance(resistance_ohm)
        self.set_load(load_on)

    def configure_cp(self, power_w: Number, load_on: bool = False) -> None:
        self.set_power(power_w)
        self.set_load(load_on)

    def configure_cv(self, voltage_v: Number, load_on: bool = False) -> None:
        self.set_cv_enabled(True)
        self.set_voltage(voltage_v)
        self.set_load(load_on)


__all__ = [
    "KikusuiPLZ603W",
    "Measurement",
    "PLZ603WError",
    "PLZ603WCommunicationError",
    "PLZ603WInstrumentError",
]