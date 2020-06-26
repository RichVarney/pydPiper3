#!/usr/bin/python
# coding: UTF-8

# musicdata service to read from RuneAudio
# Written by: Ron Ritchey


import json, redis, threading, logging, queue, time, getopt, sys, logging
from . import musicdata

class musicdata_rune(musicdata.musicdata):

    def __init__(self, q, server='localhost', port=6379, pwd=''):
        super(musicdata_rune, self).__init__(q)
        self.server = server
        self.port = port
        self.pwd = pwd
        self.connection_failed = 0

        self.dataclient = None

        # Now set up a thread to listen to the channel and update our data when
        # the channel indicates a relevant key has changed
        data_t = threading.Thread(target=self.run)
        data_t.daemon = True
        data_t.start()


    def connect(self):

        # Try up to 10 times to connect to REDIS
        self.connection_failed = 0

        logging.debug("Connecting to Rune Redis service on {0}:{1}".format(self.server, self.port))

        while True:
            if self.connection_failed >= 10:
                logging.debug("Could not connect to Rune Redis service")
                raise RuntimeError("Could not connect to Rune Redis service")
            try:
                # Connection to REDIS
                client = redis.StrictRedis(self.server, self.port, self.pwd)

                # Configure REDIS to send keyspace messages for set events
                client.config_set('notify-keyspace-events', 'KEA')
                self.dataclient = client
                logging.debug("Connected to Rune Redis service")
                break
            except:
                self.dataclient = None
                self.connection_failed += 1
                time.sleep(1)


    def subscribe(self):
        # Try to subscribe.  If you fail, reconnect and try again.
        # If you fail, allow the resulting exception to be passed on.

        try:
            # Create a pubsub to receive messages
            self.pubsub = self.dataclient.pubsub(ignore_subscribe_messages=True)

            # Subscribe to act_player_info keyspace events
            self.pubsub.psubscribe('__key*__:act_player_info')
        except redis.ConnectionError:
            self.connect()

            # Try again to subscribe
            # Create a pubsub to receive messages
            self.pubsub = self.dataclient.pubsub(ignore_subscribe_messages=True)

            # Subscribe to act_player_info keyspace events
            self.pubsub.subscribe('__key*__:act_player_info')

    def run(self):

        logging.debug("RUNE musicdata service starting")

        while True:
            if self.dataclient is None:
                try:
                    # Try to connect
                    self.connect()
                    self.subscribe()
                    self.status()
                    self.sendUpdate()
                except (redis.ConnectionError, RuntimeError):
                    self.dataclient = None
                    # On connection error, sleep 5 and then return to top and try again
                    time.sleep(5)
                    continue
            try:
                # Wait for notice that key has changed
                msg = self.pubsub.get_message()
                if msg:
                    # act_player_info key event occured
                    self.status()
                    self.sendUpdate()
                time.sleep(.01)
            except (redis.ConnectionError, RuntimeError):
                # if we lose our connection while trying to query DB
                # sleep 5 and then return to top to try again
                self.dataclient = None
                logging.debug("Could not get status from Rune Redis service")
                time.sleep(5)
                continue


    def status(self):
        # Read musicplayer status and update musicdata
        try:
            msg = self.dataclient.get('act_player_info')
            status = json.loads(msg)
        except ValueError:
            logging.debug("Bad status message received.  Contents were {0}".format(msg))
            raise RuntimeError("Bad status message received.")
        except:
            # Caught something else.  Report it and then inform calling function that the connection is bad
            e = sys.exc_info()[0]
            logging.debug("Caught {0} trying to get status from Rune".format(e))
            raise RuntimeError("Could not get status from Rune")



        state = status.get('state')
        if state != "play":
            self.musicdata['state'] = "stop"
        else:
            self.musicdata['state'] = "play"

        # Update remaining variables
        self.musicdata['artist'] = status['currentartist'] if 'currentartist' in status else ""
        self.musicdata['title'] = status['currentsong'] if 'currentsong' in status else ""
        self.musicdata['album'] = status['currentalbum'] if 'currentalbum' in status else ""
        self.musicdata['volume'] = self.intn(status['volume']) if 'volume' in status else 0
        self.musicdata['length'] = self.intn(status['time']) if 'time' in status else 0
        self.musicdata['elapsed'] = self.intn(status['elapsed']) if 'elapsed' in status else 0
        self.musicdata['actPlayer'] = status['actPlayer'] if 'actPlayer' in status else ""
        self.musicdata['single'] = bool(self.intn(status['single'])) if 'single' in status else False
        self.musicdata['random'] = bool(self.intn(status['random'])) if 'random' in status else False
        self.musicdata['repeat'] = bool(self.intn(status['repeat'])) if 'repeat' in status else False
        self.musicdata['musicdatasource'] = "Rune"

        # For backwards compatibility
        self.musicdata['duration'] = self.musicdata['length']
        self.musicdata['current'] = self.musicdata['elapsed']

        # Set default values
        self.musicdata['samplerate'] = ""
        self.musicdata['bitrate'] = ""
        self.musicdata['channels'] = 0
        self.musicdata['bitdepth'] = ""
        self.musicdata['tracktype'] = ""
        self.musicdata['encoding'] = ""
        self.musicdata['tracktype'] = ""

        if self.musicdata['actPlayer'] == 'Spotify':
            self.musicdata['bitrate'] = "320 kbps"
            plp = self.musicdata['playlist_position'] = self.intn(status['song'])+1 if 'song' in status else 0
            plc = self.musicdata['playlist_length'] = self.intn(status['playlistlength']) if 'playlistlength' in status else 0

            # For backwards compatibility
            self.musicdata['playlist_count'] = self.musicdata['playlist_length']

            self.musicdata['playlist_display'] = "{0}/{1}".format(plp, plc)
            self.musicdata['actPlayer'] = "Spotify"
            self.musicdata['tracktype'] = "Spotify"
            self.musicdata['stream'] = 'not webradio'

        elif self.musicdata['actPlayer'] == 'MPD':
            plp = self.musicdata['playlist_position'] = self.intn(status['song'])+1 if 'song' in status else 0
            plc = self.musicdata['playlist_length'] = self.intn(status['playlistlength']) if 'playlistlength' in status else 0

            # For backwards compatibility
            self.musicdata['playlist_count'] = self.musicdata['playlist_length']

            self.musicdata['bitrate'] = "{0} kbps".format(status['bitrate']) if 'bitrate' in status else ""

            # if radioname is None then this is coming from a playlist (e.g. not streaming)
            if status.get('radioname') == None:
                self.musicdata['playlist_display'] = "{0}/{1}".format(plp, plc)
                self.musicdata['stream'] = 'not webradio'
            else:
                self.musicdata['playlist_display'] = "Radio"
                self.musicdata['stream'] = 'webradio'
                # if artist is empty, place radioname in artist field
                if self.musicdata['artist'] == "" or self.musicdata['artist'] is None:
                    self.musicdata['artist'] = status['radioname'] if 'radioname' in status else ""


            audio = status['audio'] if 'audio' in status else None
            chnum = 0
            if audio is None:
                tracktype = "MPD"
            else:
                audio = audio.split(':')
                if len(audio) == 3:
                    sample = round(float(audio[0])/1000,1)
                    bits = audio[1]
                    chnum = int(audio[2])
                    if audio[2] == '1':
                        channels = 'Mono'
                    elif audio[2] == '2':
                        channels = 'Stereo'
                    elif int(audio[2]) > 2:
                        channels = 'Multi'
                    else:
                        channels = ""

                    if channels == "":
                        tracktype = "{0} bit, {1} kHz".format(bits, sample)
                    else:
                        tracktype = "{0} {1} bit {2} kHz".format(channels, bits, sample)
                else:
                    # If audio information not available just send that MPD is the source
                    tracktype = "MPD"

            self.musicdata['tracktype'] = tracktype
            self.musicdata['channels'] = chnum

        elif self.musicdata['actPlayer'] == 'Airplay':
            self.musicdata['playlist_position'] = 1
            self.musicdata['playlist_count'] = 1
            self.musicdata['playlist_length'] = 1
            self.musicdata['tracktype'] = "Airplay"
            self.musicdata['playlist_display'] = "Aplay"
            self.musicdata['stream'] = 'not webradio'
        
        else:
            # Unexpected player type
            logging.debug("Unexpected player type {0} discovered".format(actPlayer))
            self.musicdata['playlist_position'] = 1
            self.musicdata['playlist_count'] = 1
            self.musicdata['playlist_length'] = 1
            self.musicdata['tracktype'] = actPlayer
            self.musicdata['playlist_display'] = "Radio"
            self.musicdata['stream'] = 'webradio'

        # if duration is not available, then suppress its display
        if int(self.musicdata['length']) > 0:
            timepos = time.strftime("%-M:%S", time.gmtime(int(self.musicdata['elapsed']))) + "/" + time.strftime("%-M:%S", time.gmtime(int(self.musicdata['length'])))
            remaining = time.strftime("%-M:%S", time.gmtime( int(self.musicdata['length']) - int(self.musicdata['elapsed']) ) )
        else:
            timepos = time.strftime("%-M:%S", time.gmtime(int(self.musicdata['elapsed'])))
            remaining = timepos

        self.musicdata['remaining'] = remaining.decode()
        self.musicdata['elapsed_formatted'] = timepos.decode()

        # For backwards compatibility
        self.musicdata['position'] = self.musicdata['elapsed_formatted']

        self.validatemusicvars(self.musicdata)


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename='musicdata_rune.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hs:p:w:",["server=","port=","pwd="])
    except getopt.GetoptError:
        print('musicdata_rune.py -s <server> -p <port> -w <password>')
        sys.exit(2)

    # Set defaults
    server = 'localhost'
    port = 6379
    pwd= ''

    for opt, arg in opts:
        if opt == '-h':
            print('musicdata_rune.py -s <server> -p <port> -w <password>')
            sys.exit()
        elif opt in ("-s", "--server"):
            server = arg
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-w", "--pwd"):
            pwd = arg


    import sys
    q = queue.Queue()
    mdr = musicdata_rune(q, server, port, pwd)

    try:
        start = time.time()
        while True:
            if start+120 < time.time():
                break;
            try:
                item = q.get(timeout=1000)
                print("++++++++++")
                for k,v in item.items():
                    print("[{0}] '{1}' type {2}".format(k,v,type(v)))
                print("++++++++++")
                print()
                q.task_done()
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print('')
        pass

    print("Exiting...")
