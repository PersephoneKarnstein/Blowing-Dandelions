function PlotFollowers(G) {

    // G.addNode("Contrapoints")
    for (var i = 0; i < followers_received.length; i++) {
        G.addNode(followers_received[i], {
            "xlink:href"="http://pbs.twimg.com/profile_images/1142870920639459328/c2zAn8iC_normal.jpg",
            width="40",
            height="40",
            x="-20",
            y="-20",
        });
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