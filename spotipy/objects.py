import uos
from . import urequests


class Item(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']

    def __eq__(self, other):
        if other is not None and hasattr(other, 'id'):
            return self.id == other.id
        return False


class Device(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.name = kwargs['name']
        self.is_active = kwargs['is_active']
        self.volume = kwargs['volume_percent']

    def _vol_change(self, sp):
        sp.volume(self.volume, self.id)

    def vol_increase(self, sp):
        self.volume += 5
        if self.volume > 100:
            self.volume = 100
        self._vol_change(sp)

    def vol_decrease(self, sp):
        self.volume -= 5
        if self.volume < 0:
            self.volume = 0
        self._vol_change(sp)

    def next_track(self, sp):
        sp.next_track(device_id=self.id)

    def previous_track(self, sp):
        sp.previous_track(device_id=self.id)


class Artist(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.name = kwargs['name']


class Image(object):
    def __init__(self, height=0, width=0, url=None, album_id=None):
        self.height = height
        self.width = width
        self.url = url
        self.path = '/sd/spotify_cache/%s' % album_id

    def download(self, cb):
        if self.url:
            try:
                s = urequests.request('GET', self.url)
                with open(self.path, 'wb') as fh:
                    fh.write(s.content)
                    s.close()
                if cb:
                    cb(self.path)
                return True
            except Exception:
                print("Failed to download %s" % self.url)
        return False

    def exists(self):
        try:
            uos.stat(self.path)
            return True
        except Exception:
            return False


class Album(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.artists = [Artist(**art) for art in kwargs['artists']]
        self.images = [Image(**img, album_id=self.id) for img in kwargs['images']]
        self.name = kwargs['name']


class Track(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.album = Album(**kwargs['album'])
        self.artists = [Artist(**art) for art in kwargs['artists']]
        self.duration = kwargs['duration_ms']
        self.name = kwargs['name']

    @staticmethod
    def printable_str(string):
        if len(string) > 30:
            return string[:27] + "..."
        return string

    @property
    def display_str(self):
        return "{}\n\n{}\n\n{}".format(
            self.printable_str(self.artists[0].name),
            self.printable_str(self.album.name),
            self.printable_str(self.name)
        )
