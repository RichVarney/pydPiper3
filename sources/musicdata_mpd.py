#!/usr/bin/python
# coding: UTF-8

# musicdata service to read from MPD
# Written by: Ron Ritchey


import json, mpd, threading, logging, queue, time, sys, getopt
from . import musicdata

class musicdata_mpd(musicdata.musicdata):



    def __init__(self, q, server='localhost', port=6600, pwd=''):
        super(musicdata_mpd, self).__init__(q)
        self.server = server
        self.port = port
        self.pwd = pwd
        self.connection_failed = 0
        self.timeout = 20
        self.idle_state = False

        self.dataclient = None

        # Now set up a thread to listen to the channel and update our data when
        # the channel indicates a relevant key has changed
        data_t = threading.Thread(target=self.run)
        data_t.daemon = True
        data_t.start()

        # Start the idle timer
        idle_t = threading.Thread(target=self.idlealert)
        idle_t.daemon = True
        idle_t.start()

    def idlealert(self):

        while True:
            # Generate a noidle event every timeout seconds
            time.sleep(self.timeout)

            if self.idle_state:
                try:
                    #self.dataclient.noidle()
                    self.dataclient._write_command("noidle")
                except (mpd.CommandError, NameError, mpd.ConnectionError, AttributeError):
                    # If not idle (or not created yet) return to sleeping
                    pass

    def connect(self):

        # Try up to 10 times to connect to MPD
        self.connection_failed = 0
        self.dataclient = None

        logging.debug("Connecting to MPD service on {0}:{1}".format(self.server, self.port))

        while True:
            if self.connection_failed >= 10:
                logging.debug("Could not connect to MPD")
                break
            try:
                # Connection to MPD
                client = mpd.MPDClient(use_unicode=True)
                client.connect(self.server, self.port)

                self.dataclient = client
                break
            except:
                self.dataclient = None
                self.connection_failed += 1
                time.sleep(1)
        if self.dataclient is None:
            raise mpd.ConnectionError("Could not connect to MPD")
        else:
            logging.debug("Connected to MPD")


    def run(self):

        logging.debug("MPD musicdata service starting")

        while True:
            if self.dataclient is None:
                try:
                    # Try to connect
                    self.connect()
                    self.status()
                    self.sendUpdate()
                except mpd.ConnectionError:
                    self.dataclient = None
                    # On connection error, sleep 5 and then return to top and try again
                    time.sleep(5)
                    continue


            try:
                # Wait for notice that state has changed
                self.idle_state = True
                msg = self.dataclient.idle()
                self.idle_state = False
                self.status()
                self.sendUpdate()
                time.sleep(.01)
            except mpd.ConnectionError:
                self.dataclient = None
                logging.debug("Could not get status from MPD")
                time.sleep(5)
                continue


    def status(self):
        # Read musicplayer status and update musicdata

        try:
            status = self.dataclient.status()
            current_song = self.dataclient.currentsong()
            playlist_info = self.dataclient.playlistinfo()
        except:
            # Caught something else.  Report it and then inform calling function that the connection is bad
            e = sys.exc_info()[0]
            logging.debug("Caught {0} trying to get status".format(e))
            raise RuntimeError("Could not get status from MPD")



        state = status.get('state')
        if state != "play":
            self.musicdata['state'] = "stop"
        else:
            self.musicdata['state'] = "play"

        # Update remaining variables
        self.musicdata['artist'] = current_song['artist'] if 'artist' in current_song else ""
        self.musicdata['title'] = current_song['title'] if 'title' in current_song else ""
        self.musicdata['album'] = current_song['album'] if 'album' in current_song else ""
        self.musicdata['volume'] = self.intn(status['volume']) if 'volume' in status else 0
        self.musicdata['repeat'] = bool(self.intn(status['repeat'])) if 'repeat' in status else False
        self.musicdata['random'] = bool(self.intn(status['random'])) if 'random' in status else False
        self.musicdata['single'] = bool(self.intn(status['single'])) if 'single' in status else False
        self.musicdata['uri'] = current_song['file'] if 'file' in current_song else ""


        # status['time'] is formatted as "current:duration" e.g. "24:243"
        # split time into current and duration
        temptime = status['time'] if 'time' in status else '0:0'
        (self.musicdata['elapsed'], self.musicdata['length']) = temptime.split(':')

        self.musicdata['elapsed'] = int(self.musicdata['elapsed'])
        self.musicdata['length'] = int(self.musicdata['length'])

        # for backwards compatibility
        self.musicdata['current'] = self.musicdata['elapsed']
        self.musicdata['duration'] = self.musicdata['length']

        self.musicdata['actPlayer'] = "MPD"
        self.musicdata['musicdatasource'] = "MPD"

        if self.musicdata['uri'].split(':')[0] == 'http':
            encoding = 'webradio'
        else:
            encoding = self.musicdata['uri'].split(':')[0]

        self.musicdata['encoding'] = encoding

        self.musicdata['bitrate'] = "{0} kbps".format(status['bitrate']) if 'bitrate' in status else ""

        plp = self.musicdata['playlist_position'] = int(status['song'])+1 if 'song' in status else 0
        plc = self.musicdata['playlist_length'] = int(status['playlistlength']) if 'playlistlength' in status else 0

        # For Backwards compatibility
        self.musicdata['playlist_count'] = self.musicdata['playlist_length']

        # If playlist is length 1 and the song playing is from an http source it is streaming
        if self.musicdata['encoding'] == 'webradio':
            self.musicdata['playlist_display'] = "Radio"
            if not self.musicdata['artist']:
                self.musicdata['artist'] = current_song['name'] if 'name' in current_song else ""
        else:
                self.musicdata['playlist_display'] = "{0}/{1}".format(self.musicdata['playlist_position'], self.musicdata['playlist_count'])

        audio = status['audio'] if 'audio' in status else None
        bitdepth = ""
        samplerate = ""
        chnum = 0

        if self.musicdata['encoding']:
            tracktype = self.musicdata['encoding']
        else:
            tracktype = "MPD"

        if audio is not None:
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

                tracktype = "{0} {1} {2} bit {3} kHz".format(self.musicdata['encoding'], channels, bits, sample).strip()

                bitdepth = "{0} bits".format(bits)
                samplerate = "{0} kHz".format(sample)

        self.musicdata['tracktype'] = tracktype
        self.musicdata['bitdepth'] = bitdepth
        self.musicdata['samplerate'] = samplerate
        self.musicdata['channels'] = chnum

        # if duration is not available, then suppress its display
        if int(self.musicdata['length']) > 0:
            timepos = time.strftime("%-M:%S", time.gmtime(int(self.musicdata['elapsed']))) + "/" + time.strftime("%-M:%S", time.gmtime(int(self.musicdata['length'])))
            remaining = time.strftime("%-M:%S", time.gmtime( int(self.musicdata['length']) - int(self.musicdata['elapsed']) ) )
        else:
            timepos = time.strftime("%-M:%S", time.gmtime(int(self.musicdata['elapsed'])))
            remaining = timepos

        self.musicdata['remaining'] = remaining
        self.musicdata['elapsed_formatted'] = timepos

        # For backwards compatibility
        self.musicdata['position'] = self.musicdata['elapsed_formatted']

        self.validatemusicvars(self.musicdata)


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename='musicdata_mpd.log', level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    # Suppress MPD libraries INFO messages
    loggingMPD = logging.getLogger("mpd")
    loggingMPD.setLevel( logging.WARN )

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hs:p:w:",["server=","port=","pwd="])
    except getopt.GetoptError:
        print('musicdata_mpd.py -s <server> -p <port> -w <password>')
        sys.exit(2)

    # Set defaults
    server = 'localhost'
    port = 6600
    pwd= ''

    for opt, arg in opts:
        if opt == '-h':
            print('musicdata_mpd.py -s <server> -p <port> -w <password>')
            sys.exit()
        elif opt in ("-s", "--server"):
            server = arg
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-w", "--pwd"):
            pwd = arg

    q = queue.Queue()
    mdr = musicdata_mpd(q, server, port, pwd)

    try:
        start = time.time()
        while True:
            if start+120 < time.time():
                break;
            try:
                item = q.get(timeout=1000)
                print("+++++++++")
                for k,v in item.items():
                    print("[{0}] '{1}' type {2}".format(k,v,type(v)))
                print("+++++++++")
                print()
                q.task_done()
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print('')
        pass

    print("Exiting...")
