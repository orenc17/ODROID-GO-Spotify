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
    GO.lcd.font(GO.lcd.FONT_DejaVu18, color=GO.lcd.GREEN)
    if has_art:
        GO.lcd.image(GO.lcd.RIGHT, GO.lcd.BOTTOM, 'image.jpg', 2, GO.lcd.JPG)
        GO.lcd.text(0, 0, text_to_display)
    else:
        GO.lcd.text(GO.lcd.CENTER, GO.lcd.CENTER, text_to_display)


def update_status(sp, curr_track, has_art):
    status = sp.current_playback()
    if status:
        device = Device(**status['device'])
        new_track = Track(**status['item'])
        if new_track != curr_track:
            if curr_track is None or new_track.album != curr_track.album or not has_art:
                has_art = new_track.album.images[0].download()
            update_display(new_track, has_art)
        return new_track, has_art, device
    return None, False, None


def setup():
    GO.lcd.clear()
    GO.lcd.image(GO.lcd.CENTER, GO.lcd.CENTER, 'splash.jpg', 0, GO.lcd.JPG)
    do_connect()
    token, cred_manager = util.prompt_for_user_token('',
                                                     scope=SPOTIFY_SCOPE,
                                                     client_id=SPOTIFY_CLIENT_ID,
                                                     client_secret=SPOTIPY_CLIENT_SECRET,
                                                     redirect_uri=SPOTIPY_REDIRECT_URI)
    assert token
    assert cred_manager
    return spotipy.Spotify(client_credentials_manager=cred_manager)


def main(sp):
    track, has_art, device = update_status(sp, None, False)
    last_update_time = utime.ticks_ms()
    update_display(track, has_art)

    while True:
        utime.sleep_ms(500)
        GO.update()
        if device:
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
                track, has_art, device = update_status(sp, track, has_art)
                continue
            if GO.btn_joy_x.was_axis_pressed() == 1:
                # print('pressed left')
                device.next_track(sp)
                track, has_art, device = update_status(sp, track, has_art)
                continue
            if GO.btn_a.was_pressed() == 1:
                sp.pause_playback(device.id)
                continue
            if GO.btn_b.was_pressed() == 1:
                sp.start_playback(device.id)
                track, has_art, device = update_status(sp, track, has_art)
                continue

        if utime.ticks_ms() - last_update_time > 5000:
            last_update_time = utime.ticks_ms()
            track, has_art, device = update_status(sp, track, has_art)


if __name__ == "__main__":
    obj = setup()
    main(obj)
