# novel-dl
This tool enables you to download novels from "syosetu.com" or "kakuyomu.jp" and read them even if you are offline.  
このツールは「小説家になろう」や「カクヨム」から小説をダウンロードし、オフラインでも読むことを可能にするものです。

# Description (概要)

novel-dl is a command-line program to download novels from syosetu.com or kakuyomu.jp.  
It downloads novel data from those sites and generates html with files such as css, javascript and images for offline use.  
It requires the Python interpreter and version 3.6+ and need to run on unix based platform.  
It should work on MacOS and Linux such as Ubuntu and CentOS, that is, Unix-like operating systems. Not tested on Windows.  
It is released to the public domain, which means you can modify it, redistribute it or use it however you like.  


novel-dlは、「小説家になろう」や「カクヨム」から小説をダウンロードするためのコマンドラインプログラムです。  
小説のデータをダウンロードし、オフラインでも使用するためにcss、javascript、画像などとhtmlを生成します。  
Pythonのバージョン3.3以降が必要であり、UNIXベースのプラットフォームで実行する必要があります。  
UbuntuやCentOSなどのMacOSおよびLinux、つまりUnix系OSで動作するはずです。 Windowsではテストされていません。  
これはパブリックドメインにリリースされます。つまり、好きなように変更、再配布、または使用することができます。  

# DEMO
![demo](https://raw.github.com/wiki/Keinsleif/novel-dl/images/novel-dl_DEMO.gif)

# Usage (使い方)
    novel-dl [OPTIONS] <src> [<src> ...]

# Options
### General Options
- -h, --help  
    ヘルプを出力します
- -v, --version  
    バージョン情報を出力します
- -q, --quiet  
    エラー以外の出力を制限します。  

### Downloader Options
- -a, --axel  
    遅延時間を無くすことでダウンロード速度を加速させます。  
    ※遅延時間を設けているのはサーバーに過度な負担をかけないためです。  
    何度もこのオプションを用いてダウンロードするとサイト側の利用規約の禁止事項に抵触する可能性があります。  

- -f, --from-file  
    すでにダウンロードされた小説からデータを取得します。  
    `src`には小説ディレクトリへのパスを指定します。  
    短編形式で出力されたファイル(html単体)には非対応  
    **Windowsには非対応です**

- -u, --update  
    すでにダウンロードされた小説のアップデートを行います。
    `src`には小説ディレクトリへのパスを指定します。  
    短編形式で出力されたファイル(html単体)には非対応  
    **Windowsには非対応です**

### Formatter Options
- -t, --theme <theme name>  
    出力するファイルのテーマを指定します。  
    これにより、小説の取得元に関わらず、決まった見た目のファイルを出力することができます。  
    "auto"を指定することで取得元に合わせたテーマを自動で選ぶこともできます。  

- -m, --media <media type>  
    ファイルを特定のメディアタイプ用のみのスタイルで出力します。  
    多くの場合、これはファイルサイズ削減のために使用されます。  
    使用するテーマによって指定できるメディアタイプが違います。  

- -r, --renew  
    すでに存在する話をスキップせず、上書きし、更新します。  

- -e, --episode <episode num>  
    特定の話を指定し、短編と同じような形で出力します。  

### Output Options

- -n, --name  
    出力フォルダ名、または出力ファイル名をのテンプレートを指定します。
    フォルダ名にはstrftimeの書式及び、以下のテンプレートが使用できます。  
    "{"および"}"をエスケープする場合には  
    "{"を"{{"に、"}"を"}}"に置き換えます。
  - `title` Novel title (default)  
  - `ncode` Novel identifier  
  - `theme` Novel format theme  
  - `media` Novel format media type  
  - `type` Novel type (series, single)  
  - `episode` Novel episode number

- -d, --dir  
    生成したファイル群の出力先フォルダを指定します。  


# Requirement (環境)

- Unix-like operating systems
- Python >= 3.6
- [Main libraries]
    - beautifulsoup4
    - Jinja2
    - pytz
    - requests
    - tqdm

# Installation (インストール方法)

```
$ pip3 install novel-dl
```
or
```
$ pip3 install git+https://github.com/Keinsleif/novel-dl.git
```
or
```
$ git clone https://github.com/Keinsleif/novel-dl.git
$ cd novel-dl
$ python3 setup.py install
```
# Note
**Please be sure use the generated novels data only for private.**  
**出力された小説データの使用はは絶対に個人使用に限定してください**  
