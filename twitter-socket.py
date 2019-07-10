import socketio, os, tweepy
from aiohttp import web
from time import sleep
from threading import Thread, Event

API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']

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
        self.delay = 60
        super(FollowerThread, self).__init__()

    def getFollowers(self):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global API_KEY, API_SECRET

        auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
       
        u = api.get_user(screen_name = self.screenname)
        num_followers = u.followers_count
        # on_break = #!check tweepy

        while not thread_stop_event.isSet():
            all_followers = dict()
            i = 0
            for follower in tweepy.Cursor(api.followers, screen_name=self.screenname).items():
                got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                    "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                        "is_verified":follower.verified, "image":follower.profile_image_url}
                all_followers[got_follower["id"]] = got_follower
                i+=1

                print(got_follower)

            sio.emit('followers', all_followers)
            sleep(self.delay)

            if i >= num_followers: thread_stop_event.set()

    def run(self):
        self.getFollowers()


@sio.on('connect')
def test_connect(socket_name, socket_headers):
    print(socket_name)#, socket_headers)
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = FollowerThread('contrapoints')
        thread.start()

# We bind our aiohttp endpoint to our app
# router
app.router.add_get('/', index)

# We kick off our server
if __name__ == '__main__':
    web.run_app(app)