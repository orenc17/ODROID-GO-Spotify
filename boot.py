import sys
sys.path[1] = '/flash/lib'
import network
import machine
import spotipy
import utime
import ujson
import uos
from odroid_go import GO
from spotidisplay import SpotiDisplay

# Spotify credentials

SPOTIFY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'http://esp8266.local/TEST'
SPOTIFY_SCOPE = 'streaming user-read-playback-state user-read-currently-playing user-modify-playback-state'


def do_connect():
    with open('/sd/wifi_db.json', 'r') as fp:
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


def sync_time():
    rtc = machine.RTC()
    rtc.ntp_sync(server="hr.pool.ntp.org")
    while not rtc.synced():
        continue

    print(utime.strftime("%a, %d %b %Y %H:%M:%S +0000", utime.localtime()))


def init_sd():
    uos.mountsd(True)
    if 'spotify_cache' not in uos.listdir('/sd'):
        uos.mkdir('/sd/spotify_cache')


def setup():
    GO.lcd.clear()
    GO.lcd.image(GO.lcd.CENTER, GO.lcd.CENTER, 'splash.jpg', 0, GO.lcd.JPG)
    init_sd()
    do_connect()
    sync_time()
    token, cred_manager = spotipy.prompt_for_user_token(client_id=SPOTIFY_CLIENT_ID,
                                                        client_secret=SPOTIPY_CLIENT_SECRET,
                                                        redirect_uri=SPOTIPY_REDIRECT_URI,
                                                        scope=SPOTIFY_SCOPE)

    assert token
    assert cred_manager
    return spotipy.Spotify(client_credentials_manager=cred_manager)


def main(sp):
    display = SpotiDisplay(sp)
    last_update_time = utime.ticks_ms()

    while True:
        utime.sleep_ms(500)
        GO.update()
        if display.device:
            if GO.btn_joy_y.was_axis_pressed() == 2:
                # print('pressed up')
                display.device.vol_increase(sp)
                continue
            if GO.btn_joy_y.was_axis_pressed() == 1:
                # print('pressed down')
                display.device.vol_decrease(sp)
                continue
            if GO.btn_joy_x.was_axis_pressed() == 2:
                # print('pressed right')
                display.device.previous_track(sp)
                display.update()
                continue
            if GO.btn_joy_x.was_axis_pressed() == 1:
                # print('pressed left')
                display.device.next_track(sp)
                display.update()
                continue
            if GO.btn_a.was_pressed() == 1:
                sp.pause_playback(display.device.id)
                continue
            if GO.btn_b.was_pressed() == 1:
                sp.start_playback(display.device.id)
                display.update()
                continue

        if utime.ticks_ms() - last_update_time > 5000:
            last_update_time = utime.ticks_ms()
            display.update()


if __name__ == "__main__":
    obj = setup()
    main(obj)

# Setup button
# a = Pin(32, Pin.IN, Pin.PULL_UP, handler=irq, debounce=500, trigger=Pin.IRQ_RISING, acttime=500)
# a = Pin(34, Pin.IN, handler=irq, debounce=0, trigger=Pin.IRQ_RISING, acttime=0)


