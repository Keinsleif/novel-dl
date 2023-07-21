ROOT=$(cd $(dirname $0); pwd)
TARGET=${ROOT}/../static/kakuyomu.css
curl -#L -o /tmp/kakuyomu-old.css https://cdn-static.kakuyomu.jp/css/kakuyomu.css
cat ${ROOT}/custom.css >> /tmp/kakuyomu-old.css
purifycss /tmp/kakuyomu-old.css ${ROOT}/{template,index}.html ${ROOT}/../*.html ${ROOT}/../static/kakuyomu.js --out ${TARGET} --info -m
sed -e "s@/font/dcsymbols-regular.woff?6tnyRgzhZFkJ@dcsymbols-regular.woff@" -i ${TARGET}
sed -e "s@/font/dcsymbols-regular.otf?VjSwft_YX8ck@dcsymbols-regular.otf@" -i ${TARGET}
sed -e "s@/font/dcicons-regular.eot?OicIuNS6IwQE@dcicons-regular.eot@g" -i ${TARGET}
sed -e "s@/font/dcicons-regular.otf?woyfFEfr8EbA@dcicons-regular.otf@" -i ${TARGET}
sed -e "s@.isTouch #globalHeaderTouch-globalNav img@.isTouch #globalHeaderTouch-globalNav svg@" -i ${TARGET}
rm -f /tmp/kakuyomu-old.css
