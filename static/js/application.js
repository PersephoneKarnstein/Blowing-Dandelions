var followers_received = [];
var my_friends_received = new Set();
var my_followers_received =  new Set();
// var G = new jsnx.DiGraph();

$.holdReady(true);
$.getScript("static/jsnetworkx/jsnetworkx.js", function() {
    window.G = new jsnx.DiGraph();
    $.holdReady(false);
});

$(document).on("load", function() {
    $('a[rel=tipsy]').tipsy({fade: true, gravity: 'n'});
  });

$(document).ready(function() {
    //connect to the socket server.
    // var G = new jsnx.DiGraph();
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

socket.on('connect', () => {
    console.log("Connected to server.")
    // var G = new jsnx.DiGraph();
    G.addNode("contrapoints", {
        "num_followers":9999,
        "num_status":1,
        "image":"http://pbs.twimg.com/profile_images/1146860549306818560/snzS8Jhe_normal.png",
        "id":9999
        });

    $("svg").attr({'height':'50em'})

    jsnx.draw(G, {
        element: '#canvas',
        withLabels: true,
        layoutAttr: {
            charge: -320,
            // linkDistance: function(d) {
            //     return 100/(Math.log(d.data.num_followers + 1)*Math.log10(d.data.num_status + 1)) 
                //! should be able to use this to describe how many times they have retweeted 
                // the person or something
            // }
        },
        // nodeStyle: {
        //     fill: function(d) {
        //         // return d3.interpolateSpectral(2/Math.log10(d.data.num_status));
        //         return "url("+d.data.image+")"
        //     }
        // },
        labelStyle: {
            fill: 'black'
        },

        node_shape: "image",
        node_attr: {
            r: function(d) {
                return 2*Math.log(d.data.num_followers+1);
                },
            id: function(d) {
                return "node-"+d.data.id
            }
        },
        //     title: function(d) { return d.label;}
        // },

        // stickyDrag: true
    }, true);
})

        //receive details from server
    socket.on('newfriend', function(msg) {
        console.log("Received friend of me " + msg.friend_id);
        my_friends_received.add(msg.friend_id);
    })

    socket.on('newfollower', function(msg) {
        console.log("Received follower of me " + msg.follower_id);
        my_followers_received.add(msg.follower_id);
    })

    socket.on('meData', function(msg) {
        console.log("Hello!")// msg.meData.username, "!")
        // window.G.node.get("contrapoints").num_followers = msg.userdata.num_followers
        // window.G.node.get("contrapoints").num_status = msg.userdata.num_status
        // window.G.node.get("contrapoints").image = msg.userdata.image
    })

    socket.on('targetdata', function(msg) {
        console.log("Updated target user info.");
        window.G.node.get("contrapoints").num_followers = msg.targetdata.num_followers
        window.G.node.get("contrapoints").num_status = msg.targetdata.num_status
        window.G.node.get("contrapoints").image = msg.targetdata.image
        window.G.node.get("contrapoints").id = "node-9999"
    })

    socket.on('newfollower', function(msg) {
        console.log("Received follower " + msg.follower.screen_name);
        if (
            (typeof msg.follower.screen_name != "undefined")&&
        (typeof msg.follower.num_followers != "undefined")&&
        !isNaN(msg.follower.num_followers)
            ) {
            followers_received.push(msg.follower);
            AddFollowers(window.G)
        }
    })

});

function AddFollowers(G) {
    for (var i = 0; i < followers_received.length; i++) {
        if (!G.nodes().includes(followers_received[i]) && G.nodes().length<=101) {
            // ie, if the new person isn't already a node and also there are 100 or fewer
            // extant nodes + the core/target account
            if (
                (typeof followers_received[i]["screen_name"] != "undefined")&&
                (typeof followers_received[i]["num_followers"] != "undefined")&&
                !isNaN(followers_received[i]["num_followers"])
                ) {
                    G.addNode(followers_received[i]["screen_name"], {
                        "query_screenname":followers_received[i]["query_screenname"],
                        "id":followers_received[i]["id"],
                        "screen_name":followers_received[i]["screen_name"],
                        "location":followers_received[i]["location"],
                        "num_followers":followers_received[i]["num_followers"],
                        "num_status":followers_received[i]["num_status"],
                        "is_verified":followers_received[i]["is_verified"],
                        "image":followers_received[i]["image"]
                        });
                    G.addEdge(followers_received[i]["screen_name"], followers_received[i]["query_screenname"]);

            };
        };
    };
};