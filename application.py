#####################################################
####################### CONFIG ######################
#####################################################

from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event
from collections import deque
import os, tweepy

API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']
API_ACCESS_TOKEN = os.environ['API_ACCESS_TOKEN']
API_ACCESS_TOKEN_SECRET = os.environ['API_ACCESS_TOKEN_SECRET']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(API_ACCESS_TOKEN, API_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)


target_user = 'contrapoints' #! change to actual target user

#####################################################
################## THREADING SET-UP #################
#####################################################

#turn the flask app into a socketio app
socketio = SocketIO(app)

#Get followers of target account
follower_thread = Thread()
follower_thread_stop_event = Event()

#Get 'friends' - i.e. people you follow
friend_thread = Thread()
friend_thread_stop_event = Event()

#Send follower data to frontend
follower_send_thread = Thread()
follower_send_thread_stop_event = Event()

#Send friend data to frontend
friend_send_thread = Thread()
friend_send_thread_stop_event = Event()

#initialize a queue to add things into
FOLLOWER_QUEUE = deque()
FRIEND_QUEUE = deque()
USER_DATA = {"username":target_user}


#####################################################
################# THREAD DEFINITIONS ################
#####################################################

class FollowerThread(Thread):
    def __init__(self, screenname):
        # self.delay = 1
        self.screenname = screenname
        super(FollowerThread, self).__init__()

    def GetFollowers(self):
        """
        Because the Twitter API will time out very quickly for targets with large
        followings but can be configured to just wait out the rate limit rather
        than throwing an error, we here capture the follower data as it is received
        and add it to a queue that can be pulled from to send to the frontend.
        """

        # print("Let's heckin do this.")

        global auth, api, FOLLOWER_QUEUE, USER_DATA
       
        u = api.get_user(screen_name = self.screenname)
        num_followers = u.followers_count
        num_status = u.statuses_count
        USER_DATA["num_followers"] = num_followers
        USER_DATA["num_status"] = num_status
        all_followers = dict()
        i = 0

        while not follower_thread_stop_event.isSet():
            for follower in tweepy.Cursor(api.followers, screen_name=self.screenname).items():
                got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                    "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                        "is_verified":follower.verified, "image":follower.profile_image_url}
                all_followers[got_follower["id"]] = got_follower
                i+=1

                FOLLOWER_QUEUE.appendleft(got_follower) #! enqueue followers in this thread; dequeue in a seperate thread
                print(f"i={i}\nqueue length={len(FOLLOWER_QUEUE)}\n{got_follower}\n\n")

            if i >= num_followers: follower_thread_stop_event.set()

    def run(self):
        self.GetFollowers()

class FriendThread(Thread):
    def __init__(self):
        # self.delay = 1
        # self.screenname = screenname
        super(FriendThread, self).__init__()

    def GetFriends(self):
        """
        Because the Twitter API will time out very quickly for targets with large
        'friend' groups but can be configured to just wait out the rate limit rather
        than throwing an error, we here capture the friend data as it is received
        and add it to a queue that can be pulled from to send to the frontend.
        """

        global auth, api, FRIEND_QUEUE, USER_DATA
       
        u = api.me()
        num_friends = u.friends_count
        # USER_DATA["num_friends"] = num_friends
        all_friends = []
        j = 0

        while not follower_thread_stop_event.isSet():
            for friend in tweepy.Cursor(api.friends, id=u.id_str).items():
                # got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                #     "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                #         "is_verified":follower.verified, "image":follower.profile_image_url}
                all_friends.append(friend.id_str)
                j+=1

                FRIEND_QUEUE.appendleft(friend.id_str) #! enqueue followers in this thread; dequeue in a seperate thread
                print(f"j={j}\nfriend queue length={len(FRIEND_QUEUE)}\n{friend.screen_name}\n\n")

            if j >= num_friends: follower_send_thread_stop_event.set()

    def run(self):
        self.GetFriends()

class SenderThread_Follower(Thread):
    def __init__(self):
        self.delay = 1.5
        super(SenderThread_Follower, self).__init__()

    def SendData(self):
        """
        Pull from the queue of followers and send them to the frontend.
        """

        global FOLLOWER_QUEUE
        #infinite loop of magical random numbers
        # print("Making random numbers")
        while not follower_thread_stop_event.isSet():
            if len(FOLLOWER_QUEUE) > 0:
                follower = FOLLOWER_QUEUE.pop()
                print(f"\n\nDequeued follower:\n{follower}\nNum left in queue:{len(FOLLOWER_QUEUE)}")
                socketio.emit('newfollower', {'follower': follower}, namespace='/test')
            else: pass
            sleep(self.delay)

    def run(self):
        self.SendData()

class SenderThread_Friend(Thread):
    def __init__(self):
        self.delay = 1.5
        super(SenderThread_Friend, self).__init__()

    def SendData(self):
        """
        Pull from the queue of friends and send them to the frontend.
        """

        global FRIEND_QUEUE

        while not friend_thread_stop_event.isSet():
            if len(FRIEND_QUEUE) > 0:
                friend = FRIEND_QUEUE.pop()
                print(f"\n\nDequeued friend id:\n{friend}\nNum left in queue:{len(FRIEND_QUEUE)}")
                socketio.emit('newfriend', {'friend_id': friend}, namespace='/test')
            else: pass
            sleep(self.delay)

    def run(self):
        self.SendData()


#####################################################
#################### PAGE ROUTES ####################
#####################################################

@app.route('/')
def index():
    """Render the main page of the app."""

    return render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    """Code to be run when the browser connects to the web socket
    (in this case, when the user navigates to the main page.)"""

    # need visibility of the global thread object
    global follower_thread, friend_thread, follower_send_thread, friend_send_thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not follower_thread.isAlive():
        print("Reading followers...")
        follower_thread = FollowerThread(target_user)
        follower_thread.start()

    if not friend_thread.isAlive():
        print("Reading friends...")
        friend_thread = FriendThread()
        friend_thread.start()

    if not follower_send_thread.isAlive():
        print("Sending followers to page...")
        follower_send_thread = SenderThread_Follower()
        follower_send_thread.start()

    if not friend_send_thread.isAlive():
        print("Sending friends to page")
        friend_send_thread = SenderThread_Friend()
        friend_send_thread.start()

    while True:
        if list(USER_DATA.keys()) == ["username","num_followers","num_status"]:
            socketio.emit('userdata', {'userdata': USER_DATA}, namespace='/test')
            break
        else: 
            sleep(1)
            continue

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    """Code to be run when the browser disconnects from the web socket."""
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
