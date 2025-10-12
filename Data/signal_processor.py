"""
Signal Processing Framework - Logic Layer
Enhanced with additional operations
"""

import numpy as np


class SignalProcessor:
    """Core signal processing operations"""

    @staticmethod
    def parse_signal_file(file_path):
        """
        file format:
        Line 1: Signal Type 0/Time or 1/Frequency
        Line 2: Periodicity (0/1)
        Line 3: Num Samples N
        Line 4+: Data (Index Amplitude)
        """
        try:
            with open(file_path, 'r') as file:  # 'r' read mode
                lines = [line.strip() for line in file.readlines() if line.strip()]  # load all file lines

            if len(lines) < 3:
                raise ValueError("File must have at least 4 lines")
            if len(lines[2]) == '0':
                raise ValueError("File hase no samples for the signal")

            # Parse header
            signal_type = int(lines[0])
            is_periodic = int(lines[1])
            num_samples_header = int(lines[2])

            indices = []
            samples = []

            # Parse data lines
            for i in range(3, min(3 + num_samples_header, len(lines))):
                parts = lines[i].split()

                if len(parts) >= 2:  # check it hase split correct
                    indices.append(float(parts[0]))
                    samples.append(float(parts[1]))

            # return Dictionary after filtering the data
            return {
                "indices": np.array(indices),
                "samples": np.array(samples),
                "signal_type": signal_type,
                "is_periodic": is_periodic,
                "num_samples": len(samples)
            }
        # for errors only 😑
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    @staticmethod
    def calculate_statistics(samples):
        """Calculate basic statistics"""

        if not samples.any():
            return {"min": 0, "max": 0, "mean": 0}

        return {
            "min": min(samples),
            "max": max(samples),
            "mean": sum(samples) / len(samples)
        }

    # Arithmetic Operations
    @staticmethod
    def add_signals(signals):
        """Add multiple signals (handles unequal lengths by zero-padding)"""
        if len(signals) < 2:
            raise ValueError("Need at least 2 signals to perform addition")

        # If signals have different indices, will take the max indices
        longest_indices = max(signals, key=lambda s: len(s["indices"]))["indices"]

        # Find the maximum signal sample length
        max_len = max(len(sig["samples"]) for sig in signals)

        result_samples = [0.0] * max_len
        # Perform addition with zero-padding
        for sig in signals:
            for i in range(max_len):
                if i < len(sig["samples"]):
                    result_samples[i] += sig["samples"][i]
                else:
                    result_samples[i] += 0  # Explicitly showing zero-padding

        # return the resulting signal dictionary
        return {
            "indices": np.array(longest_indices[:max_len]),
            "samples": np.array(result_samples),
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": max_len
        }

    @staticmethod
    def subtract_signals(signal1, signal2):
        """Subtract signal2 from signal1 with zero-padding for different lengths"""
        # Find maximum length
        max_len = max(len(signal1["samples"]), len(signal2["samples"]))

        # Use indices from longer signal
        longest_indices = max([signal1, signal2], key=lambda s: len(s["indices"]))["indices"][:max_len]

        # Perform subtraction with zero-padding
        result_samples = []
        for i in range(max_len):
            val1 = signal1["samples"][i] if i < len(signal1["samples"]) else 0.0
            val2 = signal2["samples"][i] if i < len(signal2["samples"]) else 0.0
            result_samples.append(val1 - val2)

        return {
            "indices": np.array(longest_indices),
            "samples": np.array(result_samples),
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": max_len
        }

    @staticmethod
    def multiply_signal(signal, constant):
        """Multiply signal by constant"""
        return {
            "indices": signal["indices"],
            "samples": signal['samples'] * constant,  # Multiply each sample with number
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"]
        }

    @staticmethod
    def square_signal(signal):
        """Square signal samples"""
        return {
            "indices": signal["indices"],
            "samples": signal["samples"] ** 2,  # square the sampels array
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

    # Signal Generation Methods
    @staticmethod
    def generate_sinusoidal(amplitude, analog_freq, phase_deg, sampling_freq, is_cosine=False):
        """Generate sine/cosine wave - phase input in DEGREES"""
        # Validate sampling theorem
        if sampling_freq <= 2 * analog_freq:
            raise ValueError(f"Sampling frequency must be > {2 * analog_freq} Hz")

        # Convert phase from degrees to radians
        phase_rad = phase_deg

        # Calculate number of samples for one second (standard practice)
        num_samples = int(sampling_freq)  # 1 second worth of samples

        # Create sample indices (0, 1, 2, ..., num_samples-1)
        indices = np.arange(num_samples)

        # Calculate time values for each sample
        t = indices / sampling_freq

        # Generate wave using numpy functions
        if is_cosine:
            samples = amplitude * np.cos(2 * np.pi * analog_freq * t + phase_rad)
        else:
            samples = amplitude * np.sin(2 * np.pi * analog_freq * t + phase_rad)

        return {
            "indices": indices,  # FIX: Use integer indices (0, 1, 2, ...) not time values
            "samples": samples,
            "signal_type": 0,
            "is_periodic": 1,
            "num_samples": num_samples,
            "x_label": "Sample Index (n)"
        }


class SignalDataManager:
    """Manages signal data storage"""

    def __init__(self):
        self.signals = []

    def add_signal(self, signal_data, name=""):
        """Add signal to manager"""
        signal_data["name"] = name
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

    def remove_signal(self, index):
        """Remove specific signal by index"""
        if 0 <= index < len(self.signals):
            removed_signal = self.signals.pop(index)
            return removed_signal
        return None

    def remove_signals(self, indices):
        """Remove multiple signals by indices (in descending order to avoid index shifting)"""
        # Sort indices in descending order to avoid index shifting during removal
        indices_sorted = sorted(indices, reverse=True)
        removed_signals = []

        for index in indices_sorted:
            if 0 <= index < len(self.signals):
                removed_signals.append(self.signals.pop(index))

        return removed_signals

    def get_signal_count(self):
        """Get signal count"""
        return len(self.signals)
