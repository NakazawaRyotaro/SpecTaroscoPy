こんにちは。分子研の中澤遼太郎です。
こちらはスぺクトル解析を行うツール ”SpecTaroscoPy” です。
昨日は以下の通りです。
- ARPES解析。image -> EDC, MDC の変換。軸の変換。MBS A-1装置@IMSに最適化していますが、他の装置でも最低限使用可能なはずです。
- 二次微分解析。曲率解析。
- 逆畳み込み解析。
- カーブフィッティング解析。
## ライセンスと引用
ライセンスはCC BY-NC 4.0 としました。
ご理解ください。
本ツールを用いた成果を発表される際には、
謝辞または共著としてクレジットを記載いただけますと幸いです。

特にDeconvolution, Second derivative 解析をご利用の際は、以下の文献を引用してください。

R. Nakazawa, H. Sato, and H. Yoshida, arXiv (2025).
DOI: 10.48550/arXiv.2509.21246 (https://doi.org/10.48550/arXiv.2509.21246)

(現在、国際誌に投稿中)

*************************************************************************************
## License and Citation
This project is licensed under the Creative Commons 
Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

If you use "Deconvolution" and "Second derivative" in "SpecTaroscoPy" for your research, please cite:

R. Nakazawa, H. Sato, and H. Yoshida, arXiv (2025).  
DOI: 10.48550/arXiv.2509.21246 (https://doi.org/10.48550/arXiv.2509.21246)

***********************************************************************************
では、はじめに以下の初期設定をおねがいします。
(1) Pythonをインストールしてください。
	このアプリはPythonで開発されています(Python3.12.7)。
	正直、環境とか難しくて私もよくわかっていませんが...。
	
(2) Pythonのpathを通してください。
	(1)(2)で行き詰まったらAnacondaをインストールするのが早いかも。
	
(3) それでは"SpecTaroscoPy" フォルダ --> 	"main.py" をVisual Studio Codeなどで実行してください。

(4) おそらく、moduleがないよっていうエラーが出るので、指示にしたがってpip installしてください。
	たとえば下記をpip installすることになると思います。
	- customtkinter
	- mpmath
	など。
	
(5) "SpecTaroscoPy - Launcher" windowが出たら成功です。
	これ以降は、"SpecTaroscoPy" フォルダ の "SpecTaroscoPy.bat" のクリックでLauncherを起動できるようになります (Win)。
	毎回、*.py fileをVS codeなどで実行してもよいです (Win/macOS)。


## 連絡先
誤植・バグなどがあれば 
nakazawaあっとまーくims.ac.jp
まで。
アプリの改善案などもお知らせください！
