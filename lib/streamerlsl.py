import threading
import sys
import time
from lib.open_bci_v3 import OpenBCIBoard
from pylsl import StreamInfo, StreamOutlet
from collections import OrderedDict


class StreamerLSL():
    GAINS = [1, 2, 4, 6, 8, 12, 24]
    CHANNELS = "12345678QWERTYUI"

    def __init__(self, port, gain, daisy):
        self.settings = OrderedDict()
        self.initialize_board(port, daisy)
        self.init_board_settings(gain)

    def initialize_board(self, port, daisy):
        print("\n-------INSTANTIATING BOARD-------")

        self.board = OpenBCIBoard(port=port, daisy=daisy)
        self.eeg_channels = self.board.getNbEEGChannels()
        self.sample_rate = self.board.getSampleRate()

        if self.board.daisy:
            s = 'C'
        else:
            s = 'c'

        self.board.ser.write(bytes(s, 'utf-8'))

    def init_board_settings(self, gain):
        # set board configuration
        for i in range(self.eeg_channels):
            current = "channel{}".format(i+1)
            self.settings[current] = []
            self.settings[current].append(b'x')
            self.settings[current].append(self.CHANNELS[i].encode())
            self.settings[current].append(b'0')
            self.settings[current].append(str(self.GAINS.index(gain)).encode())
            self.settings[current].append(b'0')
            self.settings[current].append(b'1')
            self.settings[current].append(b'1')
            self.settings[current].append(b'0')
            self.settings[current].append(b'X')

        for item in self.settings:
            for byte in self.settings[item]:
                self.board.ser.write(byte)
                time.sleep(.2)

    def send(self, sample):
        try:
            self.outlet_eeg.push_sample(sample.channel_data)
        except:
            print("Error! Check LSL settings")

    def create_lsl(self):
        # default parameters
        eeg_name = 'OpenBCI_EEG'
        eeg_type = 'EEG'
        eeg_chan = self.eeg_channels
        eeg_hz = self.sample_rate
        eeg_data = 'double64'
        eeg_id = 'openbci_eeg_id'

        # create StreamInfo
        self.info_eeg = StreamInfo(eeg_name,
                                   eeg_type,
                                   eeg_chan,
                                   eeg_hz,
                                   eeg_data,
                                   eeg_id)

        # channel locations
        chns = self.info_eeg.desc().append_child('channels')
        if self.eeg_channels == 16:
            labels = ['Fp1', 'Fp2', 'C3', 'C4', 'T5', 'T6', 'O1',
                      'O2', 'F7', 'F8', 'F3', 'F4', 'T3', 'T4', 'P3', 'P4']
        else:
            labels = ['Fp1', 'Fp2', 'C3', 'C4', 'T5', 'T6', 'O1', 'O2']
        for label in labels:
            ch = chns.append_child("channel")
            ch.append_child_value('label', label)
            ch.append_child_value('unit', 'microvolts')
            ch.append_child_value('type', 'EEG')

        # additional Meta Data
        self.info_eeg.desc().append_child_value('manufacturer', 'OpenBCI Inc.')
        # create StreamOutlet
        self.outlet_eeg = StreamOutlet(self.info_eeg)

        print("--------------------------------------\n" +
              "LSL Configuration: \n" +
              "  Stream: \n" +
              "      Name: " + eeg_name + " \n" +
              "      Type: " + eeg_type + " \n" +
              "      Channel Count: " + str(eeg_chan) + "\n" +
              "      Sampling Rate: " + str(eeg_hz) + "\n" +
              "      Channel Format: " + eeg_data + " \n" +
              "      Source Id: " + eeg_id + " \n" +
              "Electrode Location Montage:\n" +
              str(labels) + "\n" +
              "---------------------------------------\n")

    def begin(self):
        print("\n-------------BEGIN---------------")
        # start streaming in a separate thread
        board_thread = threading.Thread(target=self.board.start_streaming,
                                        args=(self.send, -1))
        board_thread.daemon = True  # will stop on exit
        board_thread.start()
        print("Streaming data...")

        while True:
            s = input('--> ')
            if s == '/stop':
                break

        self.board.stop()
        time.sleep(2)
