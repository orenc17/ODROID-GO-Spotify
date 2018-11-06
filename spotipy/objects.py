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
    def __init__(self, height=0, width=0, url=None):
        self.height = height
        self.width = width
        self.url = url

    def download(self):
        if self.url:
            try:
                s = urequests.request('GET', self.url)
                # print('downloading image from {}'.format(self.url))
                # print('returned {}'.format(s.status_code))
                with open('image.jpg', 'wb') as fh:
                    fh.write(s.content)
                    s.close()
                return True
            except Exception:
                print(self.url)
        return False


class Album(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.artists = [Artist(**art) for art in kwargs['artists']]
        self.images = [Image(**img) for img in kwargs['images']]
        self.name = kwargs['name']


class Track(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.album = Album(**kwargs['album'])
        self.artists = [Artist(**art) for art in kwargs['artists']]
        self.duration = kwargs['duration_ms']
        self.name = kwargs['name']
