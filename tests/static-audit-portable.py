#!/usr/bin/env python3
"""Evaluate the existing PowerShell audit's assertions without PowerShell.
This is a deliberately narrow port: unsupported expressions fail, not skip.
"""
import pathlib, re, subprocess
root = pathlib.Path(__file__).resolve().parents[1]
values = {key: (root / path).read_text() for key, path in {
    'main': 'payload/game_pad_bridge_main.c',
    'bridge': 'payload/wireless_ds4.c', 'makefile': 'payload/Makefile'}.items()}
values['readerGate'] = values['main'].find('restoring wireless reader before game scan')
values['gameInstall'] = values['main'].find('int install_result = wireless_ds4_game_bridge_install(')
values['installerStart'] = values['bridge'].find('wireless_ds4_game_bridge_run_passive(')
values['installerEnd'] = values['bridge'].find('wireless_ds4_game_bridge_install(', values['installerStart'])
values['installer'] = values['bridge'][values['installerStart']:values['installerEnd']]
script = (root / 'tests/static-audit.ps1').read_text().replace('`\n', '')
tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files'], text=True).splitlines()
expected_section = script.split('$expectedTracked = @(', 1)[1].split(')', 1)[0]
expected = re.findall(r"'([^']+)'", expected_section)
values['tracked.Count'] = len(tracked)
values['expectedTracked.Count'] = len(expected)
count = 0
for expr, message in re.findall(r"Assert-True \((.*?)\)\s+'([^']*)'", script, re.S):
    expr = re.sub(r"\$(\w+)\.Contains\(\s*'([^']*)'\s*\)",
                  lambda m: str(m[2] in values[m[1]]), expr)
    expr = re.sub(r'\$([\w.]+)', lambda m: str(values[m[1]]), expr)
    for ps, py in [('-not','not'),('-and','and'),('-ge','>='),('-gt','>'),('-eq','==')]:
        expr = expr.replace(ps, py)
    if re.sub(r'True|False|not|and|[\s()0-9<>=-]', '', expr):
        raise RuntimeError('Unsupported audit expression: '+expr)
    assert eval(expr, {'__builtins__': {}}, {}), message
    count += 1
assert set(expected) == set(tracked), 'Tracked public tree differs from upstream audit'
print(f'PASS: {count} existing static assertions + tracked-file inventory (portable evaluator)')
