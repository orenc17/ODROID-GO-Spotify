import sys
sys.path[1] = '/flash/lib'
import network
import machine
import spotipy
import utime
import ujson
import uos
import uasyncio as asyncio
from uasyncio.queues import Queue
from odroid_go import GO
from spotidisplay import SpotiDisplay

# Spotify credentials

SPOTIFY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''
SPOTIPY_REDIRECT_URI = 'http://esp8266.local/TEST'
SPOTIFY_SCOPE = 'streaming user-read-playback-state user-read-currently-playing user-modify-playback-state'

COMMAND_CONTROL_PLAY = 1
COMMAND_CONTROL_PAUSE = 2
COMMAND_CONTROL_NEXT = 3
COMMAND_CONTROL_PREV = 4
COMMAND_VOL_UP = 5
COMMAND_VOL_DOWN = 6
COMMAND_UPDATE = 7


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
    token, cred_manager = spotipy.prompt_for_user_token(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE
    )

    assert token
    assert cred_manager
    return spotipy.Spotify(client_credentials_manager=cred_manager)


async def controls_thread(q):
    while True:
        await asyncio.sleep_ms(250)
        GO.update()
        if GO.btn_joy_y.was_axis_pressed() == 2:
            # print('pressed up')
            await q.put(COMMAND_VOL_UP)
            continue
        if GO.btn_joy_y.was_axis_pressed() == 1:
            # print('pressed down')
            await q.put(COMMAND_VOL_DOWN)
            continue
        if GO.btn_joy_x.was_axis_pressed() == 2:
            # print('pressed right')
            await q.put(COMMAND_CONTROL_PREV)
            await q.put(COMMAND_UPDATE)
            continue
        if GO.btn_joy_x.was_axis_pressed() == 1:
            # print('pressed left')
            await q.put(COMMAND_CONTROL_NEXT)
            await q.put(COMMAND_UPDATE)
            continue
        if GO.btn_a.was_pressed() == 1:
            await q.put(COMMAND_CONTROL_PAUSE)
            continue
        if GO.btn_b.was_pressed() == 1:
            await q.put(COMMAND_CONTROL_PLAY)
            await q.put(COMMAND_UPDATE)
            continue


async def update_periodically(q):
    while True:
        await q.put(COMMAND_UPDATE)
        await asyncio.sleep_ms(5000)


async def spotify_requests_handler(q):
    while True:
        result = await(q.get())
        if result == COMMAND_CONTROL_PLAY:
            display.play()
        elif result == COMMAND_CONTROL_PAUSE:
            display.pause()
        elif result == COMMAND_CONTROL_NEXT:
            display.next_track()
        elif result == COMMAND_CONTROL_PREV:
            display.prev_track()
        elif result == COMMAND_VOL_UP:
            display.vol_up()
        elif result == COMMAND_VOL_DOWN:
            display.vol_down()
        elif result == COMMAND_UPDATE:
            display.update()


sp = setup()
display = SpotiDisplay(sp)

Engineq = Queue()

loop = asyncio.get_event_loop()
loop.create_task(spotify_requests_handler(Engineq))
loop.create_task(update_periodically(Engineq))
loop.create_task(controls_thread(Engineq))
loop.run_forever()
