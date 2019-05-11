from odroid_go import GO
from spotipy.objects import *


class SpotiDisplay(object):
    def __init__(self, sp):
        self._sp = sp
        self.text = "Welcome to ODROID-GO \r\nSpotify Remote"
        self._text_x = GO.lcd.CENTER
        self._text_y = GO.lcd.CENTER
        self._displaying_art = False
        self.device = None
        self.track = None

        GO.lcd.clear()
        self._print_text()

    def _print_text(self):
        GO.lcd.font(GO.lcd.FONT_DejaVu18, color=GO.lcd.GREEN, transparent=True)
        GO.lcd.text(self._text_x, self._text_y, self.text)

    def _render_new_album_art(self, trk):
        GO.lcd.clear()
        self._update_song_details(trk)
        GO.lcd.image(GO.lcd.RIGHT, GO.lcd.BOTTOM,
                     trk.album.images[0].path,
                     2, GO.lcd.JPG)
        self._displaying_art = True

    def _update_song_details(self, trk):
        GO.lcd.textClear(self._text_x, self._text_y, self.text)
        self._text_x, self._text_y = 0, 0
        self.text = trk.display_str
        self._print_text()

    def _need_to_change_art(self, new_track):
        if self.track is None or new_track.album != self.track.album or not self._displaying_art:
            download_success = new_track.album.images[0].download()
            if not download_success and new_track.album != self.track.album:
                GO.lcd.clear()
            return download_success
        return False

    def update(self):
        status = self._sp.current_playback()
        if status:
            self.device = Device(**status['device'])
            new_track = Track(**status['item'])
            if new_track != self.track:
                if self._need_to_change_art(new_track):
                    self._render_new_album_art(new_track)
                else:
                    self._update_song_details(new_track)
                self.track = new_track
            else:
                if not self._displaying_art and \
                        self.track.album.images[0].download():
                    self._render_new_album_art(self.track)

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
