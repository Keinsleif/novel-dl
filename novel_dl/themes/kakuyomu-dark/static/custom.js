var type=document.getElementById("page_type").innerText;
if (type!="single"){
    var css=document.createElement('link');
    css.rel='stylesheet';
    css.id="dark";
    css.href="static/dark.css";
    css.media="screen,print";
    document.getElementsByTagName("head")[0].appendChild(css);
}