"""
Signal Processing Framework - Logic Layer
Enhanced with additional operations
"""

import math
import numpy as np


class SignalProcessor:
    """Core signal processing operations"""

    @staticmethod
    def parse_signal_file(file_path):
        """
        Parse signal file format:
        Line 1: Signal Type (0/1)
        Line 2: Periodicity (0/1)
        Line 3: Num Samples
        Line 4+: Data (Index Amplitude)
        """
        try:
            with open(file_path, 'r') as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]

            if len(lines) < 4:
                raise ValueError("File must have at least 4 lines")

            # Parse header
            signal_type = int(lines[0])
            is_periodic = int(lines[1])
            num_samples_header = int(lines[2])

            indices = []
            samples = []

            # Parse data lines
            for i in range(3, min(3 + num_samples_header, len(lines))):
                parts = lines[i].split()
                if len(parts) >= 2:
                    indices.append(float(parts[0]))
                    samples.append(float(parts[1]))

            return {
                "indices": indices,
                "samples": samples,
                "signal_type": signal_type,
                "is_periodic": is_periodic,
                "num_samples": len(samples)
            }

        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    @staticmethod
    def calculate_statistics(samples):
        """Calculate basic statistics"""
        if not samples:
            return {"min": 0, "max": 0, "mean": 0}

        return {
            "min": min(samples),
            "max": max(samples),
            "mean": sum(samples) / len(samples)
        }

    # Signal Generation Methods
    @staticmethod
    def generate_sinusoidal(amplitude, analog_freq, phase_deg, sampling_freq, is_cosine=False, duration=1.0):
        """Generate sine/cosine wave"""
        if sampling_freq <= 2 * analog_freq:
            raise ValueError(f"Sampling frequency must be > {2 * analog_freq} Hz")

        phase_rad = math.radians(phase_deg)
        num_samples = int(duration * sampling_freq)

        t = np.arange(num_samples) / sampling_freq

        if is_cosine:
            samples = amplitude * np.cos(2 * np.pi * analog_freq * t + phase_rad)
        else:
            samples = amplitude * np.sin(2 * np.pi * analog_freq * t + phase_rad)

        return {
            "indices": t.tolist(),
            "samples": samples.tolist(),
            "signal_type": 0,
            "is_periodic": 1,
            "num_samples": num_samples,
            "x_label": "Time (s)"
        }

    # Arithmetic Operations
    @staticmethod
    def add_signals(signals):
        """Add multiple signals"""
        if len(signals) < 2:
            raise ValueError("Need at least 2 signals")

        min_len = min(len(sig["samples"]) for sig in signals)
        result_samples = [0] * min_len

        for i in range(min_len):
            for sig in signals:
                result_samples[i] += sig["samples"][i]

        return {
            "indices": signals[0]["indices"][:min_len],
            "samples": result_samples,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": min_len
        }

    @staticmethod
    def multiply_signal(signal, constant):
        """Multiply signal by constant"""
        return {
            "indices": signal["indices"],
            "samples": [s * constant for s in signal["samples"]],
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def subtract_signals(signal1, signal2):
        """Subtract signal2 from signal1"""
        min_len = min(len(signal1["samples"]), len(signal2["samples"]))
        result_samples = [signal1["samples"][i] - signal2["samples"][i] for i in range(min_len)]

        return {
            "indices": signal1["indices"][:min_len],
            "samples": result_samples,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": min_len
        }

    @staticmethod
    def square_signal(signal):
        """Square signal samples"""
        return {
            "indices": signal["indices"],
            "samples": [s ** 2 for s in signal["samples"]],
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def normalize_signal(signal, target_range):
        """Normalize signal to range"""
        samples = signal["samples"]
        min_val = min(samples)
        max_val = max(samples)

        if max_val == min_val:
            normalized = [0] * len(samples)
        else:
            normalized = [(s - min_val) / (max_val - min_val) for s in samples]

            if target_range == "-1_to_1":
                normalized = [2 * n - 1 for n in normalized]

        return {
            "indices": signal["indices"],
            "samples": normalized,
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def accumulate_signal(signal):
        """Accumulate signal (running sum)"""
        samples = signal["samples"]
        accumulated = []
        total = 0

        for s in samples:
            total += s
            accumulated.append(total)

        return {
            "indices": signal["indices"],
            "samples": accumulated,
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": signal["num_samples"]
        }

    # Additional Operations
    @staticmethod
    def scale_signal(signal, scale_factor):
        """Scale signal by factor (time scaling)"""
        if scale_factor <= 0:
            raise ValueError("Scale factor must be positive")

        indices = signal["indices"]
        samples = signal["samples"]

        # For time scaling, we adjust the indices
        scaled_indices = [idx * scale_factor for idx in indices]

        return {
            "indices": scaled_indices,
            "samples": samples,
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"],
            "x_label": f"Scaled Time (×{scale_factor})"
        }

    @staticmethod
    def shift_signal(signal, shift_amount):
        """Shift signal in time"""
        indices = signal["indices"]
        shifted_indices = [idx + shift_amount for idx in indices]

        return {
            "indices": shifted_indices,
            "samples": signal["samples"],
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"],
            "x_label": f"Shifted Time (+{shift_amount})"
        }

    @staticmethod
    def reverse_signal(signal):
        """Reverse signal in time"""
        return {
            "indices": list(reversed(signal["indices"])),
            "samples": list(reversed(signal["samples"])),
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"],
            "x_label": "Reversed Time"
        }

    @staticmethod
    def differentiate_signal(signal):
        """Numerical differentiation of signal"""
        samples = signal["samples"]
        indices = signal["indices"]

        if len(samples) < 2:
            raise ValueError("Signal must have at least 2 samples for differentiation")

        derivative = []
        for i in range(len(samples) - 1):
            dx = indices[i + 1] - indices[i]
            dy = samples[i + 1] - samples[i]
            derivative.append(dy / dx if dx != 0 else 0)

        # Add last point (same as previous)
        derivative.append(derivative[-1] if derivative else 0)

        return {
            "indices": indices,
            "samples": derivative,
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": len(derivative),
            "x_label": signal.get("x_label", "Time")
        }

    @staticmethod
    def integrate_signal(signal):
        """Numerical integration of signal"""
        samples = signal["samples"]
        indices = signal["indices"]

        integral = []
        total = 0

        for i in range(len(samples)):
            if i > 0:
                dx = indices[i] - indices[i - 1]
                # Trapezoidal rule
                total += (samples[i] + samples[i - 1]) * dx / 2
            integral.append(total)

        return {
            "indices": indices,
            "samples": integral,
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": len(integral),
            "x_label": signal.get("x_label", "Time")
        }

    @staticmethod
    def convolution(signal1, signal2):
        """Convolution of two signals"""
        samples1 = signal1["samples"]
        samples2 = signal2["samples"]

        n = len(samples1)
        m = len(samples2)
        result_length = n + m - 1

        # Simple convolution implementation
        result = [0] * result_length
        for i in range(n):
            for j in range(m):
                result[i + j] += samples1[i] * samples2[j]

        # Generate appropriate indices
        min_idx = signal1["indices"][0] + signal2["indices"][0]
        max_idx = signal1["indices"][-1] + signal2["indices"][-1]
        indices = np.linspace(min_idx, max_idx, result_length).tolist()

        return {
            "indices": indices,
            "samples": result,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": result_length,
            "x_label": "Convolution Index"
        }

    @staticmethod
    def correlation(signal1, signal2):
        """Cross-correlation of two signals"""
        samples1 = signal1["samples"]
        samples2 = signal2["samples"]

        n = len(samples1)
        m = len(samples2)
        result_length = n + m - 1

        # Simple correlation implementation
        result = [0] * result_length
        for i in range(result_length):
            for j in range(max(0, i - m + 1), min(i + 1, n)):
                if 0 <= i - j < m:
                    result[i] += samples1[j] * samples2[i - j]

        # Generate appropriate indices
        min_lag = -m + 1
        max_lag = n - 1
        lags = list(range(min_lag, max_lag + 1))

        return {
            "indices": lags,
            "samples": result,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": result_length,
            "x_label": "Lag"
        }


class SignalDataManager:
    """Manages signal data storage"""

    def __init__(self):
        self.signals = []

    def add_signal(self, signal_data, name="", filepath=""):
        """Add signal to manager"""
        signal_data["name"] = name
        signal_data["filepath"] = filepath
        self.signals.append(signal_data)
        return len(self.signals) - 1

    def get_signal(self, index):
        """Get signal by index"""
        return self.signals[index] if 0 <= index < len(self.signals) else None

    def get_all_signals(self):
        """Get all signals"""
        return self.signals

    def clear_signals(self):
        """Clear all signals"""
        self.signals = []

    def get_signal_count(self):
        """Get signal count"""
        return len(self.signals)