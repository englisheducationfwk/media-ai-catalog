#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка index.html из _tools/data.json + _tools/template.html.

Использование:
    python _tools/build.py

Что делает:
  1. Читает data.json (весь контент каталога) и template.html (дизайн + приложение).
  2. Проверяет данные: уникальные id, существующие категории, корректные ссылки,
     обязательные поля у инструментов/гайдов/промптов/чек-листа.
  3. Подставляет JSON в шаблон (плейсхолдер __DATA__) и пишет ../index.html.
  4. Печатает сводку. При ошибке — ничего не пишет и выходит с кодом 1.
"""
import json
import os
import sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, '_tools')
TPL = os.path.join(TOOLS, 'template.html')
DATA = os.path.join(TOOLS, 'data.json')
OUT = os.path.join(ROOT, 'index.html')

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def main():
    if not os.path.isfile(DATA):
        print('НЕТ ФАЙЛА:', DATA)
        return 1
    if not os.path.isfile(TPL):
        print('НЕТ ФАЙЛА:', TPL)
        return 1

    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    with open(TPL, encoding='utf-8') as f:
        tpl = f.read()

    # ---------- meta ----------
    meta = data.get('meta') or {}
    for k in ('title', 'sub', 'checked', 'promptGroups'):
        if k not in meta:
            err('meta: нет поля "%s"' % k)
    meta['built'] = datetime.datetime.now().strftime('%d.%m.%Y')
    data['meta'] = meta

    # ---------- categories ----------
    cats = data.get('categories') or []
    cat_ids = set()
    if not cats:
        err('categories: пусто')
    for c in cats:
        for k in ('id', 'name', 'emo', 'color'):
            if not c.get(k):
                err('category %r: нет поля "%s"' % (c.get('id'), k))
        if c.get('id') in cat_ids:
            err('category: повтор id "%s"' % c.get('id'))
        cat_ids.add(c.get('id'))

    # ---------- tools ----------
    tools = data.get('tools') or []
    tool_ids = set()
    free_vals = ('full', 'limited', 'paid')
    for t in tools:
        tid = t.get('id')
        if not tid:
            err('tool без id: %r' % t.get('name'))
            continue
        if tid in tool_ids:
            err('tool: повтор id "%s"' % tid)
        tool_ids.add(tid)
        for k in ('name', 'tagline', 'what', 'url', 'cat', 'emo'):
            if not t.get(k):
                err('tool %s: нет поля "%s"' % (tid, k))
        if t.get('cat') not in cat_ids:
            err('tool %s: неизвестная категория "%s"' % (tid, t.get('cat')))
        if not str(t.get('url', '')).startswith('https://'):
            err('tool %s: ссылка должна начинаться с https:// (%s)' % (tid, t.get('url')))
        if not isinstance(t.get('vpn'), bool):
            err('tool %s: поле vpn должно быть true/false' % tid)
        if t.get('free') not in free_vals:
            err('tool %s: free должен быть full/limited/paid, а не %r' % (tid, t.get('free')))
        if t.get('diff') not in (1, 2, 3):
            err('tool %s: diff должен быть 1/2/3' % tid)
        if not t.get('steps'):
            err('tool %s: нет шагов «Как начать»' % tid)
        if not t.get('keys'):
            warn('tool %s: нет keys — поиск по русским словам будет беднее' % tid)

    for t in tools:
        for a in (t.get('alt') or []):
            if a not in tool_ids:
                err('tool %s: альтернатива "%s" не найдена' % (t.get('id'), a))

    # ---------- guides ----------
    guides = data.get('guides') or []
    g_ids = set()
    if not guides:
        err('guides: пусто')
    for g in guides:
        gid = g.get('id')
        if not gid:
            err('guide без id: %r' % g.get('title'))
            continue
        if gid in g_ids:
            err('guide: повтор id "%s"' % gid)
        g_ids.add(gid)
        for k in ('title', 'sub', 'intro', 'steps'):
            if not g.get(k):
                err('guide %s: нет поля "%s"' % (gid, k))
        if g.get('diff') not in (1, 2, 3):
            err('guide %s: diff должен быть 1/2/3' % gid)

    # ---------- prompts ----------
    prompts = data.get('prompts') or []
    p_ids = set()
    groups = set(meta.get('promptGroups') or [])
    for p in prompts:
        pid = p.get('id')
        if not pid:
            err('prompt без id: %r' % p.get('title'))
            continue
        if pid in p_ids:
            err('prompt: повтор id "%s"' % pid)
        p_ids.add(pid)
        for k in ('title', 'for', 'text', 'g'):
            if not p.get(k):
                err('prompt %s: нет поля "%s"' % (pid, k))
        if p.get('g') not in groups:
            err('prompt %s: группа "%s" не объявлена в meta.promptGroups' % (pid, p.get('g')))

    # ---------- checklist ----------
    checklist = data.get('checklist') or []
    if not checklist:
        err('checklist: пусто')
    c_ids = set()
    for k in checklist:
        kid = k.get('id')
        if not kid:
            err('checklist без id: %r' % k.get('t'))
            continue
        if kid in c_ids:
            err('checklist: повтор id "%s"' % kid)
        c_ids.add(kid)
        if not k.get('t'):
            err('checklist %s: нет текста "t"' % kid)

    if errors:
        print('НАЙДЕНЫ ОШИБКИ (%d):' % len(errors))
        for e in errors:
            print('  ✗', e)
        print('\nindex.html НЕ собран.')
        return 1

    # ---------- сборка ----------
    if '__DATA__' not in tpl:
        print('ОШИБКА: в template.html нет плейсхолдера __DATA__')
        return 1
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('</', '<\\/')
    html = tpl.replace('__DATA__', payload)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)

    # ---------- сводка ----------
    per_cat = {}
    for t in tools:
        per_cat[t['cat']] = per_cat.get(t['cat'], 0) + 1
    novpn = sum(1 for t in tools if t.get('vpn') is False)
    print('OK: собран %s' % OUT)
    print('   размер: %.0f КБ' % (os.path.getsize(OUT) / 1024))
    print('   инструментов: %d (без VPN: %d)' % (len(tools), novpn))
    for c in cats:
        print('     %-10s %2d' % (c['id'], per_cat.get(c['id'], 0)))
    print('   гайдов: %d · промптов: %d · чек-лист: %d' % (len(guides), len(prompts), len(checklist)))
    if warnings:
        print('Предупреждения (%d):' % len(warnings))
        for w in warnings:
            print('  ! ', w)
    return 0


if __name__ == '__main__':
    sys.exit(main())
