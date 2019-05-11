from odroid_go import GO
import uasyncio as asyncio
from spotipy.objects import *


class SpotiDisplay(object):
    def __init__(self, sp):
        self._sp = sp
        self.text = ""
        self._text_x = 0
        self._text_y = 0
        self._displaying_art = False
        self.device = None
        self.track = None

    def _print_text(self):
        GO.lcd.font(GO.lcd.FONT_DejaVu18, color=GO.lcd.GREEN, transparent=True)
        GO.lcd.text(self._text_x, self._text_y, self.text)

    def on_finish_download(self, path):
        if self.track.album.images[0].path == path:
            self.print_art(path)

    def _render_album_art(self, trk):
        if not trk.album.images[0].exists():
            loop = asyncio.get_event_loop()
            loop.call_soon(trk.album.images[0].download, self.on_finish_download)
            self._displaying_art = False
        else:
            if self.track is None or \
                    trk.album != self.track.album or \
                    not self._displaying_art:
                self.print_art(trk.album.images[0].path)
                self._displaying_art = True

    def print_art(self, art_path):
        # GO.lcd.image(GO.lcd.RIGHT, GO.lcd.BOTTOM,
        #              art_path, 2, GO.lcd.JPG)
        GO.lcd.image(132, 99, art_path, 2, GO.lcd.JPG)
        self._displaying_art = True

    def _update_song_details(self, trk):
        GO.lcd.clear()
        self._text_x, self._text_y = 0, 0
        self.text = trk.display_str
        self._print_text()

    def update(self):
        status = self._sp.current_playback()
        if status:
            self.device = Device(**status['device'])
            new_track = Track(**status['item'])
            if new_track != self.track:
                self._update_song_details(new_track)
                self._render_album_art(new_track)
                self.track = new_track
            else:
                if not self._displaying_art and \
                        self.track.album.images[0].exists():
                    self._render_album_art(self.track)

    def next_track(self):
        if self.device:
            self.device.next_track(self._sp)

    def prev_track(self):
        if self.device:
            self.device.previous_track(self._sp)

    def pause(self):
        if self.device:
            self._sp.pause_playback(self.device.id)

    def play(self):
        if self.device:
            self._sp.start_playback(self.device.id)

    def vol_up(self):
        if self.device:
            self.device.vol_increase(self._sp)

    def vol_down(self):
        if self.device:
            self.device.vol_decrease(self._sp)
