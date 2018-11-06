import sys
sys.path[1] = '/flash/lib'
import network
import spotipy
import utime
import ujson
import spotipy.util as util
from spotipy.objects import *
from odroid_go import GO

# Spotify credentials
SPOTIFY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'http://esp8266.local/'
SPOTIFY_SCOPE = 'streaming user-read-playback-state user-read-currently-playing user-modify-playback-state'


def do_connect():
    with open('wifi_db.json', 'r') as fp:
        db = ujson.load(fp)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    ssid = [s[0].decode("utf-8") for s in wlan.scan() if s[0].decode("utf-8") in db.keys()][0]
    if not wlan.isconnected():
        print('connecting to network %s' % ssid)
        wlan.connect(ssid, db[ssid])
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    return wlan


def update_display(trk, has_art):
    text_to_display = "{}\r\n\r\n{}\r\n\r\n{}".format(trk.artists[0].name,
                                                      trk.album.name,
                                                      trk.name)
    GO.lcd.clear()
    if has_art:
        GO.lcd.image(GO.lcd.RIGHT, GO.lcd.BOTTOM, 'image.jpg', 2, GO.lcd.JPG)
    GO.lcd.font(GO.lcd.FONT_DejaVu18, color=GO.lcd.GREEN)
    GO.lcd.text(0, 0, text_to_display)


def setup():
    GO.lcd.clear()
    GO.lcd.image(GO.lcd.CENTER, GO.lcd.CENTER, 'splash.jpg', 0, GO.lcd.JPG)
    interface = do_connect()
    token = util.prompt_for_user_token('',
                                       scope=SPOTIFY_SCOPE,
                                       client_id=SPOTIFY_CLIENT_ID,
                                       client_secret=SPOTIPY_CLIENT_SECRET,
                                       redirect_uri=SPOTIPY_REDIRECT_URI)
    assert token
    return spotipy.Spotify(auth=token)


def main(sp):
    status = sp.current_playback()
    track = Track(**status['item'])
    device = Device(**status['device'])

    has_art = track.album.images[0].download()
    update_display(track, has_art)
    last_update_time = utime.ticks_ms()

    while True:
        utime.sleep(1)
        GO.update()
        if GO.btn_joy_y.was_axis_pressed() == 2:
            # print('pressed up')
            device.vol_increase(sp)
            continue
        if GO.btn_joy_y.was_axis_pressed() == 1:
            # print('pressed down')
            device.vol_decrease(sp)
            continue
        if GO.btn_joy_x.was_axis_pressed() == 2:
            # print('pressed right')
            device.previous_track(sp)
            continue
        if GO.btn_joy_x.was_axis_pressed() == 1:
            # print('pressed left')
            device.next_track(sp)
            continue
        if GO.btn_a.was_pressed() == 1:
            sp.pause_playback(device.id)
            continue
        if GO.btn_b.was_pressed() == 1:
            sp.start_playback(device.id)
            continue

        if utime.ticks_ms() - last_update_time > 5000:
            last_update_time = utime.ticks_ms()
            status = sp.current_playback()
            if status:
                # print(status)
                new_track = Track(**status['item'])
                if new_track != track:
                    if new_track.album != track.album:
                        has_art = new_track.album.images[0].download()

                    track = new_track
                    update_display(track, has_art)


if __name__ == "__main__":
    main(setup())
