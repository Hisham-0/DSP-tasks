"""
Signal Processing Framework - Presentation Layer
Simple GUI with all required features
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Import signal reader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Data.signal_reader import SignalReader


class SignalProcessingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Signal Processing Framework - Task 1")
        self.root.geometry("1400x800")

        # Data storage
        self.signals = []
        self.signal_reader = SignalReader()

        # For displaying two signals
        self.signal1_index = None
        self.signal2_index = None

        # For panning (hand tool)
        self.panning = False
        self.pan_start = None

        # Build interface
        self.create_menu()
        self.create_interface()

    def create_menu(self):
        """Create menu bar"""
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

        # Arithmetic Operations menu
        arithmetic_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arithmetic Operations", menu=arithmetic_menu)
        arithmetic_menu.add_command(label="Addition", command=self.show_addition_dialog)
        arithmetic_menu.add_command(label="Multiplication", command=self.show_multiplication_dialog)

        # Display menu
        display_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Display", menu=display_menu)
        display_menu.add_command(label="Show Continuous", command=lambda: self.display_signal("continuous"))
        display_menu.add_command(label="Show Discrete", command=lambda: self.display_signal("discrete"))
        display_menu.add_separator()
        display_menu.add_command(label="Compare Two Signals", command=self.show_comparison_dialog)

    def create_interface(self):
        """Create main interface"""

        # === Top frame - Controls ===
        top_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Quick access buttons
        buttons = [
            ("Load Signal", self.load_signal),
            ("Show Continuous", lambda: self.display_signal("continuous")),
            ("Show Discrete", lambda: self.display_signal("discrete")),
            ("Compare Signals", self.show_comparison_dialog),
            ("Addition", self.show_addition_dialog),
            ("Multiplication", self.show_multiplication_dialog),
        ]

        for text, cmd in buttons:
            tk.Button(top_frame, text=text, command=cmd, width=15).pack(side=tk.LEFT, padx=5, pady=5)

        # === Main content area ===
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === Left panel - Signal list and info ===
        left_frame = tk.Frame(content_frame, relief=tk.RIDGE, borderwidth=2, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # --- Loaded Signals section ---
        list_label = tk.Label(left_frame, text="Loaded Signals", font=("Arial", 10, "bold"))
        list_label.pack(pady=5)

        # Frame that holds the listbox and both scrollbars
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        y_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Listbox for signals (with horizontal scrolling for long names)
        self.signal_listbox = tk.Listbox(
            list_frame,
            font=("Courier", 9),
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )
        self.signal_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scrollbar.config(command=self.signal_listbox.yview)
        x_scrollbar.config(command=self.signal_listbox.xview)

        # Enable horizontal scrolling when names are too long
        self.signal_listbox.config(width=0, exportselection=False)
        self.signal_listbox.bind('<<ListboxSelect>>', self.on_signal_select)

        # --- Signal Information section ---
        info_label = tk.Label(left_frame, text="Signal Information", font=("Arial", 10, "bold"))
        info_label.pack(pady=5)

        info_frame = tk.Frame(left_frame, relief=tk.SUNKEN, borderwidth=1)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_scrollbar = tk.Scrollbar(info_frame)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.info_text = tk.Text(
            info_frame,
            wrap=tk.WORD,
            height=10,
            font=("Courier", 9),
            yscrollcommand=info_scrollbar.set,
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        info_scrollbar.config(command=self.info_text.yview)

        # === Right panel - Plot area ===
        right_frame = tk.Frame(content_frame, relief=tk.RIDGE, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        plot_label = tk.Label(right_frame, text="Signal Display", font=("Arial", 10, "bold"))
        plot_label.pack(pady=5)

        # Matplotlib figure setup
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Mouse events (zoom & pan)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_wheel)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        # Initial plot setup
        self.ax.set_title("No Signal Loaded")
        self.ax.set_xlabel("Sample Index (n)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.canvas.draw()

        # === Status bar ===
        self.status_label = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

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
                self.signal1_index = None
                self.signal2_index = None
                self.update_signal_list()

                self.ax.clear()
                self.ax.set_title("No Signal Loaded")
                self.ax.set_xlabel("Sample Index (n)")
                self.ax.set_ylabel("Amplitude")
                self.ax.grid(True, linestyle='--', alpha=0.5)
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
            display_text = f"{i+1}. {signal['name']} [{type_char}-{periodic_char}, {signal['num_samples']} samples]"
            self.signal_listbox.insert(tk.END, display_text)

        self.status_label.config(text=f"Total signals: {len(self.signals)}")

    def on_signal_select(self, event):
        """Handle signal selection"""
        selection = self.signal_listbox.curselection()
        if selection:
            index = selection[0]
            self.show_signal_info(index)

    def show_signal_info(self, index):
        """Display signal information"""
        self.info_text.delete(1.0, tk.END)

        if 0 <= index < len(self.signals):
            signal = self.signals[index]
            stats = self.signal_reader.calculate_statistics(signal["samples"])

            signal_type = "Time Domain" if signal["signal_type"] == 0 else "Frequency Domain"
            periodic = "Periodic" if signal["is_periodic"] == 1 else "Non-Periodic"

            info = f"Signal Name: {signal['name']}\n"
            info += f"{'='*40}\n\n"
            info += f"Type: {signal_type}\n"
            info += f"Periodic: {periodic}\n"
            info += f"Number of Samples: {signal['num_samples']}\n\n"
            info += f"Statistics:\n"
            info += f"  Minimum: {stats['min']:.4f}\n"
            info += f"  Maximum: {stats['max']:.4f}\n"
            info += f"  Mean: {stats['mean']:.4f}\n\n"
            info += f"Sample Data (first 10):\n"
            info += f"{'Index':<10} {'Amplitude':<12}\n"
            info += f"{'-'*25}\n"

            for i in range(min(15, len(signal["samples"]))):
                info += f"{signal['indices'][i]:<10.1f} {signal['samples'][i]:<12.4f}\n"

            if len(signal["samples"]) > 10:
                info += f"\n... and {len(signal['samples']) - 10} more samples"

            self.info_text.insert(tk.END, info)

    def display_signal(self, mode):
        """Display selected signal in continuous or discrete mode"""
        selection = self.signal_listbox.curselection()

        if not selection:
            messagebox.showwarning("Warning", "Please select a signal from the list")
            return

        index = selection[0]
        signal = self.signals[index]

        self.ax.clear()

        indices = signal["indices"]
        samples = signal["samples"]

        if mode == "continuous":
            # Continuous representation
            self.ax.plot(indices, samples, 'b-', linewidth=2, label='Continuous')
            title = f"Continuous Representation: {signal['name']}"

        elif mode == "discrete":
            # Discrete representation
            markerline, stemlines, baseline = self.ax.stem(indices, samples, basefmt=" ")
            plt.setp(markerline, markersize=6, color='red')
            plt.setp(stemlines, linewidth=1.5, color='red')
            title = f"Discrete Representation: {signal['name']}"

        self.ax.set_title(title, fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Sample Index (n)", fontsize=10)
        self.ax.set_ylabel("Amplitude x(n)", fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.axhline(y=0, color='k', linewidth=0.5)

        self.fig.tight_layout()
        self.canvas.draw()

        self.status_label.config(text=f"Displaying: {signal['name']} ({mode})")

    def show_addition_dialog(self):
        """Show dialog for adding signals"""
        if len(self.signals) < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for addition")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Signals")
        dialog.geometry("400x400")

        tk.Label(dialog, text="Select Signals to Add",
                font=("Arial", 10, "bold")).pack(pady=10)

        # Listbox for signal selection
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE,
                            yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        for i, signal in enumerate(self.signals):
            listbox.insert(tk.END, f"{i+1}. {signal['name']}")

        # Buttons
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
                result["name"] = f"Addition_Result_{len(self.signals)+1}.txt"
                result["filepath"] = ""

                self.signals.append(result)
                self.update_signal_list()

                dialog.destroy()

                messagebox.showinfo("Success",
                                   f"Successfully added {len(selected)} signals\n"
                                   f"Result has {result['num_samples']} samples")

                self.status_label.config(text=f"Addition complete: {result['name']}")

            except Exception as e:
                messagebox.showerror("Error", f"Addition failed:\n{str(e)}")

        tk.Button(button_frame, text="Add Selected Signals",
                 command=perform_addition, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                 command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_multiplication_dialog(self):
        """Show dialog for multiplying signal"""
        if not self.signals:
            messagebox.showwarning("Warning", "No signals loaded")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Multiply Signal")
        dialog.geometry("400x300")

        tk.Label(dialog, text="Multiply Signal by Constant",
                font=("Arial", 10, "bold")).pack(pady=10)

        # Signal selection
        tk.Label(dialog, text="Select Signal:").pack(pady=5)

        signal_var = tk.StringVar()
        signal_combo = tk.Listbox(dialog, height=5, exportselection=False)
        signal_combo.pack(padx=10, pady=5, fill=tk.X)

        for i, signal in enumerate(self.signals):
            signal_combo.insert(tk.END, f"{i+1}. {signal['name']}")

        # Constant input
        tk.Label(dialog, text="Enter Constant:").pack(pady=5)
        tk.Label(dialog, text="(Use -1 to invert signal)",
                font=("Arial", 8)).pack()

        constant_var = tk.StringVar(value="1.0")
        tk.Entry(dialog, textvariable=constant_var, width=20).pack(pady=5)

        # Buttons
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

                if constant == -1:
                    result["name"] = f"Inverted_{signal['name']}"
                else:
                    result["name"] = f"Multiplied_{constant}x_{signal['name']}"
                result["filepath"] = ""

                self.signals.append(result)
                self.update_signal_list()

                dialog.destroy()

                operation = "inverted" if constant == -1 else f"multiplied by {constant}"
                messagebox.showinfo("Success",
                                   f"Signal {operation} successfully")

                self.status_label.config(text=f"Multiplication complete: {result['name']}")

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Multiplication failed:\n{str(e)}")

        tk.Button(button_frame, text="Multiply",
                 command=perform_multiplication, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel",
                 command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def show_comparison_dialog(self):
        """Show dialog for comparing two signals"""
        if len(self.signals) < 2:
            messagebox.showwarning("Warning", "Need at least 2 signals for comparison")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Two Signals")
        dialog.geometry("450x450")

        tk.Label(dialog, text="Select Two Signals to Compare",
                font=("Arial", 10, "bold")).pack(pady=10)

        # First signal
        tk.Label(dialog, text="Signal 1:").pack(pady=5)
        signal1_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal1_list.pack(padx=10, pady=5, fill=tk.X)

        # Second signal
        tk.Label(dialog, text="Signal 2:").pack(pady=5)
        signal2_list = tk.Listbox(dialog, height=5, exportselection=False)
        signal2_list.pack(padx=10, pady=5, fill=tk.X)

        # Populate both listboxes
        for i, signal in enumerate(self.signals):
            display_text = f"{i+1}. {signal['name']}"
            signal1_list.insert(tk.END, display_text)
            signal2_list.insert(tk.END, display_text)

        # Display mode selection
        tk.Label(dialog, text="Display Mode:", font=("Arial", 9, "bold")).pack(pady=10)

        mode_var = tk.StringVar(value="continuous")

        mode_frame = tk.Frame(dialog)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Continuous", variable=mode_var,
                      value="continuous").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Discrete", variable=mode_var,
                      value="discrete").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Both", variable=mode_var,
                      value="both").pack(side=tk.LEFT, padx=10)

        # Buttons
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

    def display_two_signals(self, index1, index2, mode="continuous"):
        """Display two signals at the same time"""
        signal1 = self.signals[index1]
        signal2 = self.signals[index2]

        self.ax.clear()

        if mode == "continuous":
            # Continuous representation for both signals
            self.ax.plot(signal1["indices"], signal1["samples"],
                        'b-', linewidth=2, label=signal1['name'], marker='o', markersize=4)
            self.ax.plot(signal2["indices"], signal2["samples"],
                        'r-', linewidth=2, label=signal2['name'], marker='s', markersize=4)
            title = "Comparison - Continuous"

        elif mode == "discrete":
            # Discrete representation for both signals
            # Signal 1 - blue stems
            markerline1, stemlines1, baseline1 = self.ax.stem(
                signal1["indices"], signal1["samples"],
                linefmt='b-', markerfmt='bo', basefmt=" ", label=signal1['name']
            )
            plt.setp(markerline1, markersize=6)
            plt.setp(stemlines1, linewidth=1.5)

            # Signal 2 - red stems (slightly offset for visibility)
            indices2_offset = [i + 0.1 for i in signal2["indices"]]
            markerline2, stemlines2, baseline2 = self.ax.stem(
                indices2_offset, signal2["samples"],
                linefmt='r-', markerfmt='rs', basefmt=" ", label=signal2['name']
            )
            plt.setp(markerline2, markersize=6)
            plt.setp(stemlines2, linewidth=1.5)

            title = "Comparison - Discrete"

        elif mode == "both":
            # Both continuous and discrete for both signals
            # Signal 1 - blue
            self.ax.plot(signal1["indices"], signal1["samples"],
                        'b-', linewidth=1.5, alpha=0.7, label=signal1['name'] + ' (line)')
            markerline1, stemlines1, baseline1 = self.ax.stem(
                signal1["indices"], signal1["samples"],
                linefmt='b-', markerfmt='bo', basefmt=" "
            )
            plt.setp(markerline1, markersize=5)
            plt.setp(stemlines1, linewidth=1, alpha=0.5)

            # Signal 2 - red
            indices2_offset = [i + 0.1 for i in signal2["indices"]]
            self.ax.plot(signal2["indices"], signal2["samples"],
                        'r-', linewidth=1.5, alpha=0.7, label=signal2['name'] + ' (line)')
            markerline2, stemlines2, baseline2 = self.ax.stem(
                indices2_offset, signal2["samples"],
                linefmt='r-', markerfmt='rs', basefmt=" "
            )
            plt.setp(markerline2, markersize=5)
            plt.setp(stemlines2, linewidth=1, alpha=0.5)

            title = "Comparison - Continuous & Discrete"

        self.ax.set_title(title, fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Sample Index (n)", fontsize=10)
        self.ax.set_ylabel("Amplitude", fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.5)
        self.ax.axhline(y=0, color='k', linewidth=0.5)
        self.ax.legend()

        self.fig.tight_layout()
        self.canvas.draw()

        self.status_label.config(text=f"Comparing: {signal1['name']} vs {signal2['name']} ({mode})")


    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom in/out"""
        if event.inaxes != self.ax:
            return

        # Get current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Get mouse position
        xdata = event.xdata
        ydata = event.ydata

        # Zoom factor
        if event.button == 'up':
            # Zoom in
            scale_factor = 0.8
        elif event.button == 'down':
            # Zoom out
            scale_factor = 1.2
        else:
            return

        # Calculate new limits centered on mouse position
        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor

        relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
        rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

        new_xlim = [xdata - new_width * (1 - relx), xdata + new_width * relx]
        new_ylim = [ydata - new_height * (1 - rely), ydata + new_height * rely]

        # Apply new limits
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        # Redraw canvas
        self.canvas.draw_idle()

        # Update status
        zoom_level = "in" if event.button == 'up' else "out"
        self.status_label.config(text=f"Zoomed {zoom_level}")


    def on_mouse_press(self, event):
        """Handle mouse button press for panning"""
        if event.inaxes != self.ax:
            return

        # Left mouse button starts panning
        if event.button == 1:
            self.panning = True
            self.pan_start = (event.xdata, event.ydata)
            # Change cursor to hand
            self.canvas.get_tk_widget().config(cursor="fleur")
            self.status_label.config(text="Panning... (drag to move)")


    def on_mouse_release(self, event):
        """Handle mouse button release"""
        if event.button == 1:
            self.panning = False
            self.pan_start = None
            # Reset cursor
            self.canvas.get_tk_widget().config(cursor="")
            self.status_label.config(text="Ready")


    def on_mouse_move(self, event):
        """Handle mouse motion for panning"""
        if not self.panning or not self.pan_start:
            return

        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
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