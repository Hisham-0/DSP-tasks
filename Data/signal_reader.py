"""
Signal Reader Module - Data Layer
Handles signal file parsing and data processing
"""
class SignalReader:
    """Class for reading and processing signal files"""

    @staticmethod
    def parse_signal_file(file_path):
        """
        Parse signal file according to the specified format

        Format:
        Line 1: Signal Type (0=Time Domain, 1=Frequency Domain)
        Line 2: Periodicity (0=Non-Periodic, 1=Periodic)
        Line 3: Number of Samples
        Line 4+: Data Values

        Args:
            file_path: Path to the signal file

        Returns:
            dict: Signal data dictionary
        """
        try:
            with open(file_path, 'r') as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]

            if len(lines) < 4:
                raise ValueError("File must have at least 4 lines")

            # Parse header
            signal_type = int(lines[0])  # 0=Time, 1=Frequency
            is_periodic = int(lines[1])  # 0=Non-periodic, 1=Periodic
            num_samples = int(lines[2])  # Number of samples

            if len(lines) != 3 + num_samples:
                raise ValueError(f"Expected {3 + num_samples} lines, got {len(lines)}")

            indices = []
            samples = []

            # Parse data lines (Time Domain: Index Amplitude)
            for i in range(3, 3 + num_samples):
                parts = lines[i].split()
                if len(parts) != 2:
                    raise ValueError(f"Line {i + 1}: Expected 2 values (Index Amplitude)")
                indices.append(float(parts[0]))
                samples.append(float(parts[1]))

            signal = {
                "indices": indices,
                "samples": samples,
                "signal_type": signal_type,
                "is_periodic": is_periodic,
                "num_samples": num_samples
            }

            return signal

        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")

    @staticmethod
    def add_signals(signal_list):
        """
        Add multiple signals together

        Args:
            signal_list: List of signal dictionaries

        Returns:
            dict: Resulting signal after addition
        """
        if len(signal_list) < 2:
            raise ValueError("Need at least 2 signals for addition")

        # Find common indices
        min_length = min(len(sig["samples"]) for sig in signal_list)

        result_indices = signal_list[0]["indices"][:min_length]
        result_samples = [0.0] * min_length

        # Add all signals
        for signal in signal_list:
            for i in range(min_length):
                result_samples[i] += signal["samples"][i]

        return {
            "indices": result_indices,
            "samples": result_samples,
            "signal_type": 0,
            "is_periodic": 0,
            "num_samples": min_length
        }

    @staticmethod
    def multiply_signal(signal, constant):
        """
        Multiply signal by a constant

        Args:
            signal: Signal dictionary
            constant: Multiplication constant

        Returns:
            dict: Resulting signal after multiplication
        """
        result_samples = [s * constant for s in signal["samples"]]

        return {
            "indices": signal["indices"][:],
            "samples": result_samples,
            "signal_type": signal["signal_type"],
            "is_periodic": signal["is_periodic"],
            "num_samples": signal["num_samples"]
        }

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