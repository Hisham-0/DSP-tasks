"""
Signal Processing Framework - Logic Layer
Handles all signal processing operations and data manipulation
"""

import math
import numpy as np

class SignalProcessor:
    """Core signal processing operations - Pure logic without GUI dependencies"""

    @staticmethod
    def parse_signal_file(file_path):
        """
        Parse signal file according to the specified format.

        Format:
        Line 1: Signal Type (0/1)
        Line 2: Periodicity (0/1)
        Line 3: Num Samples
        Line 4+: Data (Index Amplitude)
        """
        try:
            with open(file_path, 'r') as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]

            if len(lines) < 4:
                raise ValueError("File must have at least 4 lines (Header + 1 Sample)")

            # Parse header
            signal_type = int(lines[0])
            is_periodic = int(lines[1])
            num_samples_header = int(lines[2])

            indices = []
            samples = []

            # Parse data lines
            data_stop_index = min(3 + num_samples_header, len(lines))
            for i in range(3, data_stop_index):
                parts = lines[i].split()
                if len(parts) != 2:
                    raise ValueError(f"Line {i + 1}: Expected 2 values (Index Amplitude)")

                indices.append(float(parts[0]))
                samples.append(float(parts[1]))

            num_samples = len(samples)

            if num_samples_header != num_samples:
                print(f"Warning: Header declared {num_samples_header} samples, but {num_samples} samples parsed.")

            return {
                "indices": indices,
                "samples": samples,
                "signal_type": signal_type,
                "is_periodic": is_periodic,
                "num_samples": num_samples
            }

        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    @staticmethod
    def calculate_statistics(samples):
        """Calculate basic statistics (min, max, mean)"""
        if not samples:
            return {"min": 0, "max": 0, "mean": 0}

        np_samples = np.array(samples)
        return {
            "min": np.min(np_samples),
            "max": np.max(np_samples),
            "mean": np.mean(np_samples)
        }

    # --- Signal Generation Methods ---

    @staticmethod
    def generate_sinusoidal(amplitude, analog_freq_f, phase_theta_deg, sampling_freq_fs, is_cosine=False,total_time_s=1.0):
        """
        Generate a discrete-time sine or cosine wave.
        Validates sampling theorem: Fs > 2*F
        """
        if sampling_freq_fs <= 2 * analog_freq_f:
            raise ValueError(
                f"Sampling Theorem Violation: Fs ({sampling_freq_fs} Hz) must be > 2 * F ({2 * analog_freq_f} Hz)"
            )

        phase_theta_rad = math.radians(phase_theta_deg)
        num_samples = math.ceil(total_time_s * sampling_freq_fs)

        n = np.arange(num_samples)
        t = n / sampling_freq_fs

        if is_cosine:
            samples = amplitude * np.cos(2 * np.pi * analog_freq_f * t + phase_theta_rad)
        else:
            samples = amplitude * np.sin(2 * np.pi * analog_freq_f * t + phase_theta_rad)

        return {
            "indices": t.tolist(),
            "samples": samples.tolist(),
            "signal_type": 0,
            "is_periodic": 1,
            "num_samples": num_samples,
            "x_label": "Time (s)",
            "metadata": {
                "Amplitude (A)": amplitude,
                "Analog Frequency (F)": analog_freq_f,
                "Phase (theta)": f"{phase_theta_deg}° ({phase_theta_rad:.4f} rad)",
                "Sampling Frequency (Fs)": sampling_freq_fs,
                "Wave Type": "Cosine" if is_cosine else "Sine",
            }
        }

    # --- Arithmetic Operations ---

    @staticmethod
    def add_signals(signal_list):
        """Add multiple signals together (element-wise on common indices)"""
        if len(signal_list) < 2:
            raise ValueError("Need at least 2 signals for addition")

        min_length = min(len(sig["samples"]) for sig in signal_list)
        result_indices = signal_list[0]["indices"][:min_length]
        result_samples = np.zeros(min_length)

        for signal in signal_list:
            result_samples += np.array(signal["samples"][:min_length])

        return {
            "indices": result_indices,
            "samples": result_samples.tolist(),
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": min_length
        }

    @staticmethod
    def subtract_signals(signal1, signal2):
        """Subtract signal2 from signal1 (Task 2: 2.i)"""
        min_length = min(len(signal1["samples"]), len(signal2["samples"]))
        result_indices = signal1["indices"][:min_length]
        result_samples = [signal1["samples"][i] - signal2["samples"][i] for i in range(min_length)]

        return {
            "indices": result_indices,
            "samples": result_samples,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": min_length
        }

    @staticmethod
    def multiply_signal(signal, constant):
        """Multiply signal by a constant"""
        result_samples = [s * constant for s in signal["samples"]]
        return {
            "indices": signal["indices"][:],
            "samples": result_samples,
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def square_signal(signal):
        """Square the amplitude of each sample in the signal (Task 2: 2.ii)"""
        result_samples = [s ** 2 for s in signal["samples"]]
        return {
            "indices": signal["indices"][:],
            "samples": result_samples,
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def normalize_signal(signal, target_range):
        """Normalize signal to target range (0 to 1 or -1 to 1) (Task 2: 2.iii)"""
        samples = np.array(signal["samples"])
        min_val = np.min(samples)
        max_val = np.max(samples)

        if max_val == min_val:
            result_samples = np.zeros_like(samples).tolist()
        else:
            scaled = (samples - min_val) / (max_val - min_val)

            if target_range == "0_to_1":
                result_samples = scaled.tolist()
            elif target_range == "-1_to_1":
                result_samples = (2 * scaled - 1).tolist()
            else:
                raise ValueError("Invalid target range for normalization.")

        return {
            "indices": signal["indices"][:],
            "samples": result_samples,
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"],
            "metadata": {
                "Normalization Range": target_range.replace('_', ' to '),
                "Original Min": min_val,
                "Original Max": max_val,
            }
        }

    @staticmethod
    def accumulate_signal(signal):
        """Perform discrete-time accumulation (running sum) (Task 2: 2.iv)"""
        samples = np.array(signal["samples"])
        result_samples = np.cumsum(samples).tolist()

        return {
            "indices": signal["indices"][:],
            "samples": result_samples,
            "signal_type": signal["signal_type"],
            "is_periodic": 0,
            "num_samples": signal["num_samples"]
        }


class SignalDataManager:
    """Manages signal data storage and retrieval"""

    def __init__(self):
        self.signals = []
        self.processor = SignalProcessor()

    def add_signal(self, signal_data, name="", filepath=""):
        """Add a signal to the data manager"""
        signal_data["name"] = name
        signal_data["filepath"] = filepath
        self.signals.append(signal_data)
        return len(self.signals) - 1  # Return index of added signal

    def get_signal(self, index):
        """Get signal by index"""
        if 0 <= index < len(self.signals):
            return self.signals[index]
        return None

    def get_all_signals(self):
        """Get all signals"""
        return self.signals

    def clear_signals(self):
        """Clear all signals"""
        self.signals = []

    def remove_signal(self, index):
        """Remove signal by index"""
        if 0 <= index < len(self.signals):
            return self.signals.pop(index)
        return None

    def get_signal_count(self):
        """Get total number of signals"""
        return len(self.signals)
