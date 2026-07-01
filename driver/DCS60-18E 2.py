from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Union

try:
    import serial
    from serial import Serial
except Exception:  # pragma: no cover
    serial = None
    Serial = object

Number = Union[int, float]


class SorensenDCSError(Exception):
    pass


class SorensenDCSCommunicationError(SorensenDCSError):
    pass


class SorensenDCSInstrumentError(SorensenDCSError):
    def __init__(self, code: int, message: str):
        self.code = int(code)
        self.message = message
        super().__init__(f"Sorensen DCS error {self.code}: {self.message}")


@dataclass
class DCSMeasurement:
    voltage_v: float
    current_a: float


class SorensenDCS60_18E:
    MAX_VOLTAGE = 60.0
    MAX_CURRENT = 18.0

    def __init__(
        self,
        port: str,
        baudrate: int = 19200,
        timeout: float = 1.0,
        write_timeout: float = 1.0,
        terminator: str = "\n",
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
            stopbits=serial.STOPBITS_ONE,
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

    def __enter__(self) -> "SorensenDCS60_18E":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _require_open(self) -> Serial:
        if not self._ser or not self._ser.is_open:
            raise SorensenDCSCommunicationError("Serial port is not open")
        return self._ser

    def write_raw(self, command: str) -> None:
        ser = self._require_open()
        ser.write((command + self.terminator).encode("ascii"))
        ser.flush()

    def read_raw(self) -> str:
        ser = self._require_open()
        data = ser.readline()
        if not data:
            raise SorensenDCSCommunicationError("Timeout waiting for response")
        return data.decode("ascii", errors="replace").strip()

    def write(self, command: str, check_error: bool = True) -> None:
        self.write_raw(command)
        if check_error:
            self.check_error()

    def query(self, command: str, check_error: bool = False) -> str:
        self.write_raw(command)
        response = self.read_raw()
        if check_error:
            self.check_error()
        return response

    def identify(self) -> str:
        return self.query("*IDN?")

    def clear_status(self) -> None:
        self.write_raw("*CLS")

    def reset(self) -> None:
        self.write_raw("*RST")

    def wait_complete(self) -> bool:
        return self.query("*OPC?").strip() == "1"

    def check_error(self) -> None:
        resp = self.query("SYST:ERR?")
        if resp.startswith("0"):
            return
        if "," in resp:
            code_str, msg = resp.split(",", 1)
            raise SorensenDCSInstrumentError(int(code_str.strip()), msg.strip().strip('"'))
        raise SorensenDCSInstrumentError(-1, resp)

    def set_remote(self, remote: bool = True) -> None:
        self.write(f"SYST:LOCAL {'OFF' if remote else 'ON'}", check_error=False)
        self.check_error()

    def output_on(self) -> None:
        self.write("OUTP:STAT ON")

    def output_off(self) -> None:
        self.write("OUTP:STAT OFF")

    def set_output(self, enabled: bool) -> None:
        self.write(f"OUTP:STAT {'ON' if enabled else 'OFF'}")

    def output_enabled(self) -> bool:
        return self.query("OUTP:STAT?").strip() in {"1", "ON"}

    def set_voltage(self, volts: Number) -> None:
        self.write(f"SOUR:VOLT {float(volts):.6f}V")

    def get_voltage_setting(self) -> float:
        return float(self.query("SOUR:VOLT?"))

    def set_current(self, amps: Number) -> None:
        self.write(f"SOUR:CURR {float(amps):.6f}A")

    def get_current_setting(self) -> float:
        return float(self.query("SOUR:CURR?"))

    def set_voltage_limit(self, volts: Number) -> None:
        self.write(f"SOUR:VOLT:LIM {float(volts):.6f}V")

    def get_voltage_limit(self) -> float:
        return float(self.query("SOUR:VOLT:LIM?"))

    def set_current_limit(self, amps: Number) -> None:
        self.write(f"SOUR:CURR:LIM {float(amps):.6f}A")

    def get_current_limit(self) -> float:
        return float(self.query("SOUR:CURR:LIM?"))

    def set_ovp(self, volts: Number) -> None:
        self.write(f"SOUR:VOLT:PROT {float(volts):.6f}V")

    def get_ovp(self) -> float:
        return float(self.query("SOUR:VOLT:PROT?"))

    def ovp_tripped(self) -> bool:
        return self.query("SOUR:VOLT:PROT:TRIP?" if False else "SOUR:VOLT:PROT:TRIPP?", check_error=False) == "1"

    def measure_voltage(self) -> float:
        return float(self.query("MEAS:VOLT?"))

    def measure_current(self) -> float:
        return float(self.query("MEAS:CURR?"))

    def measure_all(self) -> DCSMeasurement:
        return DCSMeasurement(
            voltage_v=self.measure_voltage(),
            current_a=self.measure_current(),
        )

    def protection_condition(self) -> int:
        return int(self.query("STAT:PROT:COND?", check_error=False))

    def protection_event(self) -> int:
        return int(self.query("STAT:PROT:EVEN?", check_error=False))

    def status_byte(self) -> int:
        return int(self.query("*STB?", check_error=False))

    def event_status(self) -> int:
        return int(self.query("*ESR?", check_error=False))

    def set_trip_delay(self, seconds: Number) -> None:
        self.write(f"OUTP:PROT:DEL {float(seconds):.6f}S")

    def get_trip_delay(self) -> float:
        return float(self.query("OUTP:PROT:DEL?"))

    def set_foldback_mode(self, mode: int) -> None:
        if mode not in (0, 1, 2):
            raise ValueError("mode must be 0=OFF, 1=CV, or 2=CC")
        self.write(f"OUTP:PROT:FOLD {mode}")

    def set_triggered_voltage(self, volts: Number) -> None:
        self.write(f"SOUR:VOLT:TRIG {float(volts):.6f}V")

    def set_triggered_current(self, amps: Number) -> None:
        self.write(f"SOUR:CURR:TRIG {float(amps):.6f}A")

    def trigger(self, which: int = 3) -> None:
        if which not in (1, 2, 3):
            raise ValueError("which must be 1=voltage, 2=current, 3=both")
        self.write(f"TRIG:TYPE {which}")

    def configure(self, voltage_v: Number, current_a: Number, output_on: bool = True) -> None:
        self.set_current_limit(self.MAX_CURRENT)
        self.set_voltage_limit(self.MAX_VOLTAGE)
        self.set_current(current_a)
        self.set_voltage(voltage_v)
        self.set_output(output_on)

    def wait_for_voltage(self, target_v: Number, tolerance: float = 0.05, timeout: float = 5.0) -> float:
        t0 = time.time()
        target_v = float(target_v)
        while True:
            v = self.measure_voltage()
            if abs(v - target_v) <= tolerance:
                return v
            if time.time() - t0 > timeout:
                raise TimeoutError(f"Voltage did not settle to {target_v} V within {timeout} s")
            time.sleep(0.05)


__all__ = [
    "SorensenDCS60_18E",
    "DCSMeasurement",
    "SorensenDCSError",
    "SorensenDCSCommunicationError",
    "SorensenDCSInstrumentError",
]