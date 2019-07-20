
function PlotFollowers(){
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