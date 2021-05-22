type="";
function handleWindowResize(){
	if (window.matchMedia('(max-width: 767px)').matches){
		body.classList.remove("isPC");
		body.classList.add("isTouch");
		if (type=="index"){
			body.id="page-works-workTouch";
			document.getElementById("pc").style.display ="none";
			document.getElementById("sp").style.display ="block";
		}
	} else{
		body.classList.remove("isTouch");
		body.classList.add("isPC");
		if (type=="index"){
			body.id="page-works-work";
			document.getElementById("pc").style.display ="block";
			document.getElementById("sp").style.display ="none";
		}
	}
}

window.onload=function() {
	type="base";
	body=document.getElementById("page-works-episodes-episode");
	if (!body){
		type="index";
		body=document.getElementById("page-works-work");
	}
	else{
		l=document.getElementsByClassName("js-episode-setting-tab-container")[0];
		l.classList.remove("isHidden");
		l.classList.add("isShown");
	}
	handleWindowResize();
}
window.addEventListener('resize', handleWindowResize);
