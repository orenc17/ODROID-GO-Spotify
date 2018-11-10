import _thread
import spotipy
import network
import uQR
from odroid_go import GO
from microWebSrv import MicroWebSrv
from . import oauth2


WS_messages = False
srv_run_in_thread = True
ws_run_in_thread = False

response = None
waiting = True


# <IP>/TEST
@MicroWebSrv.route('/TEST')
def _httpHandlerTestGet(httpClient, httpResponse):
    global waiting
    global response
    response = httpClient.GetRequestQueryString()
    httpResponse.WriteResponseOk(headers=None, contentType="text/html", contentCharset="UTF-8",
                                 content="This is a test")
    waiting = False


def _acceptWebSocketCallback(webSocket, httpClient):
    if WS_messages:
        print("WS ACCEPT")
        if ws_run_in_thread or srv_run_in_thread:
            # Print thread list so that we can monitor maximum stack size
            # of WebServer thread and WebSocket thread if any is used
            _thread.list()
    webSocket.RecvTextCallback = _recvTextCallback
    webSocket.RecvBinaryCallback = _recvBinaryCallback
    webSocket.ClosedCallback = _closedCallback


def _recvTextCallback(webSocket, msg):
    if WS_messages:
        print("WS RECV TEXT : %s" % msg)
    webSocket.SendText("Reply for %s" % msg)


def _recvBinaryCallback(webSocket, data):
    if WS_messages:
        print("WS RECV DATA : %s" % data)


def _closedCallback(webSocket):
    if WS_messages:
        if ws_run_in_thread or srv_run_in_thread:
            _thread.list()
        print("WS CLOSED")


def paintQR(data):
    GO.lcd.clear()
    q = uQR.QRCode(border=8, box_size=20)
    q.add_data(data)
    q.make()
    matrix = q.get_matrix()
    scale = int(240 / len(matrix))
    for y in range(len(matrix) * scale):
        for x in range(len(matrix[0]) * scale):
            value = GO.lcd.BLACK if matrix[int(y / scale)][int(x / scale)] else GO.lcd.WHITE
            GO.lcd.pixel(x, y, value)


def prompt_for_user_token(client_id, client_secret, redirect_uri, scope=None, cache_path=".cache"):
    """
    prompts the user to login if necessary and returns
    the user token suitable for use with the spotipy.Spotify
    constructor

    Parameters:
     - client_id - the client id of your app
     - client_secret - the client secret of your app
     - redirect_uri - the redirect URI of your app
     - scope - the desired scope of the request
     - cache_path - path to location to save tokens
    """

    if not client_id or not client_secret or not redirect_uri:
        print('''
            You need to set your Spotify API credentials. You can do this by
            setting environment variables like so:

            Get your credentials at
                https://developer.spotify.com/my-applications
        ''')
        raise spotipy.SpotifyException(550, -1, 'no credentials set')

    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=cache_path)

    # try to get a valid token for this user, from the cache,
    # if not in the cache, the create a new (this will send
    # the user to a web page where they can authorize this app)

    token_info = sp_oauth.get_cached_token()
    if not token_info:
        try:
            mdns = network.mDNS()
            mdns.start('esp8266', 'esp8266')
            _ = mdns.addService('_http', '_tcp', 80, "esp8266")
        except Exception as e:
            print(e)
            raise

        srv = MicroWebSrv()
        srv.MaxWebSocketRecvLen = 256
        srv.WebSocketThreaded = ws_run_in_thread
        srv.WebSocketStackSize = 4096
        srv.AcceptWebSocketCallback = _acceptWebSocketCallback
        srv.Start(threaded=srv_run_in_thread, stackSize=8192)

        print('web server is ruunning')

        # ----------------------------------------------------------------------------

        auth_url = sp_oauth.get_authorize_url()
        paintQR(auth_url)
        print('''

User authentication requires interaction with your
web browser. Once you enter your credentials and
give authorization, you will be redirected to
a url.  Paste that url you were directed to to
complete the authorization.

Please scan QR code or navigate here:  %s


                ''' % auth_url)

        while waiting:
            continue

        print('finished waiting')

        mdns.stop()
        srv.Stop()
        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    # Auth'ed API request
    if token_info:
        return token_info['access_token'], sp_oauth
    else:
        return None, None
