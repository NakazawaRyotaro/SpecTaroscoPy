こんにちは。分子研の中澤遼太郎です。
こちらはスぺクトル解析を行うツール ”SpecTaroscoPy” です。

詳しいアプリケーションの使い方は、本ページのReleaseよりzip fileをダウンロードし、zip file内の***manual.pdf***を御覧ください。

機能は以下の通りです。
- ARPES解析 (EDC/MDC作成, 軸の変換)  
MBS A-1/Scienta DA30@IMSの出力データに最適化しているが、他の装置でも利用可能
- 二次微分解析, 曲率解析
- 逆畳み込み解析
- カーブフィッティング解析

## ライセンスと引用
ライセンスはCC BY-NC 4.0 としました。
ご理解ください。
本ツールを用いた成果を発表される際には、
謝辞などクレジットを記載いただけますと幸いです。励みになります。
特にDeconvolution, Second derivative 解析をご利用の際は、以下の文献を引用お願いいたします。

R. Nakazawa, H. Sato, and H. Yoshida, Rev. Sci. Instrum. 97, 023906 (2026)  
doi: 10.1063/5.0303140  
ArXiv: https://doi.org/10.48550/arXiv.2509.21246



## License and Citation
This project is licensed under the Creative Commons 
Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).
If you use "Deconvolution" and "Second derivative" in "SpecTaroscoPy" for your research, please cite:

R. Nakazawa, H. Sato, and H. Yoshida, Rev. Sci. Instrum. 97, 023906 (2026)  
doi: 10.1063/5.0303140  
ArXiv: https://doi.org/10.48550/arXiv.2509.21246


## 初期設定 (プログラム起動までの手順)
では、はじめに以下の初期設定をおねがいします。

1. 	Pythonをインストールしてください。
	このアプリはPythonで開発しました (Python3.12.7)。
	Visual Stadio Codeをインストール、Pythonをインストール・パスを通せば十分と思われる。
	
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
