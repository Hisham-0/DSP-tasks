"""
Signal Processing Framework - Presentation Layer
Clean GUI implementation with radio button zoom controls
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# Import logic layer
try:
    from signal_processor import SignalProcessor, SignalDataManager
except ImportError:
    # Fallback for different project structure
    try:
        from Data.signal_processor import SignalProcessor, SignalDataManager
    except ImportError:
        # Mock classes if logic layer not found
        class SignalProcessor:
            @staticmethod
            def parse_signal_file(*args): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def calculate_statistics(*args): return {"min": 0, "max": 0, "mean": 0}
            @staticmethod
            def generate_sinusoidal(*args, **kwargs): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def add_signals(*args): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def subtract_signals(*args, **kwargs): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def multiply_signal(*args, **kwargs): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def square_signal(*args): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def normalize_signal(*args, **kwargs): raise NotImplementedError("SignalProcessor not found")
            @staticmethod
            def accumulate_signal(*args): raise NotImplementedError("SignalProcessor not found")

        class SignalDataManager:
            def __init__(self): self.signals = []
            def add_signal(self, *args): pass
            def get_signal(self, index): return None
            def get_all_signals(self): return []
            def clear_signals(self): pass
            def remove_signal(self, index): return None
            def get_signal_count(self): return 0


class SignalProcessingGUI:
    """Main GUI class - Handles only presentation and user interaction"""

    def __init__(self, root):
        self.root = root
        self.root.title("Signal Processing Framework")
        self.root.geometry("1500x900")

        # Initialize data manager (separated logic)
        self.data_manager = SignalDataManager()

        # GUI state variables
        self.panning = False
        self.pan_start = None
        self.zoom_mode_var = tk.StringVar(value="both")
        self.initial_xlim = (None, None)
        self.initial_ylim = (None, None)

        # Build interface
        self.create_menu()
        self.create_interface()

    # ===== MENU CREATION =====
    def create_menu(self):
        """Create main application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu - UPDATED
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Signal", command=self.load_signal)
        file_menu.add_separator()
        file_menu.add_command(label="Delete Selected Signal", command=self.delete_signal)
        file_menu.add_command(label="Delete All Signals", command=self.delete_all_signals)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Signal Generation Menu (unchanged)
        signal_gen_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Generation", menu=signal_gen_menu)
        signal_gen_menu.add_command(label="Sine Wave",
                                    command=lambda: self.show_sinusoidal_dialog(is_cosine=False))
        signal_gen_menu.add_command(label="Cosine Wave",
                                    command=lambda: self.show_sinusoidal_dialog(is_cosine=True))

        # Operations Menu (unchanged)
        operations_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Operations", menu=operations_menu)
        operations_menu.add_command(label="Addition", command=self.show_addition_dialog)
        operations_menu.add_command(label="Subtraction", command=self.show_subtraction_dialog)
        operations_menu.add_command(label="Multiplication", command=self.show_multiplication_dialog)
        operations_menu.add_command(label="Squaring", command=self.show_squaring_dialog)
        operations_menu.add_separator()
        operations_menu.add_command(label="Normalization", command=self.show_normalization_dialog)
        operations_menu.add_command(label="Accumulation", command=self.show_accumulation_dialog)

        # Display Menu (unchanged)
        display_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Display", menu=display_menu)
        display_menu.add_command(label="Show Continuous",
                                 command=lambda: self.display_signal("continuous"))
        display_menu.add_command(label="Show Discrete",
                                 command=lambda: self.display_signal("discrete"))
        display_menu.add_separator()
        display_menu.add_command(label="Compare Signals", command=self.show_comparison_dialog)
        display_menu.add_command(label="Reset View", command=self.reset_plot_view)

    # ===== INTERFACE CREATION =====
    def create_interface(self):
        """Create main GUI interface"""
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Panel - Signal Management
        self.create_left_panel(content_frame)

        # Right Panel - Plot Area
        self.create_right_panel(content_frame)

        # Status Bar
        self.create_status_bar()

    def create_left_panel(self, parent):
        """Create left panel with signal list and information"""
        left_frame = tk.Frame(parent, relief=tk.RIDGE, borderwidth=2, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # Signal List Section
        list_label = tk.Label(left_frame, text="Loaded Signals", font=("Arial", 12, "bold"))
        list_label.pack(pady=5)

        list_frame = tk.Frame(left_frame, height=200, relief=tk.SUNKEN, borderwidth=1)
        list_frame.pack(fill=tk.X, padx=5, pady=2)
        list_frame.pack_propagate(False)

        # Scrollbars for signal list
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
        self.signal_listbox.bind('<<ListboxSelect>>', self.on_signal_select)

        y_scrollbar.config(command=self.signal_listbox.yview)
        x_scrollbar.config(command=self.signal_listbox.xview)

        # Quick Operations Section
        operations_label = tk.Label(left_frame, text="Quick Operations", font=("Arial", 12, "bold"))
        operations_label.pack(pady=5)

        operations_frame = tk.Frame(left_frame, relief=tk.SUNKEN, borderwidth=1)
        operations_frame.pack(fill=tk.X, padx=5, pady=5)

        # Operation buttons in grid
        operations = [
            ("Add Signals", self.show_addition_dialog),
            ("Subtract", self.show_subtraction_dialog),
            ("Multiply", self.show_multiplication_dialog),
            ("Square", self.show_squaring_dialog),
            ("Normalize", self.show_normalization_dialog),
            ("Accumulate", self.show_accumulation_dialog),
            ("Sine Gen", lambda: self.show_sinusoidal_dialog(False)),
            ("Cosine Gen", lambda: self.show_sinusoidal_dialog(True)),
        ]

        for i, (text, command) in enumerate(operations):
            row = i // 2
            col = i % 2
            btn = tk.Button(
                operations_frame,
                text=text,
                command=command,
                width=15,
                height=2,
                font=("Arial", 9, "bold"),
                relief=tk.RAISED
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

        operations_frame.columnconfigure(0, weight=1)
        operations_frame.columnconfigure(1, weight=1)

        # Signal Information Section
        info_label = tk.Label(left_frame, text="Signal Information", font=("Arial", 12, "bold"))
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

    def create_right_panel(self, parent):
        """Create right panel with plot area and controls"""
        right_frame = tk.Frame(parent, relief=tk.RIDGE, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Quick Access Controls
        self.create_quick_access_controls(right_frame)

        # Matplotlib Plot Area
        self.fig = Figure(figsize=(9, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Setup mouse interactions
        self.setup_mouse_interactions()

        # Initial plot setup
        self.setup_initial_plot()

    def create_quick_access_controls(self, parent):
        """Create quick access button controls with radio button zoom"""
        control_frame = tk.Frame(parent, borderwidth=1, relief=tk.GROOVE, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Row 1 buttons - File and Display operations - UPDATED
        row1 = tk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=3)

        # Row 2 buttons - Signal operations
        row2 = tk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=3)

        # Row 3 - Zoom mode radio buttons
        row3 = tk.Frame(control_frame)
        row3.pack(fill=tk.X, pady=3)

        # Button definitions for row 1 - UPDATED
        row1_buttons = [
            ("Load Signal", self.load_signal),
            ("Delete Selected", self.delete_signal),  # CHANGED FROM "Clear All"
            ("Continuous", lambda: self.display_signal("continuous")),
            ("Discrete", lambda: self.display_signal("discrete")),
            ("Compare", self.show_comparison_dialog),
            ("Reset View", self.reset_plot_view),
        ]

        # Button definitions for row 2 (unchanged)
        row2_buttons = [
            ("Add Signals", self.show_addition_dialog),
            ("Subtract", self.show_subtraction_dialog),
            ("Multiply", self.show_multiplication_dialog),
            ("Square", self.show_squaring_dialog),
            ("Normalize", self.show_normalization_dialog),
            ("Accumulate", self.show_accumulation_dialog),
        ]

        # Create buttons for row 1 and 2
        for text, cmd in row1_buttons:
            self.create_control_button(row1, text, cmd, width=12)

        for text, cmd in row2_buttons:
            self.create_control_button(row2, text, cmd, width=12)

        # Create zoom mode radio buttons in row 3
        self.create_zoom_radio_buttons(row3)

    def create_zoom_radio_buttons(self, parent):
        """Create radio buttons for zoom mode selection"""
        # Create a labeled frame for zoom controls
        zoom_frame = tk.LabelFrame(parent, text="Mouse Wheel Zoom Mode",
                                  font=("Arial", 9, "bold"), padx=10, pady=5)
        zoom_frame.pack(fill=tk.X, pady=5)

        # Create radio buttons
        self.zoom_both = tk.Radiobutton(
            zoom_frame,
            text="Both Axes",
            variable=self.zoom_mode_var,
            value="both",
            font=("Arial", 9),
            command=lambda: self.set_zoom_mode('both')
        )
        self.zoom_both.pack(side=tk.LEFT, padx=15, pady=2)

        self.zoom_x_only = tk.Radiobutton(
            zoom_frame,
            text="X-Axis Only",
            variable=self.zoom_mode_var,
            value="x_only",
            font=("Arial", 9),
            command=lambda: self.set_zoom_mode('x_only')
        )
        self.zoom_x_only.pack(side=tk.LEFT, padx=15, pady=2)

        self.zoom_y_only = tk.Radiobutton(
            zoom_frame,
            text="Y-Axis Only",
            variable=self.zoom_mode_var,
            value="y_only",
            font=("Arial", 9),
            command=lambda: self.set_zoom_mode('y_only')
        )
        self.zoom_y_only.pack(side=tk.LEFT, padx=15, pady=2)

        # Set default selection
        self.zoom_mode_var.set("both")

    def create_control_button(self, parent, text, command, width=10):
        """Helper to create standardized control buttons"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
        )
        btn.pack(side=tk.LEFT, padx=3, pady=3)
        return btn

    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_label = tk.Label(
            self.root,
            text="Ready | Zoom Mode: Both Axes",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_mouse_interactions(self):
        """Setup mouse event handlers for plot interaction"""
        self.canvas.mpl_connect('scroll_event', self.on_mouse_wheel)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def setup_initial_plot(self):
        """Setup initial empty plot"""
        self.ax.set_title("Signal Display Area - No Signal Loaded", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Sample Index (n)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.fig.tight_layout()
        self.canvas.draw()

        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()

    # ===== ZOOM AND INTERACTION METHODS =====
    def set_zoom_mode(self, mode):
        """Set current zoom mode"""
        self.zoom_mode_var.set(mode)
        mode_display = {
            'both': 'Both Axes',
            'x_only': 'X-Axis Only',
            'y_only': 'Y-Axis Only'
        }
        self.update_status(f"Zoom mode set to: {mode_display[mode]}")

    def update_status(self, message):
        """Update status bar with message"""
        mode_display = self.zoom_mode_var.get().replace('_', ' ').title()
        self.status_label.config(text=f"{message} | Zoom Mode: {mode_display}")

    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom with axis-specific control"""
        if event.inaxes != self.ax:
            return

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zoom_mode = self.zoom_mode_var.get()

        scale_factor = 0.8 if event.button == 'up' else 1.2
        xdata, ydata = event.xdata, event.ydata

        new_xlim, new_ylim = list(xlim), list(ylim)

        # Apply zoom based on mode
        if zoom_mode in ["both", "x_only"] and xlim[1] > xlim[0]:
            new_width = (xlim[1] - xlim[0]) * scale_factor
            relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
            new_xlim = [xdata - new_width * (1 - relx), xdata + new_width * relx]

        if zoom_mode in ["both", "y_only"] and ylim[1] > ylim[0]:
            new_height = (ylim[1] - ylim[0]) * scale_factor
            rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])
            new_ylim = [ydata - new_height * (1 - rely), ydata + new_height * rely]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()

        zoom_level = "in" if event.button == 'up' else "out"
        self.update_status(f"Zoomed {zoom_level}")

    def on_mouse_press(self, event):
        """Start panning on left mouse button press"""
        if event.inaxes != self.ax or event.button != 1:
            return

        self.panning = True
        self.pan_start = (event.xdata, event.ydata)
        self.canvas.get_tk_widget().config(cursor="fleur")
        self.update_status("Panning... (drag to move)")

    def on_mouse_release(self, event):
        """Stop panning on mouse button release"""
        if event.button == 1:
            self.panning = False
            self.pan_start = None
            self.canvas.get_tk_widget().config(cursor="")
            self.update_status("Ready")

    def on_mouse_move(self, event):
        """Handle mouse movement for panning"""
        if not self.panning or not self.pan_start or event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        dx = self.pan_start[0] - event.xdata
        dy = self.pan_start[1] - event.ydata

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
        self.canvas.draw_idle()

    # ===== SIGNAL MANAGEMENT METHODS =====
    def load_signal(self):
        """Load signal from file"""
        file_path = filedialog.askopenfilename(
            title="Select Signal File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "signals")
        )

        if file_path:
            try:
                signal_data = SignalProcessor.parse_signal_file(file_path) # call method to hande the file
                signal_name = os.path.basename(file_path)

                self.data_manager.add_signal(signal_data, signal_name, file_path)
                self.update_signal_list()

                # Show success message
                signal_type = "Time Domain" if signal_data["signal_type"] == 0 else "Frequency Domain"
                periodic = "Periodic" if signal_data["is_periodic"] == 1 else "Non-Periodic"

                messagebox.showinfo("Signal Loaded",
                                  f"Signal: {signal_name}\n"
                                  f"Type: {signal_type}\n"
                                  f"Periodic: {periodic}\n"
                                  f"Samples: {signal_data['num_samples']}")

                self.update_status(f"Loaded: {signal_name}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load signal:\n{str(e)}")
                self.update_status("Error loading signal")

    #
    #
    #
    def delete_signal(self):
        """Delete selected signal(s) from the list"""
        if self.data_manager.get_signal_count() == 0:
            messagebox.showinfo("Info", "No signals to delete")
            return

        # Get current selection
        selected_indices = self.signal_listbox.curselection()

        if not selected_indices:
            messagebox.showwarning("Warning",
                                   "Please select one or more signals to delete.\n\n"
                                   "Tip: Use Ctrl+Click to select multiple signals")
            return

        # Create confirmation message
        if len(selected_indices) == 1:
            signal = self.data_manager.get_signal(selected_indices[0])
            message = f"Are you sure you want to delete signal:\n'{signal['name']}'?"
        else:
            message = f"Are you sure you want to delete {len(selected_indices)} selected signals?"

        # Ask for confirmation
        response = messagebox.askyesno("Delete Signals", message)

        if response:
            # Remove the selected signals
            removed_signals = self.data_manager.remove_signals(selected_indices)

            # Update the display
            self.update_signal_list()
            self.info_text.delete(1.0, tk.END)

            # Reset plot if no signals left, otherwise keep current display
            if self.data_manager.get_signal_count() == 0:
                self.setup_initial_plot()
            else:
                # Redraw the plot to remove deleted signals
                self.redraw_current_plot()

            # Show success message
            if len(removed_signals) == 1:
                self.update_status(f"Deleted signal: {removed_signals[0]['name']}")
            else:
                self.update_status(f"Deleted {len(removed_signals)} signals")

    def delete_all_signals(self):
        """Delete all signals (alternative to clear_signals)"""
        if self.data_manager.get_signal_count() > 0:
            response = messagebox.askyesno("Delete All Signals",
                                           "Are you sure you want to delete ALL signals?")
            if response:
                self.data_manager.clear_signals()
                self.update_signal_list()
                self.info_text.delete(1.0, tk.END)
                self.setup_initial_plot()
                self.update_status("All signals deleted")
        else:
            messagebox.showinfo("Info", "No signals to delete")

    def redraw_current_plot(self):
        """Redraw the current plot after deletion"""
        if not self.ax.has_data():
            self.setup_initial_plot()
            return

        # Get the current title to determine what was being displayed
        current_title = self.ax.get_title()

        # Clear and set up basic plot structure
        self.ax.clear()
        self.ax.set_title(current_title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Sample Index (n)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.7)

        self.fig.tight_layout()
        self.canvas.draw()

    #
    #
    #
    def update_signal_list(self):
        """Update the signal listbox display"""
        self.signal_listbox.delete(0, tk.END)

        for i, signal in enumerate(self.data_manager.get_all_signals()):
            type_char = "T" if signal["signal_type"] == 0 else "F"
            periodic_char = "P" if signal["is_periodic"] == 1 else "NP"
            display_text = f"{i+1}. {signal['name']} [{type_char}-{periodic_char}, {signal['num_samples']} samples]"
            self.signal_listbox.insert(tk.END, display_text)

        self.update_status(f"Total signals: {self.data_manager.get_signal_count()}")

    def on_signal_select(self, event):
        """Handle signal selection in listbox"""
        selection = self.signal_listbox.curselection()
        if selection:
            self.show_signal_info(selection[0])

    def show_signal_info(self, index):
        """Display detailed information about selected signal"""
        self.info_text.delete(1.0, tk.END)

        signal = self.data_manager.get_signal(index)
        if not signal:
            return

        stats = SignalProcessor.calculate_statistics(signal["samples"])
        signal_type = "Time Domain" if signal["signal_type"] == 0 else "Frequency Domain"
        periodic = "Periodic" if signal["is_periodic"] == 1 else "Non-Periodic"

        info = f"Signal Name: {signal['name']}\n"
        info += f"{'='*45}\n"
        info += f"Source: {os.path.basename(signal.get('filepath', 'Generated'))}\n"
        info += f"Type: {signal_type}\n"
        info += f"Periodicity: {periodic}\n"
        info += f"Samples: {signal['num_samples']}\n"
        info += f"X-Axis: {signal.get('x_label', 'Sample Index (n)')}\n\n"

        # Show metadata if available
        if "metadata" in signal:
            info += "PROCESSING METADATA:\n"
            for key, value in signal["metadata"].items():
                info += f"  - {key}: {value}\n"
            info += "\n"

        info += "STATISTICS:\n"
        info += f"  Min: {stats['min']:.4f}\n"
        info += f"  Max: {stats['max']:.4f}\n"
        info += f"  Mean: {stats['mean']:.4f}\n\n"

        info += "SAMPLE DATA (first 10):\n"
        info += f"{'Index':<12} {'Amplitude':<15}\n"
        info += f"{'-'*27}\n"

        for i in range(min(15, len(signal["samples"]))):
            info += f"{signal['indices'][i]:<12.4f} {signal['samples'][i]:<15.4f}\n"

        if len(signal["samples"]) > 15:
            info += f"\n... showing 15 of {len(signal['samples'])} samples."

        self.info_text.insert(tk.END, info)



    # ===== PLOT DISPLAY METHODS =====
    def display_signal(self, mode):
        """Display selected signal in specified mode"""
        selection = self.signal_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a signal from the list")
            return

        signal = self.data_manager.get_signal(selection[0])
        if not signal:
            return

        self.ax.clear()
        indices = np.array(signal["indices"])
        samples = np.array(signal["samples"])

        x_label = signal.get("x_label", "Sample Index (n)")

        if mode == "continuous":
            self.ax.plot(indices, samples, 'k-', linewidth=2.5, alpha=0.8)
            title = f"Continuous: {signal['name']}"

        elif mode == "discrete":
            # Plot dotted continuous line
            self.ax.plot(indices, samples, color='k', linestyle='--', linewidth=1.5, alpha=0.8)

            # Plot discrete stems
            markerline, stemlines, baseline = self.ax.stem(
                indices, samples,
                linefmt='b-', markerfmt='bo', basefmt=" ",
            )
            plt.setp(markerline, markersize=5, color='b')
            plt.setp(stemlines, linewidth=1.5, color='b', alpha=0.9)
            title = f"Discrete: {signal['name']}"

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel("Amplitude x(n)", fontsize=12)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.7)

        # Set appropriate axis limits
        y_padding = (np.max(samples) - np.min(samples)) * 0.1
        if y_padding == 0:
            y_padding = 1
        self.ax.set_ylim(np.min(samples) - y_padding, np.max(samples) + y_padding)

        self.fig.tight_layout()
        self.canvas.draw()

        # Save current limits for reset
        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()

        self.update_status(f"Displaying: {signal['name']} ({mode} mode)")

    def reset_plot_view(self):
        """Reset plot to initial zoom state"""
        if not self.ax.has_data():
            messagebox.showinfo("Info", "No data to reset")
            return

        self.ax.set_xlim(self.initial_xlim)
        self.ax.set_ylim(self.initial_ylim)
        self.canvas.draw_idle()
        self.update_status("Plot view reset")

    # ===== DIALOG METHODS =====
    def show_sinusoidal_dialog(self, is_cosine):
        """Show dialog for generating sine/cosine waves"""
        wave_type = "Cosine" if is_cosine else "Sine"
        dialog = SinusoidalDialog(self.root, wave_type, self)
        dialog.show()

    def show_addition_dialog(self):
        """Show dialog for adding signals"""
        if self.data_manager.get_signal_count() < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for addition")
            return
        dialog = OperationDialog(self.root, "Add Signals", self, "addition")
        dialog.show()

    def show_subtraction_dialog(self):
        """Show dialog for subtracting signals"""
        if self.data_manager.get_signal_count() < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for subtraction")
            return
        dialog = OperationDialog(self.root, "Subtract Signals", self, "subtraction")
        dialog.show()

    def show_multiplication_dialog(self):
        """Show dialog for multiplying signal by constant"""
        if self.data_manager.get_signal_count() < 1:
            messagebox.showwarning("Warning", "No signals loaded")
            return
        dialog = OperationDialog(self.root, "Multiply Signal", self, "multiplication")
        dialog.show()

    def show_squaring_dialog(self):
        """Show dialog for squaring signal"""
        self._show_single_operation_dialog("Square Signal", "squaring")

    def show_normalization_dialog(self):
        """Show dialog for normalizing signal"""
        self._show_single_operation_dialog("Normalize Signal", "normalization")

    def show_accumulation_dialog(self):
        """Show dialog for accumulating signal"""
        self._show_single_operation_dialog("Accumulate Signal", "accumulation")

    def _show_single_operation_dialog(self, title, operation_type):
        """Helper for single-signal operations"""
        if self.data_manager.get_signal_count() < 1:
            messagebox.showwarning("Warning", f"No signals loaded for {title}")
            return
        dialog = OperationDialog(self.root, title, self, operation_type)
        dialog.show()

    def show_comparison_dialog(self):
        """Show dialog for comparing two signals"""
        if self.data_manager.get_signal_count() < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for comparison")
            return
        dialog = ComparisonDialog(self.root, self)
        dialog.show()


    # ===== OPERATION EXECUTION METHODS =====
    def execute_operation(self, operation_type, **kwargs):
        """Execute signal processing operation and handle results"""
        try:
            result = None

            if operation_type == "sinusoidal":
                # Extract parameters for sinusoidal generation
                amplitude = kwargs.get('amplitude', 1.0)
                analog_freq = kwargs.get('analog_freq', 1.0)  # Fixed parameter name
                phase_deg = kwargs.get('phase_deg', 0.0)  # Fixed parameter name
                sampling_freq = kwargs.get('sampling_freq', 100.0)  # Fixed parameter name
                is_cosine = kwargs.get('is_cosine', False)
                duration = kwargs.get('duration', 1.0)  # Fixed parameter name

                result = SignalProcessor.generate_sinusoidal(
                    amplitude=amplitude,
                    analog_freq=analog_freq,  # Match parameter names in SignalProcessor
                    phase_deg=phase_deg,
                    sampling_freq=sampling_freq,
                    is_cosine=is_cosine,
                    duration=duration
                )

                wave_type = "Cosine" if is_cosine else "Sine"
                name = f"{wave_type}_{amplitude}A_{analog_freq}F_{sampling_freq}Fs"
                self.data_manager.add_signal(result, name)

            elif operation_type == "addition":
                signals = [self.data_manager.get_signal(i) for i in kwargs['signal_indices']]
                result = SignalProcessor.add_signals(signals)
                self.data_manager.add_signal(result, f"Addition_Result")

            elif operation_type == "subtraction":
                sig1 = self.data_manager.get_signal(kwargs['signal1_index'])
                sig2 = self.data_manager.get_signal(kwargs['signal2_index'])
                result = SignalProcessor.subtract_signals(sig1, sig2)
                self.data_manager.add_signal(result, f"Subtraction_Result")

            elif operation_type == "multiplication":
                signal = self.data_manager.get_signal(kwargs['signal_index'])
                result = SignalProcessor.multiply_signal(signal, kwargs['constant'])
                self.data_manager.add_signal(result, f"Multiplied_{kwargs['constant']}x")

            elif operation_type == "squaring":
                signal = self.data_manager.get_signal(kwargs['signal_index'])
                result = SignalProcessor.square_signal(signal)
                self.data_manager.add_signal(result, f"Squared_{signal['name']}")

            elif operation_type == "normalization":
                signal = self.data_manager.get_signal(kwargs['signal_index'])
                result = SignalProcessor.normalize_signal(signal, kwargs['target_range'])
                self.data_manager.add_signal(result, f"Normalized_{signal['name']}")

            elif operation_type == "accumulation":
                signal = self.data_manager.get_signal(kwargs['signal_index'])
                result = SignalProcessor.accumulate_signal(signal)
                self.data_manager.add_signal(result, f"Accumulated_{signal['name']}")

            if result:
                self.update_signal_list()
                messagebox.showinfo("Success", "Operation completed successfully")
                self.update_status(f"{operation_type.title()} operation completed")
                return True

        except Exception as e:
            messagebox.showerror("Error", f"Operation failed:\n{str(e)}")
            self.update_status(f"Error in {operation_type} operation")

        return False

    def display_two_signals(self, index1, index2, mode="discrete"):
        """Display two signals for comparison"""
        sig1 = self.data_manager.get_signal(index1)
        sig2 = self.data_manager.get_signal(index2)

        if not sig1 or not sig2:
            return

        self.ax.clear()
        x_label = sig1.get("x_label", "Sample Index (n)")

        if mode == "continuous":
            self.ax.plot(sig1["indices"], sig1["samples"], 'k-', linewidth=2.5, label=sig1['name'])
            self.ax.plot(sig2["indices"], sig2["samples"], 'r-', linewidth=2.5, label=sig2['name'])

        elif mode == "discrete":
            # Signal 1 with blue stems
            self.ax.plot(sig1["indices"], sig1["samples"], 'k--', linewidth=1.5, alpha=0.8)
            markerline1, stemlines1, _ = self.ax.stem(sig1["indices"], sig1["samples"],
                                                    linefmt='b-', markerfmt='bo', basefmt=" ")
            plt.setp(markerline1, markersize=5, color='b')
            plt.setp(stemlines1, linewidth=1.5, color='b', alpha=0.9)

            # Signal 2 with red stems (offset)
            offset_indices = np.array(sig2["indices"]) + 0.01
            self.ax.plot(offset_indices, sig2["samples"], 'k--', linewidth=1.5, alpha=0.8)
            markerline2, stemlines2, _ = self.ax.stem(offset_indices, sig2["samples"],
                                                    linefmt='r-', markerfmt='rs', basefmt=" ")
            plt.setp(markerline2, markersize=5, color='r')
            plt.setp(stemlines2, linewidth=1.5, color='r', alpha=0.9)

        self.ax.set_title(f"Comparison: {sig1['name']} vs {sig2['name']}", fontsize=14, fontweight='bold')
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel("Amplitude", fontsize=12)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.legend(loc='best', fontsize=10)

        self.fig.tight_layout()
        self.canvas.draw()
        self.update_status(f"Comparing: {sig1['name']} vs {sig2['name']}")


# ===== DIALOG CLASSES =====
class SinusoidalDialog:
    """Dialog for generating sinusoidal signals"""

    def __init__(self, parent, wave_type, gui):
        self.parent = parent
        self.wave_type = wave_type
        self.gui = gui
        self.dialog = None

    def show(self):
        """Show the dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Generate {self.wave_type} Wave")
        self.dialog.geometry("400x450")
        self.dialog.transient(self.parent)  # Set to be on top of the main window
        self.dialog.grab_set()  # Modal

        tk.Label(self.dialog, text=f"Parameters for {self.wave_type} Wave",
                font=("Arial", 10, "bold")).pack(pady=10)

        # Parameter fields
        self.amplitude_var = self._create_parameter_field("Amplitude (A):", 1.0)
        self.freq_var = self._create_parameter_field("Analog Frequency (F, Hz):", 1.0)
        self.phase_var = self._create_parameter_field("Phase Shift (theta, degrees):", 0.0)
        self.sampling_freq_var = self._create_parameter_field("Sampling Frequency (Fs, Hz):", 100.0)
        self.time_var = self._create_parameter_field("Duration (seconds):", 1.0)

        tk.Label(self.dialog, text="*Fs must obey Sampling Theorem (Fs > 2*F)",
                fg='red').pack(pady=5)

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Generate", command=self.generate,
                 width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 width=10).pack(side=tk.LEFT, padx=5)

    def _create_parameter_field(self, label, default):
        """Create a labeled parameter input field"""
        frame = tk.Frame(self.dialog)
        frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame, text=label, width=25, anchor='w').pack(side=tk.LEFT)
        var = tk.StringVar(value=str(default))
        entry = tk.Entry(frame, textvariable=var, width=15)
        entry.pack(side=tk.RIGHT, expand=True)
        return var

    def generate(self):
        """Generate the sinusoidal signal"""
        try:
            # Get all parameter values
            amplitude = float(self.amplitude_var.get())
            analog_freq = float(self.freq_var.get())  # Fixed variable name
            phase_deg = float(self.phase_var.get())  # Fixed variable name
            sampling_freq = float(self.sampling_freq_var.get())  # Fixed variable name
            duration = float(self.time_var.get())  # Fixed variable name
            is_cosine = (self.wave_type == "Cosine")

            # Validate parameters
            if any(v <= 0 for v in [sampling_freq, analog_freq, duration]):
                raise ValueError("Frequency, duration, and sampling rate must be positive.")

            # Prepare parameters for execution - using correct parameter names
            params = {
                'amplitude': amplitude,
                'analog_freq': analog_freq,  # Match parameter names in execute_operation
                'phase_deg': phase_deg,
                'sampling_freq': sampling_freq,
                'duration': duration,
                'is_cosine': is_cosine
            }

            # Execute the operation
            success = self.gui.execute_operation("sinusoidal", **params)
            if success:
                self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Error", f"Input Error:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed:\n{str(e)}")


class OperationDialog:
    """Base dialog for signal operations"""

    def __init__(self, parent, title, gui, operation_type):
        self.parent = parent
        self.title = title
        self.gui = gui
        self.operation_type = operation_type
        self.dialog = None

    def show(self):
        """Show the operation dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        if self.operation_type in ["addition", "subtraction"]:
            self.dialog.geometry("450x450")
        else:
            self.dialog.geometry("350x300")

        self.create_content()
        self.create_buttons()

    def create_content(self):
        """Create dialog content - to be overridden by specific operations"""
        tk.Label(self.dialog, text=f"Select for {self.title}",
                font=("Arial", 10, "bold")).pack(pady=10)

        if self.operation_type == "addition":
            self.create_addition_content()
        elif self.operation_type == "subtraction":
            self.create_subtraction_content()
        elif self.operation_type == "multiplication":
            self.create_multiplication_content()
        elif self.operation_type in ["squaring", "normalization", "accumulation"]:
            self.create_single_signal_content()

    def create_addition_content(self):
        """Create content for addition operation"""
        tk.Label(self.dialog, text="Select signals to add:").pack(pady=5)

        frame = tk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.populate_signal_list()

    def create_subtraction_content(self):
        """Create content for subtraction operation"""
        tk.Label(self.dialog, text="Signal 1 (Minuend):").pack(pady=5)
        self.signal1_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal1_list.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(self.dialog, text="Signal 2 (Subtrahend):").pack(pady=5)
        self.signal2_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal2_list.pack(padx=10, pady=5, fill=tk.X)

        self.populate_signal_list([self.signal1_list, self.signal2_list])

    def create_multiplication_content(self):
        """Create content for multiplication operation"""
        tk.Label(self.dialog, text="Select signal:").pack(pady=5)
        self.signal_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal_list.pack(padx=10, pady=5, fill=tk.X)
        self.populate_signal_list([self.signal_list])

        tk.Label(self.dialog, text="Enter constant:").pack(pady=5)
        self.constant_var = tk.StringVar(value="1.0")
        tk.Entry(self.dialog, textvariable=self.constant_var, width=20).pack(pady=5)

    def create_single_signal_content(self):
        """Create content for single-signal operations"""
        tk.Label(self.dialog, text="Select signal:").pack(pady=5)
        self.signal_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal_list.pack(padx=10, pady=5, fill=tk.X)
        self.populate_signal_list([self.signal_list])

        # Add range selection for normalization
        if self.operation_type == "normalization":
            tk.Label(self.dialog, text="Target Range:", font=("Arial", 9, "bold")).pack(pady=10)
            self.range_var = tk.StringVar(value="-1_to_1")
            tk.Radiobutton(self.dialog, text="Normalize from -1 to 1",
                          variable=self.range_var, value="-1_to_1").pack()
            tk.Radiobutton(self.dialog, text="Normalize from 0 to 1",
                          variable=self.range_var, value="0_to_1").pack()

    def populate_signal_list(self, listboxes=None):
        """Populate signal listboxes with available signals"""
        if listboxes is None:
            listboxes = [self.listbox] if hasattr(self, 'listbox') else []

        for listbox in listboxes:
            listbox.delete(0, tk.END)
            for i, signal in enumerate(self.gui.data_manager.get_all_signals()):
                listbox.insert(tk.END, f"{i+1}. {signal['name']}")

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Process", command=self.process,
                 width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 width=10).pack(side=tk.LEFT, padx=5)

    def process(self):
        """Process the selected operation"""
        try:
            if self.operation_type == "addition":
                selected = self.listbox.curselection()
                if len(selected) < 2:
                    messagebox.showwarning("Warning", "Select at least 2 signals")
                    return
                self.gui.execute_operation("addition", signal_indices=selected)

            elif self.operation_type == "subtraction":
                sel1 = self.signal1_list.curselection()
                sel2 = self.signal2_list.curselection()
                if not sel1 or not sel2:
                    messagebox.showwarning("Warning", "Select both signals")
                    return
                if sel1[0] == sel2[0]:
                    messagebox.showwarning("Warning", "Select different signals")
                    return
                self.gui.execute_operation("subtraction", signal1_index=sel1[0], signal2_index=sel2[0])

            elif self.operation_type == "multiplication":
                selected = self.signal_list.curselection()
                if not selected:
                    messagebox.showwarning("Warning", "Select a signal")
                    return
                constant = float(self.constant_var.get())
                self.gui.execute_operation("multiplication", signal_index=selected[0], constant=constant)

            elif self.operation_type == "squaring":
                selected = self.signal_list.curselection()
                if not selected:
                    messagebox.showwarning("Warning", "Select a signal")
                    return
                self.gui.execute_operation("squaring", signal_index=selected[0])

            elif self.operation_type == "normalization":
                selected = self.signal_list.curselection()
                if not selected:
                    messagebox.showwarning("Warning", "Select a signal")
                    return
                self.gui.execute_operation("normalization", signal_index=selected[0],
                                         target_range=self.range_var.get())

            elif self.operation_type == "accumulation":
                selected = self.signal_list.curselection()
                if not selected:
                    messagebox.showwarning("Warning", "Select a signal")
                    return
                self.gui.execute_operation("accumulation", signal_index=selected[0])

            self.dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Error", f"Input error:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Operation failed:\n{str(e)}")


