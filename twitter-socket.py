import socketio, os, tweepy, warnings
from aiohttp import web
from time import sleep
from threading import Thread, Event
from tweepy import RateLimitError
from datetime import datetime as dt

warnings.filterwarnings("ignore", category=RuntimeWarning)

API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']
API_ACCESS_TOKEN = os.environ['API_ACCESS_TOKEN']
API_ACCESS_TOKEN_SECRET = os.environ['API_ACCESS_TOKEN_SECRET']

# creates a new Async Socket IO Server
sio = socketio.AsyncServer()
# Creates a new Aiohttp Web Application
app = web.Application()
# Binds our Socket.IO server to our Web App
# instance
sio.attach(app)

# we can define aiohttp endpoints just as we normally
# would with no change
async def index(request):
    with open('template2.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

#initialize thread
thread = Thread()
thread_stop_event = Event()


class FollowerThread(Thread):
    def __init__(self, screenname):
        self.screenname = screenname
        # self.delay = 60
        super(FollowerThread, self).__init__()

    def dispCountdown(self, timer_start):
        t = timer_start
        while t>=0:
            mins, secs = divmod(t, 60)
            timeformat = '{:02.0f}:{:02.0f} - [{: <30s}]'.format(mins, secs, '|'*int(30*t/timer_start))
            print(timeformat, end='\r')
            sleep(1)
            t -= 1

    def getFollowers(self):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global API_KEY, API_SECRET, API_ACCESS_TOKEN, API_ACCESS_TOKEN_SECRET

        auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        auth.set_access_token(API_ACCESS_TOKEN, API_ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=False, wait_on_rate_limit_notify=True, compression=True)
       
        u = api.get_user(screen_name = self.screenname)
        num_followers = u.followers_count

        all_followers = dict()
        i = 0
        while not thread_stop_event.isSet():
            try:
                for follower in tweepy.Cursor(api.followers, screen_name=self.screenname).items():
                    got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                        "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                            "is_verified":follower.verified, "image":follower.profile_image_url}
                    all_followers[got_follower["id"]] = got_follower
                    i+=1

                    # print(got_follower)
            except RateLimitError:
                print(f"Grabbed {len(all_followers)} followers. Waiting for timeout...")
                sio.emit('followers', all_followers)
                timeout_ends = dt.fromtimestamp(api.rate_limit_status()['resources']['followers']['/followers/list']['reset'])
                time_left = (timeout_ends - dt.now()).total_seconds()
                self.dispCountdown(time_left)

                if i >= num_followers: thread_stop_event.set()
                else: continue


    def run(self):
        self.getFollowers()


@sio.on('connect')
def test_connect(socket_name, socket_headers):
    print(socket_name)#, socket_headers)
    # # need visibility of the global thread object
    sio.send("hi")
    global thread
    print('Client connected')

    if not thread.isAlive():
        print("Starting Thread")
        thread = FollowerThread('contrapoints')
        thread.start()

# We bind our aiohttp endpoint to our app
# router
app.router.add_get('/', index)

# We kick off our server
if __name__ == '__main__':
    # sio.connect('http://localhost:8080')
    web.run_app(app)