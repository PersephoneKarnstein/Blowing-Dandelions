var followers_received = [];


$(document).ready(function() {
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');


    socket.on('connect', () => {
            var G = new jsnx.DiGraph();
        })
        //receive details from server
    socket.on('newfollower', function(msg) {
        console.log("Received follower" + msg.follower.screen_name);
        //maintain a list of ten numbers
        // if (followers_received.length >= 10) {
        //     followers_received.shift()
        // }
        followers_received.push(msg.follower);
        PlotFollowers(G)
            // followers_string = '';
            // for (var i = 0; i < followers_received.length; i++) {
            //     followers_string = followers_string + '<p>' + followers_received[i].toString() + '</p>';
            // }
            // $('#log').html(followers_string);
    });

});

function PlotFollowers() {
    var G = new jsnx.DiGraph();

    G.addNode("Contrapoints")
    for (var i = 0; i < followers_received.length; i++) {
        G.addNode(followers_received[i]);
        G.addEdge(followers_received[i]["query_screenname"], followers_received[i]["screen_name"]);
        // followers_string = followers_string + '<p>' + followers_received[i].toString() + '</p>';
    }

    jsnx.draw(G, {
        element: '#canvas',
        withLabels: true,
        nodeStyle: {
            fill: function(d) {
                return d.data.color;
            }
        },
        labelStyle: {
            fill: 'white'
        },
        stickyDrag: true
    });
}