function onLoad () {
    var ws;

    if (!('WebSocket' in window)) {
	alert('Your browser does not have a key feature (WebSockets) needed ' +
	      'to run this. Cannot continue.');
	return;
    }

    try {
	ws = new WebSocket("ws://localhost:8888/appresponse");
    } catch (err) {
	alert('Exception: ' + err);
    }

    ws.onopen = function() {
       //ws.send("python asynk.py --op=sync --pwd=");
    };

    ws.onmessage = function (evt) {
       $("div#log").append(evt.data);
       //alert(evt.data);
    };

    ws. onerror = function(error){
	alert('Error Detected: ' + error);
	console.log('Error detected: ' + error);
    }

    ws.onclose = function() {
	alert('Connection closed to server');
    };

    //load profile names
    $.getJSON("/profiles",
        function(data){
            for (x in data){
                $("#profile").append("<option value=\""+data[x]+"\">"+data[x]+"</option>");
            }
        });

    //load profile variables on choosing a profile
    $("#profile").change(function(){
        if ($("#profile").val()!=0){
            $.getJSON("/pdata/"+$("#profile").val(),
            function(data){
                $("#db1").val(data["db1"]);
                $("#uname1").val(data["uname1"]);
                $("#db2").val(data["db2"]);
                $("#uname2").val(data["uname2"]);
            });
        }
    });

    //preparing the sync command
    $("input#sync").click(function(evt){
        opts1=opts2="";
        if ($("#db1").val()=='cd') {
            opts1+=" --cduser="+$("#uname1").val()+" cdpwd="+$("#pass1").val();
        }
        else if ($("#db1").val()=='gc') {
            opts1+=" --pwd="+$("#pass1").val();
        }
        if ($("#db2").val()=='cd') {
            opts2+=" --cduser="+$("#uname2").val()+" cdpwd="+$("#pass2").val();
        }
        else if ($("#db2").val()=='gc') {
            opts1+=" --pwd="+$("#pass2").val();
        }
        opts1=opts2="";
        ws.send("python asynk.py --op=sync --name="+$("#profile").val()+opts1+opts2);
        //ws.send ("python asynk.py --op=sync --name="+$("#profile").val());
    });


}

$(onLoad);
