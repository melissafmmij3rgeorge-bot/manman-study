# -*- coding: utf-8 -*-
"""把 POKE_DEX 151 条数据内嵌进 index.html 的占位符"""
import io

P = r'C:\Users\clim\Documents\ChatGPT\软件开发\index.html'
D = r'C:\Users\clim\Documents\ChatGPT\软件开发\_tmp_poke\dex.js'

html = io.open(P, encoding='utf-8', newline='').read()
dex = io.open(D, encoding='utf-8').read()

body = dex.split('var POKE_DEX=', 1)[1].strip()
if body.endswith(';'):
    body = body[:-1].rstrip()
body = body.replace('\r\n', '\n')

marker = '/*__POKE_DEX__*/'
assert marker in html, '找不到占位符 /*__POKE_DEX__*/'
assert '{id:1,' not in html, '已经内嵌过了'

html = html.replace(marker, body)
io.open(P, 'w', encoding='utf-8', newline='').write(html)
print('OK 内嵌完成，行数=%d 字节=%d' % (body.count('\n') + 1, len(html)))
