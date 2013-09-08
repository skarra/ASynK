function setUpWebSocket () {
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
        function (data) {
            for (x in data){
                $("#profile").append("<option>" + data[x] + "</option>");
                $('#profile').selectpicker('refresh');
            }
        });

    //load profile variables on choosing a profile
    $("#profile").change(function () {
        if ($("#profile").val()!=0) {
            $.getJSON("/pdata/"+$("#profile").val(),
                function (data) {
                    $("#adv_dbid1").val(data["db1"]);
                    $("#adv_stid1").val(data["uname1"]);
                    $("#adv_dbid2").val(data["db2"]);
                    $("#adv_stid2").val(data["uname2"]);
                });
        }
    });

    // preparing the sync command - in the advanced template
    $("input#adv_dryrun").click(function (evt){
        opts1=opts2="";
        if ($("#adv_dbid1").val()=='cd') {
            opts1+=" --cduser="+$("#adv_stid1").val()+" cdpwd="+$("#adv_pwd1").val();
        }
        else if ($("#adv_dbid1").val()=='gc') {
            opts1+=" --pwd="+$("#adv_pwd1").val();
        }
        if ($("#adv_dbid2").val()=='cd') {
            opts2+=" --cduser="+$("#adv_stid2").val()+" cdpwd="+$("#adv_pwd2").val();
        }
        else if ($("#adv_dbid2").val()=='gc') {
            opts1+=" --pwd="+$("#adv_pwd2").val();
        }
        // opts1=opts2="";
        ws.send("python asynk.py --op=sync --dry-run --name="+$("#profile").val()+opts1+opts2);
        //ws.send ("python asynk.py --op=sync --name="+$("#profile").val());
    });
}

function setUpMainToggle () {
    $('#adv_toggle').on('switch-change', function (e, data) {
        var $el = $(data.el), value = data.value;
        console.log(e, $el, value);

        if (value == true) {
            $("#adv_sync").addClass("hidden");
            $("#basic_sync").removeClass("hidden");
        } else {
            $("#basic_sync").addClass("hidden");
            $("#adv_sync").removeClass("hidden");
        }
    });
}

function setUpSelectPicker () {
    $('.selectpicker').selectpicker({
    });
}

function onLoad () {
    setUpWebSocket();
    setUpMainToggle();
    setUpSelectPicker();
}

$(onLoad);
