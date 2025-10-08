"""
Signal Processing Framework - Presentation Layer
Simple GUI with all required features (Task 2 Complete)
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# Add the parent directory to the path to import signal_reader
# This assumes signal_reader.py is in a 'Data' directory relative to this script's location
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Attempt to import SignalReader (assuming it's relative path setup works)
try:
    from Data.signal_reader import SignalReader
except ImportError:
    # Fallback import if the structure is flat (i.e., both files in the same dir)
    try:
        from signal_reader import SignalReader
    except ImportError:
        # If both attempts fail, create a mock class to allow the GUI to run/be debugged
        class MockSignalReader:
            def parse_signal_file(self, *args): raise NotImplementedError("SignalReader not found.")

            def calculate_statistics(self, *args): return {"min": 0, "max": 0, "mean": 0}

            def generate_sinusoidal(self, *args, **kwargs): raise NotImplementedError("SignalReader not found.")

            def add_signals(self, *args): raise NotImplementedError("SignalReader not found.")

            def subtract_signals(self, *args, **kwargs): raise NotImplementedError("SignalReader not found.")

            def multiply_signal(self, *args, **kwargs): raise NotImplementedError("SignalReader not found.")

            def square_signal(self, *args): raise NotImplementedError("SignalReader not found.")

            def normalize_signal(self, *args, **kwargs): raise NotImplementedError("SignalReader not found.")

            def accumulate_signal(self, *args): raise NotImplementedError("SignalReader not found.")


        SignalReader = MockSignalReader


class SignalProcessingGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Signal Processing Framework - Improved Interface")
        self.root.geometry("1500x900")  # Window size remains large

        # Data storage
        self.signals = []
        self.signal_reader = SignalReader()

        # State tracking for interaction modes
        self.panning = False
        self.pan_start = None
        # New state variables for axis-specific zooming
        self.zoom_mode_var = tk.StringVar(value="both")  # Options: "both", "x_only", "y_only"

        # Store initial axis limits for reset functionality
        self.initial_xlim = (None, None)
        self.initial_ylim = (None, None)

        # Bind the variable change to the status update function
        self.zoom_mode_var.trace_add("write", self.update_zoom_status)

        # Build interface
        self.create_menu()
        self.create_interface()

    def create_menu(self):
        """Create menu bar with features"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Signal", command=self.load_signal)
        file_menu.add_separator()
        file_menu.add_command(label="Clear All Signals", command=self.clear_signals)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Signal Generation Menu
        signal_gen_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Generation", menu=signal_gen_menu)
        signal_gen_menu.add_command(label="Sine Wave", command=lambda: self.show_sinusoidal_dialog(is_cosine=False))
        signal_gen_menu.add_command(label="Cosine Wave", command=lambda: self.show_sinusoidal_dialog(is_cosine=True))

        # Arithmetic Operations Menu
        arithmetic_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operations", menu=arithmetic_menu)
        arithmetic_menu.add_command(label="Addition (Multiple)", command=self.show_addition_dialog)
        arithmetic_menu.add_command(label="Subtraction (S1 - S2)", command=self.show_subtraction_dialog)
        arithmetic_menu.add_command(label="Multiplication (by Constant)", command=self.show_multiplication_dialog)
        arithmetic_menu.add_command(label="Squaring", command=self.show_squaring_dialog)
        arithmetic_menu.add_separator()
        arithmetic_menu.add_command(label="Normalization", command=self.show_normalization_dialog)
        arithmetic_menu.add_command(label="Accumulation", command=self.show_accumulation_dialog)

        # Display menu
        display_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Display/View", menu=display_menu)
        display_menu.add_command(label="Show Continuous", command=lambda: self.display_signal("continuous"))
        display_menu.add_command(label="Show Discrete", command=lambda: self.display_signal("discrete"))
        display_menu.add_separator()
        display_menu.add_command(label="Compare Two Signals", command=self.show_comparison_dialog)
        display_menu.add_command(label="Reset Zoom/Pan", command=self.reset_plot_view)

        # Removed explicit zoom commands from menu since we now use radio buttons in the interface
        # display_menu.add_separator()
        # display_menu.add_command(label="Set Zoom: X-Axis Only", command=lambda: self.zoom_mode_var.set("x_only"))
        # display_menu.add_command(label="Set Zoom: Y-Axis Only", command=lambda: self.zoom_mode_var.set("y_only"))
        # display_menu.add_command(label="Set Zoom: Both Axes", command=lambda: self.zoom_mode_var.set("both"))

    def create_interface(self):
        """Create main interface with modified layout and quick access buttons (without custom colors)."""

        # === Main content area ===
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === Left panel - Signal list and info (Fixed Width: 400px) ===
        left_frame = tk.Frame(content_frame, relief=tk.RIDGE, borderwidth=2, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # --- Loaded Signals section ---
        list_label = tk.Label(left_frame, text="Loaded Signals", font=("Arial", 12, "bold"))
        list_label.pack(pady=5)

        list_frame = tk.Frame(left_frame, height=200, relief=tk.SUNKEN, borderwidth=1)
        list_frame.pack(fill=tk.X, padx=5, pady=2)
        list_frame.pack_propagate(False)

        y_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.signal_listbox = tk.Listbox(
            list_frame,
            font=("Courier", 10),
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            height=8,
        )
        self.signal_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scrollbar.config(command=self.signal_listbox.yview)
        x_scrollbar.config(command=self.signal_listbox.xview)
        self.signal_listbox.config(width=0, exportselection=False)
        self.signal_listbox.bind('<<ListboxSelect>>', self.on_signal_select)

        # --- Signal Information section (Expands vertically) ---
        info_label = tk.Label(left_frame, text="Signal Statistics & Metadata", font=("Arial", 12, "bold"))
        info_label.pack(pady=5)

        info_frame = tk.Frame(left_frame, relief=tk.SUNKEN, borderwidth=1)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_scrollbar = tk.Scrollbar(info_frame)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.info_text = tk.Text(
            info_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            yscrollcommand=info_scrollbar.set,
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        info_scrollbar.config(command=self.info_text.yview)

        # === Right panel - Plot area (Display Section) ===
        right_frame = tk.Frame(content_frame, relief=tk.RIDGE, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Quick Access Buttons and Controls Section (Bigger) ---
        quick_access_frame = tk.Frame(right_frame, borderwidth=1, relief=tk.GROOVE, padx=10, pady=10)
        quick_access_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Row 1: File, Display, and Comparison
        row1_frame = tk.Frame(quick_access_frame)
        row1_frame.pack(fill=tk.X, pady=3)

        # Row 2: Operations
        row2_frame = tk.Frame(quick_access_frame)
        row2_frame.pack(fill=tk.X, pady=3)

        # Row 3: Zoom/View Controls & Reset
        row3_frame = tk.Frame(quick_access_frame)
        row3_frame.pack(fill=tk.X, pady=3)

        # List of quick access buttons with full words
        # Row 1 Buttons
        self._add_button(row1_frame, "Load Signal", self.load_signal)
        self._add_button(row1_frame, "Clear All", self.clear_signals)
        self._add_button(row1_frame, "Continuous Display", lambda: self.display_signal("continuous"))
        self._add_button(row1_frame, "Discrete Display", lambda: self.display_signal("discrete"))
        self._add_button(row1_frame, "Compare Signals", self.show_comparison_dialog)

        # Row 2 Buttons
        self._add_button(row2_frame, "Add Signals", self.show_addition_dialog)
        self._add_button(row2_frame, "Subtract Signals", self.show_subtraction_dialog)
        self._add_button(row2_frame, "Multiply by Const.", self.show_multiplication_dialog)
        self._add_button(row2_frame, "Square Signal", self.show_squaring_dialog)
        self._add_button(row2_frame, "Normalize Signal", self.show_normalization_dialog)
        self._add_button(row2_frame, "Accumulate Signal", self.show_accumulation_dialog)
        self._add_button(row2_frame, "Sine Wave Gen.", lambda: self.show_sinusoidal_dialog(is_cosine=False))

        # Row 3: Reset Button (Left) and Radio Buttons for Zoom Mode (Right)

        # Reset Button (Left)
        tk.Button(
            row3_frame,
            text="Reset View",
            command=self.reset_plot_view,
            width=17,
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
        ).pack(side=tk.LEFT, padx=3, pady=3)

        # Zoom Mode Radio Buttons (Right)
        zoom_frame = tk.LabelFrame(row3_frame, text="Mouse Wheel Zoom Mode", padx=5, pady=0)
        zoom_frame.pack(side=tk.LEFT, padx=10, pady=3, fill=tk.Y)

        tk.Radiobutton(zoom_frame, text="X-Axis Only", variable=self.zoom_mode_var, value="x_only",
                       indicatoron=0, width=12, font=("Arial", 8)).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Radiobutton(zoom_frame, text="Y-Axis Only", variable=self.zoom_mode_var, value="y_only",
                       indicatoron=0, width=12, font=("Arial", 8)).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Radiobutton(zoom_frame, text="Both Axes", variable=self.zoom_mode_var, value="both",
                       indicatoron=0, width=12, font=("Arial", 8)).pack(side=tk.LEFT, padx=2, pady=2)

        # ------------------------------------

        # Matplotlib figure setup
        self.fig = Figure(figsize=(9, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Mouse events (zoom & pan)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_wheel)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Initial plot setup
        self.ax.set_title("Signal Display Area - No Signal Loaded", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Sample Index (n)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.fig.tight_layout()
        self.canvas.draw()

        # Save initial limits
        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()

        # === Status bar ===
        self.status_label = tk.Label(self.root, text="Ready | Zoom Mode: Both Axes (Default)", relief=tk.SUNKEN,
                                     anchor=tk.W, font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _add_button(self, parent_frame, text, cmd):
        """Helper function to create a standardized button (monochrome, full word)."""
        button_width = 17
        tk.Button(
            parent_frame,
            text=text,
            command=cmd,
            width=button_width,
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
        ).pack(side=tk.LEFT, padx=3, pady=3)

    # --- Interaction Mode Control ---

    def update_zoom_status(self, *args):
        """Updates the status bar based on the current zoom mode without alerts."""
        mode = self.zoom_mode_var.get()
        if mode == "x_only":
            status_text = "X-Axis Only"
        elif mode == "y_only":
            status_text = "Y-Axis Only"
        else:
            status_text = "Both Axes (Default)"

        # Preserve the current status text (e.g., 'Displaying: Sine Wave')
        current_status = self.status_label.cget("text").split(" | Zoom Mode:")[0]
        if "Ready" not in current_status and "Displaying" not in current_status:
            current_status = "Ready"

        self.status_label.config(text=f"{current_status} | Zoom Mode: {status_text}")

    # --- Utility and Display Methods ---

    def load_signal(self):
        """Load signal from file"""
        file_path = filedialog.askopenfilename(
            title="Select Signal File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            # Initial directory hint (will likely need adjustment based on execution environment)
            initialdir=os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "signals")
        )

        if file_path:
            try:
                signal = self.signal_reader.parse_signal_file(file_path)
                signal["name"] = os.path.basename(file_path)
                signal["filepath"] = file_path
                self.signals.append(signal)
                self.update_signal_list()

                signal_type = "Time Domain" if signal["signal_type"] == 0 else "Frequency Domain"
                periodic = "Periodic" if signal["is_periodic"] == 1 else "Non-Periodic"

                self.status_label.config(text=f"Loaded: {signal['name']}")

                messagebox.showinfo("Signal Loaded",
                                    f"Signal: {signal['name']}\n"
                                    f"Type: {signal_type}\n"
                                    f"Periodic: {periodic}\n"
                                    f"Samples: {signal['num_samples']}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load signal:\n{str(e)}")
                self.status_label.config(text="Error loading signal")

    def clear_signals(self):
        """Clear all signals"""
        if self.signals:
            response = messagebox.askyesno("Clear Signals",
                                           "Are you sure you want to clear all signals?")
            if response:
                self.signals = []
                self.update_signal_list()
                self.info_text.delete(1.0, tk.END)

                self.ax.clear()
                self.ax.set_title("Signal Display Area - No Signal Loaded", fontsize=14, fontweight='bold')
                self.ax.set_xlabel("Sample Index (n)")
                self.ax.set_ylabel("Amplitude")
                self.ax.grid(True, linestyle='--', alpha=0.5)
                self.fig.tight_layout()
                self.canvas.draw()

                self.status_label.config(text="All signals cleared")
        else:
            messagebox.showinfo("Info", "No signals to clear")

    def update_signal_list(self):
        """Update signal listbox"""
        self.signal_listbox.delete(0, tk.END)

        for i, signal in enumerate(self.signals):
            type_char = "T" if signal["signal_type"] == 0 else "F"
            periodic_char = "P" if signal["is_periodic"] == 1 else "NP"
            display_text = f"{i + 1}. {signal['name']} [{type_char}-{periodic_char}, {signal['num_samples']} samples]"
            self.signal_listbox.insert(tk.END, display_text)

        self.status_label.config(text=f"Total signals: {len(self.signals)}")

    def on_signal_select(self, event):
        """
        Handle signal selection.
        Only displays information but does NOT auto-display the plot,
        as requested by the user.
        """
        selection = self.signal_listbox.curselection()
        if selection:
            index = selection[0]
            self.show_signal_info(index)
            # Removed: self.display_signal("discrete")

    def show_signal_info(self, index):
        """Display signal information (Updated to include metadata)"""
        self.info_text.delete(1.0, tk.END)

        if 0 <= index < len(self.signals):
            signal = self.signals[index]
            stats = self.signal_reader.calculate_statistics(signal["samples"])

            signal_type = "Time Domain" if signal["signal_type"] == 0 else "Frequency Domain"
            periodic = "Periodic" if signal["is_periodic"] == 1 else "Non-Periodic"

            info = f"Signal Name: {signal['name']}\n"
            info += f"{'=' * 45}\n"
            info += f"FILEPATH: {os.path.basename(signal['filepath']) or 'Generated'}\n"
            info += f"Source Type: {signal_type}\n"
            info += f"Periodicity: {periodic}\n"
            info += f"Total Samples: {signal['num_samples']}\n"
            info += f"Indices Labeled As: {signal.get('x_label', 'Sample Index (n)')}\n\n"

            # Include metadata for generated/processed signals
            if "metadata" in signal:
                info += "PROCESSING METADATA:\n"
                for key, value in signal["metadata"].items():
                    info += f"  - {key}: {value}\n"
                info += "\n"

            info += f"STATISTICAL SUMMARY:\n"
            info += f"  Minimum Amplitude: {stats['min']:.4f}\n"
            info += f"  Maximum Amplitude: {stats['max']:.4f}\n"
            info += f"  Mean Amplitude: {stats['mean']:.4f}\n\n"
            info += f"Sample Data (first 10 pairs):\n"
            info += f"{'Index':<12} {'Amplitude':<15}\n"
            info += f"{'-' * 27}\n"

            for i in range(min(10, len(signal["samples"]))):
                idx_display = f"{signal['indices'][i]:<12.4f}"
                info += f"{idx_display} {signal['samples'][i]:<15.4f}\n"

            if len(signal["samples"]) > 10:
                info += f"\n... showing 10 of {len(signal['samples'])} samples."

            self.info_text.insert(tk.END, info)

            # Do not update plot if a signal is selected (as requested)
            # if self.ax.get_title() == "Signal Display Area - No Signal Loaded":
            #     self.display_signal("discrete")

    def display_signal(self, mode):
        """Display selected signal in continuous or discrete mode, styled to match the image."""
        selection = self.signal_listbox.curselection()

        if not selection:
            messagebox.showwarning("Warning", "Please select a signal from the list")
            return

        index = selection[0]
        signal = self.signals[index]

        self.ax.clear()

        indices = np.array(signal["indices"])
        samples = np.array(signal["samples"])

        x_label = signal.get("x_label", "Sample Index (n)")

        if mode == "continuous":
            # Use black ('k') for continuous line
            self.ax.plot(indices, samples, 'k-', linewidth=2.5, label='Continuous Signal', alpha=0.8)
            title = f"Continuous Representation: {signal['name']}"

        elif mode == "discrete":
            # 1. Plot the dotted continuous line (like the photo)
            self.ax.plot(indices, samples, color='k', linestyle='--', linewidth=1.5, alpha=0.8,
                         label='Continuous Outline')

            # 2. Plot the discrete stems (blue lines)
            markerline, stemlines, baseline = self.ax.stem(
                indices, samples,
                linefmt='b-',  # Blue lines
                markerfmt='bo',  # Blue markers
                basefmt=" ",
                label='Discrete Samples',
                # Removed use_line_collection=True to fix rendering issue
            )
            # Apply styling to match the sample image's clear markers
            plt.setp(markerline, markersize=5, color='b')
            plt.setp(stemlines, linewidth=1.5, color='b', alpha=0.9)
            title = f"Discrete Representation: {signal['name']}"

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel("Amplitude x(n)", fontsize=12)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.7)
        self.ax.legend(loc='best', fontsize=10)  # Added legend for clarity

        # Adjust the axis limits slightly for padding
        y_padding = (np.max(samples) - np.min(samples)) * 0.1
        if y_padding == 0: y_padding = 1
        self.ax.set_ylim(np.min(samples) - y_padding, np.max(samples) + y_padding)

        self.fig.tight_layout()
        self.canvas.draw()

        # Update initial limits for reset functionality
        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()

        zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
        self.status_label.config(text=f"Displaying: {signal['name']} ({mode} mode) | Zoom Mode: {zoom_mode_text}")

    def reset_plot_view(self):
        """Resets the plot view to the initial zoom and pan state."""
        if not self.ax.has_data():
            messagebox.showinfo("Info", "No data loaded or plotted to reset view.")
            return

        self.ax.set_xlim(self.initial_xlim)
        self.ax.set_ylim(self.initial_ylim)
        self.canvas.draw_idle()
        zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
        self.status_label.config(text=f"Plot view reset | Zoom Mode: {zoom_mode_text}")

    # --- Task 2: Signal Generation Dialogs (Logic remains the same) ---

    def show_sinusoidal_dialog(self, is_cosine):
        """Show dialog for generating sine or cosine wave (Task 2: 1)"""
        wave_type = "Cosine" if is_cosine else "Sine"
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Generate {wave_type} Wave")
        dialog.geometry("400x450")

        tk.Label(dialog, text=f"Parameters for {wave_type} Wave", font=("Arial", 10, "bold")).pack(pady=10)

        params = [
            ("Amplitude (A):", 1.0, "amplitude_var"),
            ("Analog Frequency (F, Hz):", 1.0, "freq_var"),
            ("Phase Shift (theta, degrees):", 0.0, "phase_var"),
            ("Sampling Frequency (Fs, Hz):", 100.0, "sampling_freq_var"),
            ("Duration (seconds):", 1.0, "time_var"),
        ]

        vars_dict = {}
        for text, default, var_name in params:
            frame = tk.Frame(dialog)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=text, width=25, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            tk.Entry(frame, textvariable=var, width=15).pack(side=tk.RIGHT, expand=True)
            vars_dict[var_name] = var

        tk.Label(dialog, text="*Fs must obey Sampling Theorem (Fs > 2*F)", fg='red').pack(pady=5)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def generate():
            try:
                A = float(vars_dict["amplitude_var"].get())
                F = float(vars_dict["freq_var"].get())
                theta = float(vars_dict["phase_var"].get())
                Fs = float(vars_dict["sampling_freq_var"].get())
                T = float(vars_dict["time_var"].get())

                if Fs <= 0 or F <= 0 or T <= 0:
                    raise ValueError("Frequency, duration, and sampling rate must be positive.")

                result = self.signal_reader.generate_sinusoidal(
                    amplitude=A,
                    analog_freq_f=F,
                    phase_theta_deg=theta,
                    sampling_freq_fs=Fs,
                    is_cosine=is_cosine,
                    total_time_s=T
                )

                result["name"] = f"{wave_type}_{A}A_{F}F_{Fs}Fs.txt"
                result["filepath"] = ""
                result["x_label"] = "Time (s)"

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()

                messagebox.showinfo("Success", f"{wave_type} wave generated successfully. (Fs={Fs} > 2*F={2 * F})")
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(text=f"Generated: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except ValueError as e:
                messagebox.showerror("Error", f"Input Error:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Generation failed:\n{str(e)}")

        tk.Button(button_frame, text="Generate", command=generate, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    # --- Task 2: Arithmetic Operations Dialogs (Logic remains the same) ---

    def _show_single_signal_operation_dialog(self, title, operation_func):
        """Helper for simple operations (Squaring, Accumulation, etc.) on a single signal"""
        if not self.signals:
            messagebox.showwarning("Warning", f"No signals loaded for {title}")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("350x250")

        tk.Label(dialog, text=f"Select Signal for {title}", font=("Arial", 10, "bold")).pack(pady=10)

        tk.Label(dialog, text="Select Signal:").pack(pady=5)
        signal_combo = tk.Listbox(dialog, height=5, exportselection=False)
        signal_combo.pack(padx=10, pady=5, fill=tk.X)

        for i, signal in enumerate(self.signals):
            signal_combo.insert(tk.END, f"{i + 1}. {signal['name']}")

        def perform_operation():
            selected = signal_combo.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a signal")
                return

            try:
                signal = self.signals[selected[0]]
                result = operation_func(signal)

                result["name"] = f"{title}_{signal['name']}"
                result["filepath"] = ""

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()

                messagebox.showinfo("Success", f"Signal {title} successfully")
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(text=f"{title} complete: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except Exception as e:
                messagebox.showerror("Error", f"{title} failed:\n{str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Process", command=perform_operation, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_addition_dialog(self):
        """Show dialog for adding signals (Task 1)"""
        if len(self.signals) < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for addition")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Signals")
        dialog.geometry("400x400")

        tk.Label(dialog, text="Select Signals to Add", font=("Arial", 10, "bold")).pack(pady=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for i, signal in enumerate(self.signals):
            listbox.insert(tk.END, f"{i + 1}. {signal['name']}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def perform_addition():
            selected = listbox.curselection()
            if len(selected) < 2:
                messagebox.showwarning("Warning", "Select at least 2 signals")
                return

            try:
                signal_list = [self.signals[i] for i in selected]
                result = self.signal_reader.add_signals(signal_list)
                result["name"] = f"Addition_Result_{len(self.signals) + 1}.txt"

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()

                messagebox.showinfo("Success", f"Successfully added {len(selected)} signals")
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(text=f"Addition complete: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except Exception as e:
                print(e.with_traceback())
                # messagebox.showerror("Error", f"Addition failed:\n{str(e)}")

        tk.Button(button_frame, text="Add Selected Signals", command=perform_addition, width=20).pack(side=tk.LEFT,
                                                                                                      padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_subtraction_dialog(self):
        """Show dialog for subtracting two signals (Signal 1 - Signal 2) (Task 2: 2.i)"""
        if len(self.signals) < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for subtraction")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Subtract Signals (Signal 1 - Signal 2)")
        dialog.geometry("450x450")

        tk.Label(dialog, text="Select Signal 1 (Minuend) - Signal 2 (Subtrahend)", font=("Arial", 10, "bold")).pack(
            pady=10)

        tk.Label(dialog, text="Signal 1:").pack(pady=5)
        signal1_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal1_list.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(dialog, text="Signal 2:").pack(pady=5)
        signal2_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal2_list.pack(padx=10, pady=5, fill=tk.X)

        for i, signal in enumerate(self.signals):
            display_text = f"{i + 1}. {signal['name']}"
            signal1_list.insert(tk.END, display_text)
            signal2_list.insert(tk.END, display_text)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def perform_subtraction():
            sel1 = signal1_list.curselection()
            sel2 = signal2_list.curselection()

            if not sel1 or not sel2:
                messagebox.showwarning("Warning", "Select both signals")
                return
            if sel1[0] == sel2[0]:
                messagebox.showwarning("Warning", "Please select different signals")
                return

            sig1 = self.signals[sel1[0]]
            sig2 = self.signals[sel2[0]]

            try:
                result = self.signal_reader.subtract_signals(sig1, sig2)
                result["name"] = f"Subtraction_Result_S{sel1[0] + 1}_minus_S{sel2[0] + 1}"

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()

                messagebox.showinfo("Success", "Signals subtracted successfully")
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(text=f"Subtraction complete: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except Exception as e:
                messagebox.showerror("Error", f"Subtraction failed:\n{str(e)}")

        tk.Button(button_frame, text="Subtract", command=perform_subtraction, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_multiplication_dialog(self):
        """Show dialog for multiplying signal by a constant (Task 1)"""
        if not self.signals:
            messagebox.showwarning("Warning", "No signals loaded")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Multiply Signal")
        dialog.geometry("400x300")

        tk.Label(dialog, text="Multiply Signal by Constant", font=("Arial", 10, "bold")).pack(pady=10)

        tk.Label(dialog, text="Select Signal:").pack(pady=5)
        signal_combo = tk.Listbox(dialog, height=5, exportselection=False)
        signal_combo.pack(padx=10, pady=5, fill=tk.X)
        for i, signal in enumerate(self.signals):
            signal_combo.insert(tk.END, f"{i + 1}. {signal['name']}")

        tk.Label(dialog, text="Enter Constant:").pack(pady=5)
        constant_var = tk.StringVar(value="1.0")
        tk.Entry(dialog, textvariable=constant_var, width=20).pack(pady=5)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def perform_multiplication():
            selected = signal_combo.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a signal")
                return

            try:
                constant = float(constant_var.get())
                signal = self.signals[selected[0]]

                result = self.signal_reader.multiply_signal(signal, constant)
                result["name"] = f"Multiplied_{constant}x_{signal['name']}"

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(
                    text=f"Multiplication complete: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Multiplication failed:\n{str(e)}")

        tk.Button(button_frame, text="Multiply", command=perform_multiplication, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_squaring_dialog(self):
        """Show dialog for squaring a signal (Task 2: 2.ii)"""
        self._show_single_signal_operation_dialog(
            title="Squared",
            operation_func=self.signal_reader.square_signal
        )

    def show_accumulation_dialog(self):
        """Show dialog for accumulation of input signal (Task 2: 2.iv)"""
        self._show_single_signal_operation_dialog(
            title="Accumulation",
            operation_func=self.signal_reader.accumulate_signal
        )

    def show_normalization_dialog(self):
        """Show dialog for signal normalization (Task 2: 2.iii)"""
        if not self.signals:
            messagebox.showwarning("Warning", "No signals loaded for Normalization")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Normalization")
        dialog.geometry("350x380")

        tk.Label(dialog, text="Select Signal and Target Range", font=("Arial", 10, "bold")).pack(pady=10)

        tk.Label(dialog, text="Select Signal:").pack(pady=5)
        signal_combo = tk.Listbox(dialog, height=5, exportselection=False)
        signal_combo.pack(padx=10, pady=5, fill=tk.X)
        for i, signal in enumerate(self.signals):
            signal_combo.insert(tk.END, f"{i + 1}. {signal['name']}")

        tk.Label(dialog, text="Target Range:", font=("Arial", 9, "bold")).pack(pady=10)
        range_var = tk.StringVar(value="-1_to_1")
        tk.Radiobutton(dialog, text="Normalize from -1 to 1", variable=range_var, value="-1_to_1").pack()
        tk.Radiobutton(dialog, text="Normalize from 0 to 1", variable=range_var, value="0_to_1").pack()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def perform_normalization():
            selected = signal_combo.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Select a signal")
                return

            try:
                signal = self.signals[selected[0]]
                target_range = range_var.get()
                result = self.signal_reader.normalize_signal(signal, target_range)

                range_str = target_range.replace('_to_', 'T')
                result["name"] = f"Normalized_{range_str}_{signal['name']}"

                self.signals.append(result)
                self.update_signal_list()
                dialog.destroy()

                messagebox.showinfo("Success",
                                    f"Signal normalized to {target_range.replace('_to_', ' to ')} successfully")
                zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
                self.status_label.config(text=f"Normalization complete: {result['name']} | Zoom Mode: {zoom_mode_text}")

            except Exception as e:
                messagebox.showerror("Error", f"Normalization failed:\n{str(e)}")

        tk.Button(button_frame, text="Normalize", command=perform_normalization, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    # --- Comparison & Display (Monochrome styling) ---

    def show_comparison_dialog(self):
        """Show dialog for comparing two signals"""
        if len(self.signals) < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for comparison")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Two Signals")
        dialog.geometry("450x450")

        tk.Label(dialog, text="Select Two Signals to Compare",
                 font=("Arial", 10, "bold")).pack(pady=10)

        tk.Label(dialog, text="Signal 1:").pack(pady=5)
        signal1_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal1_list.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(dialog, text="Signal 2:").pack(pady=5)
        signal2_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal2_list.pack(padx=10, pady=5, fill=tk.X)

        for i, signal in enumerate(self.signals):
            display_text = f"{i + 1}. {signal['name']}"
            signal1_list.insert(tk.END, display_text)
            signal2_list.insert(tk.END, display_text)

        tk.Label(dialog, text="Display Mode:", font=("Arial", 9, "bold")).pack(pady=10)

        mode_var = tk.StringVar(value="discrete")  # Default to discrete mode for comparison

        mode_frame = tk.Frame(dialog)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Continuous", variable=mode_var,
                       value="continuous").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Discrete (Offset)", variable=mode_var,
                       value="discrete").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Combined", variable=mode_var,
                       value="both").pack(side=tk.LEFT, padx=10)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def compare_signals():
            sel1 = signal1_list.curselection()
            sel2 = signal2_list.curselection()

            if not sel1 or not sel2:
                messagebox.showwarning("Warning", "Select both signals")
                return

            if sel1[0] == sel2[0]:
                messagebox.showwarning("Warning", "Please select different signals")
                return

            self.display_two_signals(sel1[0], sel2[0], mode_var.get())
            dialog.destroy()

        tk.Button(button_frame, text="Compare",
                  command=compare_signals, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                  command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def display_two_signals(self, index1, index2, mode="discrete"):
        """Display two signals at the same time with offset for discrete mode, using default colors."""
        signal1 = self.signals[index1]
        signal2 = self.signals[index2]

        self.ax.clear()

        x_label = signal1.get("x_label", signal2.get("x_label", "Sample Index (n)"))

        def get_offset_indices(indices, offset_factor=0.01):
            """Applies a small offset to the indices for the second signal to prevent overlap"""
            if not indices: return indices
            indices_arr = np.array(indices)
            data_range = indices_arr[-1] - indices_arr[0] if len(indices_arr) > 1 else 1.0
            # Calculate a small, proportional offset
            offset = offset_factor * (data_range / len(indices_arr))
            return (indices_arr + offset).tolist()

        if mode == "continuous":
            # Signal 1 (Black line)
            self.ax.plot(signal1["indices"], signal1["samples"],
                         'k-', linewidth=2.5, label=signal1['name'], alpha=0.8)
            # Signal 2 (Red line - using red for contrast, as this is standard Matplotlib)
            self.ax.plot(signal2["indices"], signal2["samples"],
                         'r-', linewidth=2.5, label=signal2['name'], alpha=0.8)
            title = "Comparison - Continuous"

        elif mode == "discrete":
            # Signal 1: Plot the dotted continuous line (like the photo)
            self.ax.plot(signal1["indices"], signal1["samples"], color='k', linestyle='--', linewidth=1.5, alpha=0.8,
                         label=signal1['name'] + ' Outline')

            # Signal 1: Plot the discrete stems (blue lines)
            markerline1, stemlines1, baseline1 = self.ax.stem(
                signal1["indices"], signal1["samples"],
                linefmt='b-', markerfmt='bo', basefmt=" ", label=signal1['name'] + ' Samples',
                # Removed use_line_collection=True
            )
            plt.setp(markerline1, markersize=5, color='b')
            plt.setp(stemlines1, linewidth=1.5, color='b', alpha=0.9)

            # Signal 2: Plot the dotted continuous line (like the photo)
            self.ax.plot(signal2["indices"], signal2["samples"], color='r', linestyle='--', linewidth=1.5, alpha=0.8,
                         label=signal2['name'] + ' Outline')

            # Signal 2 (Red Stem, slightly offset for visual separation)
            indices2_offset = get_offset_indices(signal2["indices"])
            markerline2, stemlines2, baseline2 = self.ax.stem(
                indices2_offset, signal2["samples"],
                linefmt='r-', markerfmt='rs', basefmt=" ", label=signal2['name'] + ' Samples',
                # Removed use_line_collection=True
            )
            plt.setp(markerline2, markersize=5, color='r')
            plt.setp(stemlines2, linewidth=1.5, color='r', alpha=0.9)

            title = "Comparison - Discrete (Offset for Clarity)"

        elif mode == "both":
            # Signal 1 (Black Line and Stem)
            self.ax.plot(signal1["indices"], signal1["samples"],
                         'k-', linewidth=1.5, alpha=0.5, label=signal1['name'] + ' (Line)')
            # FIXED: Removed use_line_collection=True from stem plots
            markerline1, stemlines1, baseline1 = self.ax.stem(
                signal1["indices"], signal1["samples"],
                linefmt='k-', markerfmt='ko', basefmt=" ",
            )
            plt.setp(markerline1, markersize=5, color='k')

            # Signal 2 (Red Line and Stem)
            self.ax.plot(signal2["indices"], signal2["samples"],
                         'r-', linewidth=1.5, alpha=0.5, label=signal2['name'] + ' (Line)')
            indices2_offset = get_offset_indices(signal2["indices"])
            # FIXED: Removed use_line_collection=True from stem plots
            markerline2, stemlines2, baseline2 = self.ax.stem(
                indices2_offset, signal2["samples"],
                linefmt='r-', markerfmt='rs', basefmt=" ",
            )
            plt.setp(markerline2, markersize=5, color='r')

            title = "Comparison - Combined Continuous & Discrete"

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel("Amplitude", fontsize=12)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.7)
        self.ax.legend(loc='best', fontsize=10)

        # Recalculate and set initial limits
        all_samples = np.concatenate([signal1["samples"], signal2["samples"]])
        all_indices = np.concatenate([signal1["indices"], signal2["indices"]])

        y_padding = (np.max(all_samples) - np.min(all_samples)) * 0.1
        if y_padding == 0: y_padding = 1

        self.initial_xlim = (np.min(all_indices), np.max(all_indices))
        self.initial_ylim = (np.min(all_samples) - y_padding, np.max(all_samples) + y_padding)
        self.ax.set_xlim(self.initial_xlim)
        self.ax.set_ylim(self.initial_ylim)

        self.fig.tight_layout()
        self.canvas.draw()

        zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
        self.status_label.config(
            text=f"Comparing: {signal1['name']} vs {signal2['name']} ({mode} mode) | Zoom Mode: {zoom_mode_text}")

    # --- Interactive Mouse Functions (Zoom and Pan) ---

    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom in/out, respecting the zoom_mode."""
        if event.inaxes != self.ax: return

        # Get current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zoom_mode = self.zoom_mode_var.get()

        # Get mouse position
        xdata = event.xdata
        ydata = event.ydata

        # Zoom factor
        scale_factor = 0.8 if event.button == 'up' else 1.2 if event.button == 'down' else None
        if scale_factor is None: return

        new_xlim = list(xlim)
        new_ylim = list(ylim)

        # Calculate zoom based on current mode
        if zoom_mode in ["both", "x_only"]:
            if xlim[1] > xlim[0]:
                new_width = (xlim[1] - xlim[0]) * scale_factor
                relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
                new_xlim = [xdata - new_width * (1 - relx), xdata + new_width * relx]
            # Handle case where axis limits are zero/very small after aggressive zoom/data is static
            else:
                new_xlim = xlim

        if zoom_mode in ["both", "y_only"]:
            if ylim[1] > ylim[0]:
                new_height = (ylim[1] - ylim[0]) * scale_factor
                rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])
                new_ylim = [ydata - new_height * (1 - rely), ydata + new_height * rely]
            else:
                new_ylim = ylim

        # Apply new limits
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        # Redraw canvas
        self.canvas.draw_idle()

        # Update status
        zoom_level = "in" if event.button == 'up' else "out"
        zoom_mode_text = zoom_mode.replace('_', ' ').title()
        self.status_label.config(text=f"Zoomed {zoom_level} | Zoom Mode: {zoom_mode_text}")

    def on_mouse_press(self, event):
        """Handle mouse button press for panning (Left Click)"""
        if event.inaxes != self.ax or event.button != 1: return

        self.panning = True
        self.pan_start = (event.xdata, event.ydata)
        # Change cursor to hand
        self.canvas.get_tk_widget().config(cursor="fleur")
        zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
        self.status_label.config(text=f"Panning... (drag to move) | Zoom Mode: {zoom_mode_text}")

    def on_mouse_release(self, event):
        """Handle mouse button release"""
        if event.button == 1:
            self.panning = False
            self.pan_start = None
            # Reset cursor
            self.canvas.get_tk_widget().config(cursor="")
            zoom_mode_text = self.zoom_mode_var.get().replace('_', ' ').title()
            self.status_label.config(text=f"Ready | Zoom Mode: {zoom_mode_text}")

    def on_mouse_move(self, event):
        """Handle mouse motion for panning"""
        if not self.panning or not self.pan_start or event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        # Calculate how much to pan
        dx = self.pan_start[0] - event.xdata
        dy = self.pan_start[1] - event.ydata

        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Apply pan
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)

        # Redraw
        self.canvas.draw_idle()


def main():
    root = tk.Tk()
    app = SignalProcessingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
