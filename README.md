こんにちは。分子研の中澤遼太郎です。
こちらはスぺクトル解析を行うツール ”SpecTaroscoPy” です。

機能は以下の通りです。

- ARPES解析。Image --> EDC, MDC の変換。軸の変換。MBS A-1装置@IMSの出力データに最適化していますが、他の装置でも最低限使用できるはず。
- 二次微分解析。曲率解析。
- 逆畳み込み解析。
- カーブフィッティング解析。

詳しいアプリケーションの使い方は、***manual.pdf***を御覧ください。

## ライセンスと引用
ライセンスはCC BY-NC 4.0 としました。
ご理解ください。
本ツールを用いた成果を発表される際には、
謝辞などクレジットを記載いただけますと幸いです。励みになります。
特にDeconvolution, Second derivative 解析をご利用の際は、以下の文献を引用お願いいたします。

R. Nakazawa, H. Sato, and H. Yoshida, arXiv (2025).
DOI: 10.48550/arXiv.2509.21246 (https://doi.org/10.48550/arXiv.2509.21246)

(現在、国際誌に投稿中)


## License and Citation
This project is licensed under the Creative Commons 
Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).
If you use "Deconvolution" and "Second derivative" in "SpecTaroscoPy" for your research, please cite:

R. Nakazawa, H. Sato, and H. Yoshida, arXiv (2025).

DOI: 10.48550/arXiv.2509.21246 (https://doi.org/10.48550/arXiv.2509.21246)

(Under the peer review)

## 初期設定 (プログラム起動までの手順)
では、はじめに以下の初期設定をおねがいします。

1. 	Pythonをインストールしてください。
	このアプリはPythonで開発しました (Python3.12.7)。
	正直、環境とか難しくて私もよくわかっていませんが...。
	Visual Stadio Codeインストールして、拡張機能でPythonインストールすれば十分と思われる。
	
	あるいは、AnacondaなりPythonの公式ページなりからPythonをダウンロードしてください。
	(公式Python, AnacondaでPythonをインストールした人は)
	Pythonのpathを通してください。
	
1.	それでは"SpecTaroscoPy" フォルダ --> "src" フォルダ --> "main.py" をVisual Studio Codeなどで実行してください。

1.	出力にmoduleがないよっていうエラーが出る (Visual Stadio Codeの場合、ターミナルにModuleNotFoundErrorがでるはず) 。
	Findできなかったモジュールをターミナルでpip installしていく。
	ターミナルに、
	pip install XXX
	と打ってエンター。
	たとえば下記のモジュールがないってエラーを吐いてきます。
	- customtkinter
	- mpmath
	
1.	"SpecTaroscoPy - Launcher" windowが出たら成功です。
	これ以降は、"SpecTaroscoPy" フォルダ の "SpecTaroscoPy.bat" のクリックでLauncherを起動できるようになります (Win)。
	毎回、*.py fileをVS codeなどで実行してもよいです (Win/macOS)。

1.	Launcherで所望の解析方法のボタンを押して解析スタート！それぞれの解析アプリの使い方は説明書（manual.pdf）を参考に。

## 連絡先
誤植・バグなどがあれば 
nakazawaあっとまーくims.ac.jp
まで。
アプリの改善案などもお知らせください！
