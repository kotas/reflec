# Reflec

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito


## はじめに

この Reflec は2つのソフトウェアから成っています。

* Reflec2
  * Windows Media エンコーダーによるメディアストリーミング（mms://〜）を、
    ミラーリングするためのソフトウェアです。
  * WME で配信されているメディアストリーミングをクライアント部が受信します。
  * サーバー部は外部からの接続を受け付け、クライアント部が受信したストリー
    ミングをそのまま配信します。これにより、ライブストリーミングを劣化なし
    でそのままミラーリングする事ができます。

* LiveAlive2
  * あらかじめ設定されたアドレスを監視して、メディアストリーミングが開始し
    ていたら Reflec2 を起動するソフトウェアです。
  * 複数のアドレスについて定期的にポートが開放されているかを調べ、メディア
    ストリーミングの開始を検出します。開始が検出されたアドレスに対して色々
    なアクションを起こす事ができます。

実際にはこれらの動作に加えて、プラグインによる様々な機能が追加されています。


## 何のために作ったの？

昔むかし、とある場所で、ストリーミング動画を中継したり、中継状況を表示したりする
需要があったのです。それだけです。


## ファイル構成

    readme.txt                  このファイル
    livealive2.py               LiveAlive2 メインプログラム
    reflec2.py                  Reflec2 メインプログラム

    conf/                       設定ファイル群
        clients.xml.example         クライアントの設定ファイル例
        global.ini.example          共通設定ファイル例
        livealive2.ini.example      LiveAlive2 の設定ファイル例
        reflec2.ini.example         Reflec2 の設定ファイル例
    livealive-plugins/          LiveAlive2 のプラグイン
        (プラグインスクリプト)
    reflec-plugins/             Reflec2 のプラグイン
        (プラグインスクリプト)
    lib/                        実行に必要なファイル群
        (色々)


## 動作環境

Reflec は基本的に Windows での動作を想定しています。

Reflec を実行するには以下のソフトウェアが必要です。

* Python 2.5 以降
  * http://www.python.jp/Zope/download/pythoncore

* Python for Windows extensions
  * https://sourceforge.net/projects/pywin32/

* Skype4COM
  * http://developer.skype.com/accessories/skype4com

また、一部のプラグインは Windows でしか動作しません。


## 実行する前の準備

実行する前に、設定ファイルを準備します。

`conf/` フォルダの中には、設定ファイルのサンプルが入っています。

これらのファイルの名前には `.example` という拡張子がついていますが、実際には
`.example` をとった `livealive2.ini` や `reflec2.ini` というファイルが利用されます。

初めて利用する場合、サンプルをそのまま利用してみてください。
サンプルにはあらかじめ適切に設定が書かれているので、そのまま利用できます。

サンプルをそのまま利用する場合、サンプルファイルの名前を変更して、最後の
`.example` を削除してください。

    (名前の変更前)             (名前の変更後)
    clients.xml.example     → clients.xml
    livealive2.ini.example  → livealive2.ini
    reflec2.ini.example     → reflec2.ini

実行にはこれら3つの設定ファイルが必要なので注意してください。

また、設定ファイルの中身をのぞいて、好きなように設定を変えてみてください。

設定ファイルが用意できたら準備完了です。

## 実行方法

`livealive2.py` をダブルクリックして実行してください。

コマンドプロンプト画面が表示され、動作に関する情報が表示されます。

