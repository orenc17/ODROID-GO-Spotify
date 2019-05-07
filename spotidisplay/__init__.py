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
        self._has_art = False

        GO.lcd.clear()
        self._print_text()
        self.update()

    def _print_text(self):
        GO.lcd.font(GO.lcd.FONT_DejaVu18, color=GO.lcd.GREEN, transparent=True)
        GO.lcd.text(self._text_x, self._text_y, self.text)

    def _render_new_album_art(self):
        GO.lcd.clear()
        GO.lcd.image(GO.lcd.RIGHT, GO.lcd.BOTTOM,
                     self.track.album.images[0].path,
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
                    self._render_new_album_art()
                self._update_song_details(new_track)
                self.track = new_track
            else:
                if not self._displaying_art and self.track.album.images[0].download():
                    self._render_new_album_art()

