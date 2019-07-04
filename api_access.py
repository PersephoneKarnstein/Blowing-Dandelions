import os, tweepy
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event

global API_KEY = os.environ['API_KEY']
global API_SECRET = os.environ['API_SECRET']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app)

#initialize thread
thread = Thread()
thread_stop_event = Event()

# def addToQueue(screenname, work_queue):
#     auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
#     api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
    
#     et = ET()
#     i=0
#     for follower in tweepy.Cursor(api.followers, screen_name=screenname).items():
#         work_queue.put({"query_screenname":screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
#             "location":follower.location,"num_followers":follower.followers_count, \
#                 "is_verified":follower.verified, "image":follower.profile_image_url})
#         i+=1
#     print(f"{i} users found so far, {et():.1f} s elapsed.")


class FollowerThread(Thread):
    def __init__(self):
        self.delay = 60
        super(FollowerThread, self).__init__()

    def getFollowers(self, screenname):
        """
        Send the results of the non-timing-out tweepy request to a page as they arrive.
        """

        print("Let's heckin do this.")

        global API_KEY, API_SECRET

        auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
       
        u = api.get_user(screen_name = screenname)
        num_followers = u.followers_count
        # on_break = #!check tweepy

        while not thread_stop_event.isSet():
            all_followers = dict()
            i = 0
            for follower in tweepy.Cursor(api.followers, screen_name=screenname).items():
                got_follower = {"query_screenname":screenname,"id":follower.id_str, "screen_name":follower.screen_name, \
                    "location":follower.location,"num_followers":follower.followers_count, "num_status":follower.statuses_count\
                        "is_verified":follower.verified, "image":follower.profile_image_url}
                all_followers[got_follower["id"]] = got_follower
                i+=1

                print(got_follower)

            socketio.emit('all_followers', all_followers, namespace='/test')
            sleep(self.delay)

            if i >= num_followers: thread_stop_event.set()

    def run(self):
        self.getFollowers()


@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = FollowerThread()
        thread.start()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)