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
Pythonインタープリターとバージョン3.6以降が必要であり、UNIXベースのプラットフォームで実行する必要があります。  
これは、UbuntuやCentOSなどのMacOSおよびLinux、つまりUnix系OSで動作するはずです。 Windowsではテストされていません。  
それはパブリックドメインにリリースされます。つまり、好きなように変更、再配布、または使用することができます。  

# DEMO
![demo](https://raw.github.com/wiki/kazuto28/novel-dl/images/novel-dl_DEMO.gif)
# Usage (使い方)

# Requirement (環境)

- Ubuntu 20.04.2 LTS
- Python >= 3.3
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
$ pip3 install git+https://github.com/kazuto28/novel-dl.git
```

# Note
**Use the generated novels data only for private.**
