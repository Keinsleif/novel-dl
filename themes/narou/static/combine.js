loadFiles=['reset','kotei','novel_smpview'];
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
	for (var i=0;i<loadFiles.length;i++) {
		if (enableCSS.includes(loadFiles[i])) {
			document.getElementById(loadFiles[i]).disabled=false;
		} else{
			document.getElementById(loadFiles[i]).disabled=true;
		}
	}
}
window.onload=function(){
	for (var i=0;i<loadFiles.length; i++) {
		var css=document.createElement('link');
		css.rel='stylesheet';
		css.id=loadFiles[i];
		css.href="static/"+loadFiles[i]+".css";
		css.media="screen,print";
		css.disabled=true;
		document.getElementsByTagName("head")[0].appendChild(css);
	}
	handleWindowResize()
}
window.addEventListener('resize', handleWindowResize)