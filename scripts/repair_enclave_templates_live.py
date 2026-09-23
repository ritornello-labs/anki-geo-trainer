"""Guarded template-only enclave repair via AnkiConnect; no import or sync.

Default: inspect and prepare a timestamped backup/plan. --apply PLAN applies
exactly that reviewed plan after checking the templates have not changed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from build_apkg import guard_js
from rollout_live_update import invoke, normalized_scheduling

ROOT = Path(__file__).resolve().parent.parent
BASELINE = 'a9aa540'
BUNDLE_RE = re.compile(r'(window.GT_BUNDLES\["([^"]+)"\]=JSON.parse\(atob\(")([A-Za-z0-9+/=]+)("\)\))')


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=True, indent=2) + '\n')


def baseline(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT).decode()


def function(src, name):
    start = src.index(f'  function {name}(')
    end = src.index('\n  }', start) + len('\n  }')
    return src[start:end]


def patch_template(src):
    old_engine = guard_js(baseline('engine/geo-engine.js'))
    new_engine = guard_js((ROOT / 'engine/geo-engine.js').read_text())
    # Match Anki-guarded function text; preserve all unrelated code.
    for name in ['pointInRegion', 'el']:
        old, new = function(old_engine, name), function(new_engine, name)
        if old in src:
            assert src.count(old) == 1, name
            src = src.replace(old, new)
        elif new not in src:
            raise RuntimeError(f'Unknown live implementation: {name}')
    # Older Place/Which models lack later Sketch/scaffold code. Patch only the
    # common land-layer tail, leaving those version differences intact.
    land_tail = '    svg.appendChild(land);'
    small_layer = function(new_engine, 'buildSvg')
    small_layer = small_layer[small_layer.index('    if (!borderless) {\n      for (var si'):small_layer.index(land_tail)]
    if small_layer not in src:
        assert src.count(land_tail) == 1
        src = src.replace(land_tail, small_layer + land_tail)
    highlight = function(new_engine, 'highlightAnswer')
    if highlight not in src:
        anchor = '  function nounOf(bundle) {'
        assert src.count(anchor) == 1
        src = src.replace(anchor, highlight + '\n\n' + anchor)
    src = src.replace('if (built.byId[target]) built.byId[target].classList.add("gt-answer");',
                      'highlightAnswer(built, target);')

    def replace_bundle(match):
        scope = match[2]
        old = json.loads(base64.b64decode(match[3]))
        original = json.loads(baseline(f'data/bundles/{scope}.json'))
        current = json.loads((ROOT / 'data/bundles' / f'{scope}.json').read_text())
        # Legacy physical Place models predate the Sketch family declaration.
        # Keep their metadata; only geometry/context and engine code are repaired.
        original['families'] = old.get('families', original.get('families'))
        current['families'] = old.get('families', current.get('families'))
        if original['families'] is None:
            original.pop('families')
            current.pop('families')
        if old != original and old != current:
            raise RuntimeError(f'Live bundle differs from source baseline: {scope}')
        encoded = base64.b64encode(json.dumps(current, separators=(',', ':')).encode()).decode()
        return match[1] + encoded + match[4]
    return BUNDLE_RE.sub(replace_bundle, src)


def cards_snapshot(ids):
    rows = []
    for i in range(0, len(ids), 20):
        for card in invoke('cardsInfo', cards=ids[i:i+20]):
            row = normalized_scheduling(card)
            row['fieldsSha256'] = hashlib.sha256(json.dumps(card['fields'], sort_keys=True).encode()).hexdigest()
            rows.append(row)
        if i % 200 == 0:
            print(f'Scheduling {min(i+20,len(ids))}/{len(ids)}', flush=True)
    return rows


def prepare():
    stamp = datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')
    out = ROOT / 'backups/live-imports' / f'{stamp}-enclave-repair'
    plan = {'models': [], 'collectionCardCount': len(invoke('findCards', query='')),
            'collectionNoteCount': len(invoke('findNotes', query=''))}
    errors = []
    for name in invoke('modelNames'):
        if not name.startswith('GeoTrainer ') or name.startswith('GeoTrainer Draw '):
            continue
        query = f'note:"{name}"'
        ids = sorted(invoke('findNotes', query=query))
        if not ids:
            continue
        templates = invoke('modelTemplates', modelName=name)
        try:
            patched = {key: {side: patch_template(src) for side, src in sides.items()}
                       for key, sides in templates.items()}
        except (RuntimeError, AssertionError) as error:
            errors.append(f'{name}: {error}')
            continue
        if templates == patched:
            continue
        plan['models'].append({'name': name, 'noteIds': ids,
            'cardIds': sorted(invoke('findCards', query=query)),
            'fields': invoke('modelFieldNames', modelName=name),
            'css': invoke('modelStyling', modelName=name),
            'before': templates, 'after': patched})
        print(f'Prepared {name}: {len(ids)} notes', flush=True)
    if errors:
        raise RuntimeError('\n'.join(errors))
    dump(out / 'plan-state.json', plan)
    print(f'PLAN={out / "plan-state.json"}', flush=True)


def apply(path):
    plan = json.loads(path.read_text())
    out = path.parent
    assert not (out / 'verification.json').exists(), 'Already applied and verified'
    all_cards = sorted({cid for m in plan['models'] for cid in m['cardIds']})
    # All stale-state checks finish before the first write.
    for m in plan['models']:
        assert invoke('modelTemplates', modelName=m['name']) == m['before'], m['name']
        assert invoke('modelStyling', modelName=m['name']) == m['css']
        assert invoke('modelFieldNames', modelName=m['name']) == m['fields']
        assert sorted(invoke('findNotes', query=f'note:"{m["name"]}"')) == m['noteIds']
        assert sorted(invoke('findCards', query=f'note:"{m["name"]}"')) == m['cardIds']
    before = cards_snapshot(all_cards)
    dump(out / 'before-state.json', before)
    for m in plan['models']:
        invoke('updateModelTemplates', model={'name': m['name'], 'templates': m['after']})
        print(f'Updated {m["name"]}', flush=True)
    for m in plan['models']:
        assert invoke('modelTemplates', modelName=m['name']) == m['after'], m['name']
        assert invoke('modelStyling', modelName=m['name']) == m['css']
        assert invoke('modelFieldNames', modelName=m['name']) == m['fields']
        assert sorted(invoke('findNotes', query=f'note:"{m["name"]}"')) == m['noteIds']
        assert sorted(invoke('findCards', query=f'note:"{m["name"]}"')) == m['cardIds']
    after = cards_snapshot(all_cards)
    dump(out / 'after-state.json', after)
    assert before == after, 'Card scheduling/deck/identity changed'
    counts = {'collectionCardCount': len(invoke('findCards', query='')),
              'collectionNoteCount': len(invoke('findNotes', query=''))}
    assert all(counts[k] == plan[k] for k in counts), counts
    result = {'modelsUpdated': len(plan['models']), 'cardsVerified': len(all_cards),
              'schedulingChanges': 0, 'schemaChanges': 0, 'syncRun': False,
              'planSha256': hashlib.sha256(path.read_bytes()).hexdigest(), **counts}
    dump(out / 'verification.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', type=Path)
    args = parser.parse_args()
    if args.apply:
        apply(args.apply)
    else:
        prepare()
