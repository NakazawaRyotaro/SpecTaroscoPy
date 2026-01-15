## 変更履歴

- VS codeで開くとき、Command+K, Vでプレビューが見れます。

|Date|Version|コメント|
|-----|-----|-----|
|2025/07/07|6.4.7|ARPES image解析の平均前EDCの規格化バグ (6.4.4-6.4.6 で存在?) を修正。  EDC viewerをとりあえず正常動作するように修正した。これ以上はGraph Maneger classを作って機能を分けたほうが良さそう。|
|2025/09/28|6.4.8|ARPES image解析でMBS A-1アプリによらず最低限の解析が出来るように改善。  出力はX (Ek, EF, VL)が1列目。2列目以降が強度。|
|2025/09/30|6.4.9|READMEとCHANGELOGを分け、md fileに変更。|
|2025/10/04|6.4.10|Frame.pyのバグを修正しました。|
|2025/12/19|6.4.12|ARPES imageでDA30も半手動で解析可能。Second derivativeは出力figureの見た目を変更。|
|2025/12/19|6.5.0|ARPES image解析でDA30のtext fileを読み込めるようにした。|
|2025/12/19|6.5.2|ARPES image/二次微分解析のバグ修正。|
|2026/01/15|6.6.0|二次微分のパラメータ依存解析プログラムをsrc/analysis/SecondDerivative_ParameterDependence.pyとして追加。GUIは未作成。|