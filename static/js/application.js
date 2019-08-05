var followers_received = [];
var friends_received = [];
// var G = new jsnx.DiGraph();

$.holdReady(true);
$.getScript("static/jsnetworkx/jsnetworkx.js", function() {
    window.G = new jsnx.DiGraph();
    $.holdReady(false);
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
            "num_status":1
            });

        $("svg").attr({'height':'50em'})
        
        jsnx.draw(G, {
            element: '#canvas',
            withLabels: true,
            layoutAttr: {
                charge: -320,
            },
            nodeStyle: {
                fill: function(d) {
                    return d3.interpolateSpectral(2/Math.log10(d.data.num_status));
                }
            },
            labelStyle: {
                fill: 'black'
            },
            nodeAttr: {
                r: function(d) {
                    // console.log("........")
                    // console.log(d)
                    // // console.log(d.data)
                    // console.log(d.data.screen_name)
                    // console.log(d.data.num_followers)
                    // console.log(d.data.num_status)
                    return 2*Math.log(d.data.num_followers);
                }
            },
            //     title: function(d) { return d.label;}
            // },
    
            // stickyDrag: true
        }, true);
    })

        //receive details from server
    socket.on('newfriend', function(msg) {
        console.log("Received friend " + msg.friend_id);
        friends_received.push(msg.friend_id);
    })

    socket.on('userdata', function(msg) {
        console.log("Updated target user info.");
        window.G.node.get("contrapoints").num_followers = msg.userdata.num_followers
        window.G.node.get("contrapoints").num_status = msg.userdata.num_status
    })

    socket.on('newfollower', function(msg) {
        console.log("Received follower " + msg.follower.screen_name);
        if (
            (typeof msg.follower.screen_name != "undefined")||
        (typeof msg.follower.num_followers != "undefined")||
        !isNaN(msg.follower.num_followers)
            ) {
            followers_received.push(msg.follower);
            AddFollowers(window.G)
        }
    })

});

function AddFollowers(G) {
    for (var i = 0; i < followers_received.length; i++) {
        if (!G.nodes().includes(followers_received[i])) {
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