TARGET=$1
purifycss kakuyomu-old.css t.html ../*.html ../static/kakuyomu.js --out ${TARGET}
sed -e "s@/font/dcsymbols-regular.woff?6tnyRgzhZFkJ@dcsymbols-regular.woff@" -i ${TARGET}
sed -e "s@/font/dcsymbols-regular.otf?VjSwft_YX8ck@dcsymbols-regular.otf@" -i ${TARGET}
sed -e "s@/font/dcicons-regular.eot?OicIuNS6IwQE@dcicons-regular.eot@g" -i ${TARGET}
sed -e "s@/font/dcicons-regular.otf?woyfFEfr8EbA@dcicons-regular.otf@" -i ${TARGET}
sed -e "s@.isTouch #globalHeaderTouch-globalNav img@.isTouch #globalHeaderTouch-globalNav svg@" -i ${TARGET}
