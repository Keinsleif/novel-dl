loadFiles={'reset':false,'kotei':false,'novel_smpview':true};
function handleWindowResize(){
	if (window.matchMedia('(max-width: 767px)').matches){
		document.getElementById("pc").style.display ="none";
		document.getElementById("sp").style.display ="block";
		enableCSS=["novel_smpview"];
	} else{
		document.getElementById("pc").style.display ="block";
		document.getElementById("sp").style.display ="none";
		enableCSS=["reset","kotei"];
	}
	for (var i in loadFiles) {
		if (enableCSS.includes(i)) {
			document.getElementById(i).disabled=false;
		} else{
			document.getElementById(i).disabled=true;
		}
	}
}
for (var i in loadFiles) {
       var css=document.createElement('link');
       css.rel='stylesheet';
       css.id=i;
       css.href="static/"+i+".css";
       css.media="screen,print";
       css.disabled=loadFiles[i];
       document.getElementsByTagName("head")[0].appendChild(css);
}
window.onload=handleWindowResize
window.addEventListener('resize', handleWindowResize)
