#!/usr/bin/env python3
# Requires Python 3.10 or higher

import sys
import socket
import struct
import json
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QScrollArea, QSizePolicy, QCheckBox, QGroupBox, QFormLayout, QFrame
from PyQt5.QtCore import Qt, QTimer, QEvent
import matplotlib.pyplot as plt
import time
import matplotlib.animation as animation
from collections import deque


class UDPReceiver(QWidget):
    def __init__(self):
        super().__init__()
        self.config = []  # Ensure config is initialized before initUI
        self.data_labels = []  # Store data labels for displaying received data
        self.packet_count = 0
        self.frequency_label = QLabel('Frequency: 0 Hz')
        self.animation_interval_edit = QLineEdit("0")  # Initialize here
        self.initUI()
        self.sock = None
        self.receiving = False  # Flag to control receiving thread
        self.was_receiving = False  # Track if receiving was active before losing focus
        self.receive_thread = None  # Initialize receive_thread to None
        self.plot_data = {}  # Store data for plotting
        self.plot_button.clicked.connect(self.plot_data_real_time)
        self.ok = False
        self.checkbox_state = {}  # Dictionary to store checkbox states
        self.start_button.setCheckable(True)
        self.stop_button.setCheckable(True)
        self.stop_button.setChecked(True)  # Initialize with stop button pressed
        self.start_button.setChecked(False)  # Initialize with start button released

    def initUI(self):
        self.setWindowTitle('UDP Data Viewer')
        
        layout = QVBoxLayout()

        # UDP Configuration
        udp_layout = QVBoxLayout()
        
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel('UDP IP:'))
        self.ip_edit = QLineEdit('10.24.7.51')
        ip_layout.addWidget(self.ip_edit)
        udp_layout.addLayout(ip_layout)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('UDP Port:'))
        self.port_edit = QLineEdit('12345')
        port_layout.addWidget(self.port_edit)
        udp_layout.addLayout(port_layout)
        
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(QLabel('Buffer Size:'))
        self.buffer_edit = QLineEdit('118')
        buffer_layout.addWidget(self.buffer_edit)
        udp_layout.addLayout(buffer_layout)
        
        button_layout = QHBoxLayout()  # Create a horizontal layout for start and stop buttons
        self.start_button = QPushButton('Start Receiving')
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: green; 
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: darkgreen;
                color: white;
                font-weight: bold;
            }
        """)
        self.start_button.clicked.connect(self.start_receiving)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('Stop Receiving')
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: red; 
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: darkred;
                color: white;
                font-weight: bold;
            }
        """)
        self.stop_button.clicked.connect(self.stop_receiving)
        button_layout.addWidget(self.stop_button)
        
        udp_layout.addLayout(button_layout)  # Add the horizontal layout to udp_layout

        # Add a horizontal line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        udp_layout.addWidget(separator)
        
        layout.addLayout(udp_layout)

        # Packet Configuration
        self.packet_layout = QVBoxLayout()
        #self.add_packet_config()
        layout.addLayout(self.packet_layout)

        packet_button_layout = QHBoxLayout()  # Create a horizontal layout for add and clear buttons
        self.add_button = QPushButton('Add Packet Config')
        self.add_button.clicked.connect(self.add_packet_config)
        packet_button_layout.addWidget(self.add_button)

        self.clear_button = QPushButton('Clear Config')  # Add clear button
        self.clear_button.clicked.connect(self.clear_packet_config)
        packet_button_layout.addWidget(self.clear_button)

        layout.addLayout(packet_button_layout)  # Add the horizontal layout to the main layout

        # Plot Settings
        plot_group_box = QGroupBox("Plot Settings")
        plot_layout = QFormLayout()

        self.plot_button = QPushButton('Plot Data')  # Add plot button
        plot_layout.addRow(self.plot_button)

        self.min_y_edit = QLineEdit('-1')
        self.max_y_edit = QLineEdit('1')
        plot_layout.addRow(QLabel('Min Y:'), self.min_y_edit)
        plot_layout.addRow(QLabel('Max Y:'), self.max_y_edit)

        self.fix_y_checkbox = QCheckBox('Fix Y Axis')  # Add checkbox
        plot_layout.addRow(self.fix_y_checkbox)

        plot_layout.addRow(QLabel('Animation Interval (ms):'), self.animation_interval_edit)  # Add interval input

        plot_group_box.setLayout(plot_layout)
        layout.addWidget(plot_group_box)

        # Save/Load Configuration
        config_layout = QHBoxLayout()
        self.save_button = QPushButton('Save Config')
        self.save_button.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_button)
        self.load_button = QPushButton('Load Config')
        self.load_button.clicked.connect(self.load_config)
        config_layout.addWidget(self.load_button)
        layout.addLayout(config_layout)

        layout.addWidget(self.frequency_label)

        self.setLayout(layout)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Ensure close event is triggered

        self.frequency_timer = QTimer(self)
        self.frequency_timer.timeout.connect(self.update_frequency)
        self.frequency_timer.start(1000)  # Update frequency every second

        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.WindowDeactivate:
            self.was_receiving = self.receiving
            # Do not stop receiving when losing focus
        elif event.type() == QEvent.WindowActivate and self.was_receiving:
            self.start_receiving()
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        self.stop_receiving()
        event.accept()

    def add_packet_config(self):
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel('Label:'))
        label_edit = QLineEdit()
        config_layout.addWidget(label_edit)
        config_layout.addWidget(QLabel('Type:'))
        type_edit = QLineEdit()
        config_layout.addWidget(type_edit)
        config_layout.addWidget(QLabel('Offset:'))
        offset_edit = QLineEdit()
        config_layout.addWidget(offset_edit)
        active_checkbox = QCheckBox('Plot')  # Add checkbox
        active_checkbox.stateChanged.connect(self.handle_checkbox_state_change)  # Connect checkbox state change event
        config_layout.addWidget(active_checkbox)
        data_label = QLabel('')
        data_label.setFixedWidth(200)  # Set a fixed width for the data label
        config_layout.addWidget(data_label)
        self.packet_layout.addLayout(config_layout)
        self.config.append((label_edit, type_edit, offset_edit, active_checkbox, data_label))  # Include checkbox in config
        self.data_labels.append(data_label)
        self.checkbox_state[label_edit.text()] = active_checkbox.isChecked()  # Initialize checkbox state

    def handle_checkbox_state_change(self, state):
        sender = self.sender()
        self.plot_data = {}  # Reset plot data when any checkbox state changes
        any_checked = False
        for label_edit, _, _, active_checkbox, _ in self.config:
            if active_checkbox == sender:
                self.checkbox_state[label_edit.text()] = (state == Qt.Checked)
            if active_checkbox.isChecked():
                any_checked = True
        self.ok = any_checked  # Set self.ok based on whether any checkbox is checked

    def start_receiving(self):
        ip = self.ip_edit.text()
        port = int(self.port_edit.text())
        buffer_size = int(self.buffer_edit.text())
        
        # Ensure the socket is closed before creating a new one
        if self.sock:
            self.sock.close()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(1.0)
        
        # Clear existing data labels
        for data_label in self.data_labels:
            data_label.setText('')
        
        self.receiving = True
        self.packet_count = 0
        self.receive_thread = threading.Thread(target=self.receive_data, args=(buffer_size,), daemon=True)
        self.receive_thread.start()
        self.start_button.setChecked(True)
        self.stop_button.setChecked(False)

    def stop_receiving(self):
        self.receiving = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()
        if self.sock:
            self.sock.close()
        self.start_button.setChecked(False)
        self.stop_button.setChecked(True)

    def receive_data(self, buffer_size):
        while self.receiving:
            if self.sock is None:
                break
            try:
                data, _ = self.sock.recvfrom(buffer_size)
                self.packet_count += 1
                self.process_data(data)
                self.ok = False
            except socket.timeout:
                continue
            except OSError as e:
                if e.errno == 10038:  # WinError 10038: Operation attempted on something that is not a socket
                    break

    def process_data(self, data):
        for label_edit, type_edit, offset_edit, active_checkbox, data_label in self.config:
            label = label_edit.text()
            data_type = type_edit.text()
            offset_text = offset_edit.text()
            if not offset_text.isdigit():
                data_label.setText(f'{label}: Error: Invalid offset')
                continue
            offset = int(offset_text)
            try:
                if data_type == 'float':
                    value = struct.unpack_from('f', data, offset)[0]
                elif data_type == 'int':
                    value = struct.unpack_from('i', data, offset)[0]
                elif data_type == 'uint_8':
                    value = struct.unpack_from('B', data, offset)[0]
                elif data_type == 'int_8':
                    value = struct.unpack_from('b', data, offset)[0]
                elif data_type == 'uint_16':
                    value = struct.unpack_from('H', data, offset)[0]
                elif data_type == 'int_16':
                    value = struct.unpack_from('h', data, offset)[0]
                elif data_type == 'uint_32':
                    value = struct.unpack_from('I', data, offset)[0]
                elif data_type == 'int_32':
                    value = struct.unpack_from('i', data, offset)[0]
                elif data_type == 'uint_64':
                    value = struct.unpack_from('Q', data, offset)[0]
                elif data_type == 'int_64':
                    value = struct.unpack_from('q', data, offset)[0]
                elif data_type == 'double':
                    value = struct.unpack_from('d', data, offset)[0]
                elif data_type == 'char':
                    value = struct.unpack_from('c', data, offset)[0].decode('utf-8')
                elif data_type == 'string':
                    end = data.find(b'\x00', offset)
                    value = data[offset:end].decode('utf-8')
                elif data_type == 'bool':
                    value = struct.unpack_from('?', data, offset)[0]
                elif data_type.startswith('bit_'):
                    bit_index = int(data_type.split('_')[1])
                    byte_value = struct.unpack_from('B', data, offset)[0]
                    value = (byte_value >> bit_index) & 1
                elif data_type == 'bcd':
                    byte_value = struct.unpack_from('B', data, offset)[0]
                    value = (byte_value >> 4) * 10 + (byte_value & 0xF)
                elif data_type == 'timestamp':
                    value = struct.unpack_from('I', data, offset)[0]
                else:
                    value = 'Unknown Type'
            except Exception as e:
                value = f'Error: {e}'
            data_label.setText(f'{label}: {value}')
            if self.ok:
                if active_checkbox.isChecked() :
                    if label not in self.plot_data:
                        self.plot_data[label] = deque(maxlen=1000)
                    self.plot_data[label].append(value)

            
    def save_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            config_data = {
                'ip': self.ip_edit.text(),
                'port': self.port_edit.text(),
                'buffer_size': self.buffer_edit.text(),
                'packet_config': [{'label': label_edit.text(), 'type': type_edit.text(), 'offset': offset_edit.text()} for label_edit, type_edit, offset_edit, _, _ in self.config]
            }
            with open(file_name, 'w') as file:
                json.dump(config_data, file)

    def load_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r') as file:
                config_data = json.load(file)
                self.ip_edit.setText(config_data['ip'])
                self.port_edit.setText(config_data['port'])
                self.buffer_edit.setText(config_data['buffer_size'])
                # Clear existing layout and config
                for i in range(self.packet_layout.count()):
                    widget = self.packet_layout.itemAt(i).widget()
                    if widget is not None:
                        widget.setParent(None)
                self.config = []
                for item in config_data['packet_config']:
                    self.add_packet_config()
                    self.config[-1][0].setText(item['label'])
                    self.config[-1][1].setText(item['type'])
                    self.config[-1][2].setText(item['offset'])

    def clear_packet_config(self):
        while self.packet_layout.count():
            item = self.packet_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
            if item.widget():
                item.widget().deleteLater()
        self.config = []
        self.data_labels = []
        self.update()  # Refresh the UI

    def update_frequency(self):
        self.frequency_label.setText(f'Frequency: {self.packet_count} Hz')
        self.packet_count = 0

    def plot_data_real_time(self):
        if hasattr(self, 'ani') and self.ani is not None:
          plt.close('all')  # Close any existing plots
        self.plot_data = {}
        self.ani = None
        lines = {}
        
        '''se non ci sono checkbox ceccate non posso fare il plot'''
        if not self.ok:
            print("Nessun dato selezionato per il plot.")
            return
        fig, ax = plt.subplots()
        lines = {}  # Dizionario per memorizzare le linee del grafico

        # Inizializza le linee per ciascun dato da plottare
        for label in self.plot_data:
            line, = ax.plot([], [], label=label)
            lines[label] = line

        ax.legend()
        ax.set_title("Dati in Tempo Reale da UDP")
        ax.set_xlabel("Campioni")
        ax.set_ylabel("Valore")
        ax.set_xlim(0, 1000)  # Limite iniziale

        if self.fix_y_checkbox.isChecked():
            min_y = float(self.min_y_edit.text())
            max_y = float(self.max_y_edit.text())
            ax.set_ylim(min_y, max_y)
        else:
            ax.set_ylim(-1, 1)  # Può essere adattato dinamicamente

        def update(frame):
            self.ok = True
            if not self.plot_data:
                print("Dati non disponibili per l'aggiornamento.")
                return []

            # Aggiorna i dati per ogni linea
            for label, data in self.plot_data.items():
                if data:  # Controlla che ci siano dati validi
                    lines[label].set_data(range(len(data)), data)

            # Aggiorna dinamicamente i limiti dell'asse
            if not self.fix_y_checkbox.isChecked():
                all_data = [item for sublist in self.plot_data.values() for item in sublist]
                if all_data:
                    ax.set_xlim(0, max(len(data) for data in self.plot_data.values()))
                    ax.set_ylim(min(all_data), max(all_data))

            return lines.values()

        def on_close(event):
            self.ani.event_source.stop()
            plt.close('all')

        fig.canvas.mpl_connect('close_event', on_close)

        interval = int(self.animation_interval_edit.text()) if self.animation_interval_edit.text().isdigit() else 50  # Default to 50ms if invalid
        self.ani = animation.FuncAnimation(fig, update, interval=interval, blit=False, cache_frame_data=False)
        plt.show()


        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UDPReceiver()
    ex.show()
    sys.exit(app.exec_())
