#!/usr/bin/env python3
# Requires Python 3.10 or higher

import sys
import socket
import struct
import json
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt

class UDPReceiver(QWidget):
    def __init__(self):
        super().__init__()
        self.config = []  # Ensure config is initialized before initUI
        self.data_labels = []  # Store data labels for displaying received data
        self.initUI()
        self.sock = None
        self.receiving = False  # Flag to control receiving thread

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
        
        self.start_button = QPushButton('Start Receiving')
        self.start_button.clicked.connect(self.start_receiving)
        udp_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('Stop Receiving')
        self.stop_button.clicked.connect(self.stop_receiving)
        udp_layout.addWidget(self.stop_button)
        
        layout.addLayout(udp_layout)

        # Packet Configuration
        self.packet_layout = QVBoxLayout()
        #self.add_packet_config()
        layout.addLayout(self.packet_layout)

        self.add_button = QPushButton('Add Packet Config')
        self.add_button.clicked.connect(self.add_packet_config)
        layout.addWidget(self.add_button)

        # Save/Load Configuration
        config_layout = QHBoxLayout()
        self.save_button = QPushButton('Save Config')
        self.save_button.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_button)
        self.load_button = QPushButton('Load Config')
        self.load_button.clicked.connect(self.load_config)
        config_layout.addWidget(self.load_button)
        layout.addLayout(config_layout)

        self.setLayout(layout)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Ensure close event is triggered

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
        data_label = QLabel('')
        data_label.setFixedWidth(200)  # Set a fixed width for the data label
        config_layout.addWidget(data_label)
        self.packet_layout.addLayout(config_layout)
        self.config.append((label_edit, type_edit, offset_edit, data_label))
        self.data_labels.append(data_label)

    def start_receiving(self):
        ip = self.ip_edit.text()
        port = int(self.port_edit.text())
        buffer_size = int(self.buffer_edit.text())
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(1.0)
        
        # Clear existing data labels
        for data_label in self.data_labels:
            data_label.setText('')
        
        self.receiving = True
        self.receive_thread = threading.Thread(target=self.receive_data, args=(buffer_size,))
        self.receive_thread.start()

    def stop_receiving(self):
        self.receiving = False
        if self.receive_thread.is_alive():
            self.receive_thread.join()
        if self.sock:
            self.sock.close()

    def receive_data(self, buffer_size):
        while self.receiving:
            try:
                data, _ = self.sock.recvfrom(buffer_size)
                self.process_data(data)
            except socket.timeout:
                continue

    def process_data(self, data):
        for label_edit, type_edit, offset_edit, data_label in self.config:
            label = label_edit.text()
            data_type = type_edit.text()
            offset = int(offset_edit.text())
            if data_type == 'float':
                value = struct.unpack_from('f', data, offset)[0]
            elif data_type == 'int':
                value = struct.unpack_from('i', data, offset)[0]
            elif data_type == 'uint_8':
                value = struct.unpack_from('B', data, offset)[0]
            elif data_type.startswith('bit'):
                bit_index = int(data_type.split('_')[1])
                byte_value = struct.unpack_from('B', data, offset)[0]
                value = (byte_value >> bit_index) & 1
            elif data_type == 'uint_16':
                value = struct.unpack_from('H', data, offset)[0]
            elif data_type == 'uint_32':
                value = struct.unpack_from('I', data, offset)[0]
            else:
                value = 'Unknown Type'
            data_label.setText(f'{label}: {value}')
            
    def save_config(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            config_data = {
                'ip': self.ip_edit.text(),
                'port': self.port_edit.text(),
                'buffer_size': self.buffer_edit.text(),
                'packet_config': [{'label': label_edit.text(), 'type': type_edit.text(), 'offset': offset_edit.text()} for label_edit, type_edit, offset_edit, _ in self.config]
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UDPReceiver()
    ex.show()
    sys.exit(app.exec_())
