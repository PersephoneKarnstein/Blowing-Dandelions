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


# __author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

#dequeue thread
thread2 = Thread()
thread2_stop_event = Event()

#initialize a queue to add things into
QUEUE = deque()

class RandomThread(Thread):
    def __init__(self, screenname):
        # self.delay = 1
        self.screenname = screenname
        super(RandomThread, self).__init__()

    def randomNumberGenerator(self):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global API_KEY, API_SECRET, QUEUE

        auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
       
        u = api.get_user(screen_name = self.screenname)
        num_followers = u.followers_count
        all_followers = dict()
        i = 0

        while not thread_stop_event.isSet():
            for follower in tweepy.Cursor(api.followers, screen_name=self.screenname).items():
                got_follower = {"query_screenname":self.screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                    "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count,\
                        "is_verified":follower.verified, "image":follower.profile_image_url}
                all_followers[got_follower["id"]] = got_follower
                i+=1

                QUEUE.appendleft(got_follower) #! enqueue followers in this thread; dequeue in a seperate thread
                print(f"i={i}\nqueue length={len(QUEUE)}\n{got_follower}\n\n")

            if i >= num_followers: thread_stop_event.set()

    def run(self):
        self.randomNumberGenerator()

class senderThread(Thread):
    def __init__(self):
        self.delay = 1.5
        super(senderThread, self).__init__()

    def randomNumberGenerator(self):
        """
        Generate a random number every 1.5 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """

        global QUEUE
        #infinite loop of magical random numbers
        # print("Making random numbers")
        while not thread_stop_event.isSet():
            if len(QUEUE) > 0:
                follower = QUEUE.pop()
                print(f"\n\nDequeued follower:\n{follower}\nNum left in queue:{len(QUEUE)}")
                socketio.emit('newfollower', {'follower': follower}, namespace='/test')
            else: pass
            sleep(self.delay)

    def run(self):
        self.randomNumberGenerator()

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread, thread2
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread 1")
        thread = RandomThread("contrapoints")
        thread.start()

    if not thread2.isAlive():
        print("Starting Thread 2")
        thread2 = senderThread()
        thread2.start()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
