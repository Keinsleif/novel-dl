type = "";
function handleWindowResize() {
	if (window.matchMedia('(max-width: 767px)').matches) {
		body.classList.replace("isPC", "isTouch");
		if (type == "index") {
			body.id = "page-works-workTouch";
		}
	} else {
		body.classList.replace("isTouch", "isPC");
		if (type == "index") {
			body.id = "page-works-work";
		}
	}
}

type = "base";
body = document.getElementById("page-works-episodes-episode");
if (!body) {
	type = "index";
	body = document.getElementById("page-works-work");
}
else {
	l = document.getElementsByClassName("js-episode-setting-tab-container")[0];
	l.classList.replace("isHidden", "isShown");
}
handleWindowResize();

window.addEventListener('resize', handleWindowResize);