class ComparisonDialog:
    """Dialog for comparing two signals"""

    def __init__(self, parent, gui):
        self.parent = parent
        self.gui = gui
        self.dialog = None

    def show(self):
        """Show the comparison dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Compare Two Signals")
        self.dialog.geometry("450x450")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Select Two Signals to Compare",
                font=("Arial", 10, "bold")).pack(pady=10)

        # Signal selection
        tk.Label(self.dialog, text="Signal 1:").pack(pady=5)
        self.signal1_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal1_list.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(self.dialog, text="Signal 2:").pack(pady=5)
        self.signal2_list = tk.Listbox(self.dialog, height=5, exportselection=False)
        self.signal2_list.pack(padx=10, pady=5, fill=tk.X)

        self.populate_signal_lists()

        # Display mode selection
        tk.Label(self.dialog, text="Display Mode:", font=("Arial", 9, "bold")).pack(pady=10)
        self.mode_var = tk.StringVar(value="discrete")

        mode_frame = tk.Frame(self.dialog)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Continuous", variable=self.mode_var,
                      value="continuous").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Discrete", variable=self.mode_var,
                      value="discrete").pack(side=tk.LEFT, padx=10)

        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Compare", command=self.compare,
                 width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 width=10).pack(side=tk.LEFT, padx=5)

    def populate_signal_lists(self):
        """Populate both signal listboxes"""
        for listbox in [self.signal1_list, self.signal2_list]:
            listbox.delete(0, tk.END)
            for i, signal in enumerate(self.gui.data_manager.get_all_signals()):
                listbox.insert(tk.END, f"{i+1}. {signal['name']}")

    def compare(self):
        """Execute the comparison"""
        sel1 = self.signal1_list.curselection()
        sel2 = self.signal2_list.curselection()

        if not sel1 or not sel2:
            messagebox.showwarning("Warning", "Select both signals")
            return

        if sel1[0] == sel2[0]:
            messagebox.showwarning("Warning", "Please select different signals")
            return

        self.gui.display_two_signals(sel1[0], sel2[0], self.mode_var.get())
        self.dialog.destroy()


# ===== MAIN APPLICATION =====
def main():
    """Main application entry point"""
    root = tk.Tk()
    app = SignalProcessingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()