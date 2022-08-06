import math

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, \
    QLabel, QStyle, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt

from app.editor import timer

from app import pygame_audio

class AudioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = self.window._data
        self.current = None

        self.setMaximumHeight(70)
        self.play_on_release = False

        self.playing: bool = False
        self.paused: bool = False
        self.loop: bool = False

        self.start_time = 0
        self.duration = 0

        self.music_player = pygame_audio.get_player()
        self.music_player.set_volume(.5)

        self.play_button = QToolButton(self)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_clicked)

        self.loop_button = QToolButton(self)
        self.loop_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.loop_button.clicked.connect(self.loop_clicked)
        self.loop_button.setCheckable(True)

        self.time_slider = QSlider(Qt.Horizontal, self)
        self.time_slider.setRange(0, 1)
        self.time_slider.setValue(0)
        self.time_slider.sliderPressed.connect(self.slider_pressed)
        self.time_slider.sliderReleased.connect(self.slider_released)

        self.time_label = QLabel("00:00 / 00:00")

        layout = QVBoxLayout()
        hbox_layout = QHBoxLayout()
        self.setLayout(layout)

        hbox_layout.addWidget(self.play_button)
        hbox_layout.addWidget(self.loop_button)
        hbox_layout.setAlignment(Qt.AlignLeft)

        second_hbox_layout = QHBoxLayout()
        second_hbox_layout.addLayout(hbox_layout)
        self.nid_label = QLabel("")
        self.nid_label.setStyleSheet("font-weight: bold")
        self.nid_label.setAlignment(Qt.AlignCenter)
        second_hbox_layout.addWidget(self.nid_label)
        layout.addLayout(second_hbox_layout)

        time_layout = QHBoxLayout()
        time_layout.setAlignment(Qt.AlignTop)
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.time_label)
        layout.addLayout(time_layout)

        self.play_button.setEnabled(False)
        self.time_slider.setEnabled(False)

        timer.get_timer().tick_elapsed.connect(self.tick)

    def set_label(self, val):
        minutes = int(val / 1000 / 60)
        seconds = int(val / 1000 % 60)
        thru_song = "%02d:%02d" % (minutes, seconds)
        minutes = int(self.duration / 1000 / 60)
        seconds = math.ceil(self.duration / 1000 % 60)
        song_length = "%02d:%02d" % (minutes, seconds)
        self.time_label.setText(thru_song + " / " + song_length)

    def null_slider(self):
        self.time_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def tick(self):
        if self.paused:
            self.duration = self.music_player.get_length()
            val = float(self.time_slider.value())
            self.set_label(val)
        elif self.playing:
            val = self.music_player.get_position()
            if val == -1:
                self.stop()
                return
            self.duration = self.music_player.get_length()
            val %= self.duration
            self.time_slider.setValue(val)
            self.set_label(val)
        else:
            pass

    def stop(self):
        self.paused = False
        self.stop_sfx()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.null_slider()

    def pause(self):
        self.paused = True
        self.pause_sfx()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def play(self):
        self.paused = False
        self.play_sfx(self.current)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def set_current(self, current):
        self.stop_sfx()
        self.current = current
        self.nid_label.setText(self.current.nid)
        self.play_button.setEnabled(True)
        self.time_slider.setEnabled(True)
        
    def play_clicked(self):
        if self.playing:
            self.pause()
        elif self.current:
            self.play()

    def loop_clicked(self, val):
        self.loop = val

    def slider_pressed(self):
        if not self.paused:
            self.pause()
            self.play_on_release = True
        self.music_player.preset_position()

    def slider_released(self):
        cur = float(self.time_slider.value())
        print("Slider Released: %s" % cur)
        self.music_player.set_position(cur)
        if self.play_on_release:
            self.play()
        else:
            self.paused = False
        self.play_on_release = False

    def play_sfx(self, sfx):
        fn = sfx.full_path
        new_song = self.music_player.play(fn, self.loop)
        self.duration = self.music_player.get_length()
        if new_song:
            self.time_slider.setRange(0, self.duration)
            print("Time Slider Maximum: %d" % self.time_slider.maximum())
            self.time_slider.setValue(0)        
        self.playing = True

    def pause_sfx(self):
        self.playing = False
        self.music_player.pause()

    def stop_sfx(self):
        self.playing = False
        self.music_player.stop()

    def find_length(self, sfx):
        return self.music_player.find_length(sfx)
