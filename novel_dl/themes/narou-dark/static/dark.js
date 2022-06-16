shortcut.add("Shift+D",function(){
    var hdoc=document.getElementsByTagName("html")[0];
    if (hdoc.classList.contains("light")){
        hdoc.classList.remove("light");
    }
    else{
        hdoc.classList.add("light");
    }
});
