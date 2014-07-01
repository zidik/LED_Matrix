window.onload=function(){
    document.getElementById('mode_submit').style.visibility = 'hidden';
};

function ajaxPOST(target_page, content_type, values){
    var xmlhttp;
    if (window.XMLHttpRequest){
        // code for IE7+, Firefox, Chrome, Opera, Safari
        xmlhttp=new XMLHttpRequest();
    }
    else{
        // code for IE6, IE5
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange=function(){
            if (xmlhttp.readyState==4 && xmlhttp.status==200){
                document.getElementById("server_response").innerHTML=xmlhttp.responseText;
            }
        }
    xmlhttp.open("POST",target_page,true);
    xmlhttp.setRequestHeader("Content-type", content_type);
    xmlhttp.send(values);
}