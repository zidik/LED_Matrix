window.onload = function () {
    document.getElementById('mode_submit').style.visibility = 'hidden';

    document.getElementById('catch_colors_players_label').style.display='none';
    document.getElementById('catch_colors_players_select').style.display='none';
};

function changeMode(select) {
    ajaxPOST(select.form.action, 'application/x-www-form-urlencoded', select.name+'='+select.value);
    if (select.value=='catch_colors_multiplayer') {
        document.getElementById('catch_colors_players_label').style.display='inline-block';
        document.getElementById('catch_colors_players_select').style.display='inline-block';
        document.getElementById('catch_colors_players_select').selectedIndex = 0;
    } else {
        document.getElementById('catch_colors_players_label').style.display='none';
        document.getElementById('catch_colors_players_select').style.display='none';
    }
}

function changePlayers(select){
    ajaxPOST(select.form.action, 'application/x-www-form-urlencoded', select.name+'='+select.value);
}

function ajaxPOST(target_page, content_type, values) {
    var xmlhttp;
    if (window.XMLHttpRequest) {
        // code for IE7+, Firefox, Chrome, Opera, Safari
        xmlhttp = new XMLHttpRequest();
    } else {
        // code for IE6, IE5
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            document.getElementById("server_response").innerHTML = xmlhttp.responseText;
        }
    };
    xmlhttp.open("POST", target_page, true);
    xmlhttp.setRequestHeader("Content-type", content_type);
    xmlhttp.send(values);
}


function togglePower(item) {
    toggleState(item);
    ajaxPOST(item.form.action, 'application/x-www-form-urlencoded', item.name + '=' + item.className);
}
function toggleState(item) {
    if (item.className == "on") {
        item.className = "off";
        item.value = "Off";
    } else {
        item.className = "on";
        item.value = "On";
    }
}