"""
Demo Flask application to test the operation of Flask with socket.io

Aim is to create a webpage that is constantly updated with random numbers from a background python process.

30th May 2014

===================

Updated 13th April 2018

+ Upgraded code to Python 3
+ Used Python3 SocketIO implementation
+ Updated CDN Javascript and CSS sources

"""

# Start with a basic flask app webpage.
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

#turn the flask app into a socketio app
socketio = SocketIO(app)

#Get followers of target account
thread1 = Thread()
thread1_stop_event = Event()

#Get 'friends' - i.e. people you follow
thread2 = Thread()
thread2_stop_event = Event()

#Send follower data to frontend
thread3 = Thread()
thread3_stop_event = Event()

#Send friend data to frontend
thread4 = Thread()
thread4_stop_event = Event()

#initialize a queue to add things into
QUEUE = deque()
FRIEND_QUEUE = deque()

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(API_ACCESS_TOKEN, API_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)


class FollowerThread(Thread):
    def __init__(self, screenname):
        # self.delay = 1
        self.screenname = screenname
        super(FollowerThread, self).__init__()

    def GetFollowers(self):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global auth, api, QUEUE

        # auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        # api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
       
        u = api.get_user(screen_name = self.screenname)
        num_followers = u.followers_count
        all_followers = dict()
        i = 0

        while not thread1_stop_event.isSet():
            for follower in tweepy.Cursor(api.followers, screen_name=self.screenname).items():
                got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                    "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                        "is_verified":follower.verified, "image":follower.profile_image_url}
                all_followers[got_follower["id"]] = got_follower
                i+=1

                QUEUE.appendleft(got_follower) #! enqueue followers in this thread; dequeue in a seperate thread
                print(f"i={i}\nqueue length={len(QUEUE)}\n{got_follower}\n\n")

            if i >= num_followers: thread1_stop_event.set()

    def run(self):
        self.GetFollowers()

class FriendThread(Thread):
    def __init__(self):
        # self.delay = 1
        # self.screenname = screenname
        super(FriendThread, self).__init__()

    def GetFriends(self):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global auth, api, FRIEND_QUEUE
       
        u = api.me()
        num_friends = u.friends_count
        all_friends = []
        j = 0

        while not thread1_stop_event.isSet():
            for friend in tweepy.Cursor(api.friends, id=u.id_str).items():
                # got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                #     "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                #         "is_verified":follower.verified, "image":follower.profile_image_url}
                all_friends.append(friend.id_str)
                j+=1

                FRIEND_QUEUE.appendleft(friend.id_str) #! enqueue followers in this thread; dequeue in a seperate thread
                print(f"j={j}\nfriend queue length={len(FRIEND_QUEUE)}\n{friend.screen_name}\n\n")

            if j >= num_friends: thread3_stop_event.set()

    def run(self):
        self.GetFriends()

class SenderThread_Follower(Thread):
    def __init__(self):
        self.delay = 1.5
        super(SenderThread_Follower, self).__init__()

    def SendData(self):
        """
        Generate a random number every 1.5 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """

        global QUEUE
        #infinite loop of magical random numbers
        # print("Making random numbers")
        while not thread1_stop_event.isSet():
            if len(QUEUE) > 0:
                follower = QUEUE.pop()
                print(f"\n\nDequeued follower:\n{follower}\nNum left in queue:{len(QUEUE)}")
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
        Generate a random number every 1.5 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """

        global FRIEND_QUEUE
        #infinite loop of magical random numbers
        # print("Making random numbers")
        while not thread2_stop_event.isSet():
            if len(FRIEND_QUEUE) > 0:
                friend = FRIEND_QUEUE.pop()
                print(f"\n\nDequeued friend id:\n{friend}\nNum left in queue:{len(FRIEND_QUEUE)}")
                socketio.emit('newfriend', {'friend_id': friend}, namespace='/test')
            else: pass
            sleep(self.delay)

    def run(self):
        self.SendData()

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread1, thread2, thread3, thread4
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread1.isAlive():
        print("Starting Thread 1")
        thread1 = FollowerThread("contrapoints")
        thread1.start()

    if not thread2.isAlive():
        print("Starting Thread 2")
        thread2 = FriendThread()
        thread2.start()

    if not thread3.isAlive():
        print("Starting Thread 3")
        thread3 = SenderThread_Follower()
        thread3.start()

    if not thread4.isAlive():
        print("Starting Thread 4")
        thread4 = SenderThread_Friend()
        thread4.start()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
