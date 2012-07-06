﻿# -*- coding: utf_8 -*-
u"""
LiveAlive2 Main Script

Licensed under the MIT License.
Copyright (c) 2007-2012 Kota Saito

以下に定める条件に従い、本ソフトウェアおよび関連文書のファイル（以下「ソフトウ
ェア」）の複製を取得するすべての人に対し、ソフトウェアを無制限に扱うことを無償
で許可します。これには、ソフトウェアの複製を使用、複写、変更、結合、掲載、頒布、
サブライセンス、および/または販売する権利、およびソフトウェアを提供する相手に
同じことを許可する権利も無制限に含まれます。

上記の著作権表示および本許諾表示を、ソフトウェアのすべての複製または重要な部分
に記載するものとします。

ソフトウェアは「現状のまま」で、明示であるか暗黙であるかを問わず、何らの保証も
なく提供されます。ここでいう保証とは、商品性、特定の目的への適合性、および権利
非侵害についての保証も含みますが、それに限定されるものではありません。作者また
は著作権者は、契約行為、不法行為、またはそれ以外であろうと、ソフトウェアに起因
または関連し、あるいはソフトウェアの使用またはその他の扱いによって生じる一切の
請求、損害、その他の義務について何らの責任も負わないものとします。
"""

import sys
import os.path

# ライブラリパスを追加
APP_DIR = os.path.dirname(__file__)
sys.path.append( os.path.join(APP_DIR, 'lib') )

# アプリケーションディレクトリを設定
import livealive.const
livealive.const.APP_DIR = APP_DIR

# アプリケーションを実行
import livealive.app
livealive.app.LiveAliveApplication().start()
