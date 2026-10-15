#!/usr/bin/env python3
"""Validate an optional project declaration offline. Never probe or install anything."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re

IDENTIFIER = r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}'
KINDS = {'availability', 'readiness', 'dependency', 'version', 'backlog', 'heartbeat', 'business'}


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('contract_invalid')


def match(pattern, value):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('contract_invalid')


def safe_path(value):
    match(r'/[A-Za-z0-9_./-]{0,240}', value)
    if '..' in value or '//' in value:
        raise ValueError('contract_invalid')


def validate(raw):
    fields(raw, ('schema', 'enabled'), ('mode', 'native', 'checks'))
    if raw['schema'] != 'mawflow.runtime_health_contract.v1' or type(raw['enabled']) is not bool:
        raise ValueError('contract_invalid')
    if raw['enabled'] is False:
        if set(raw) != {'schema', 'enabled'}:
            raise ValueError('disabled_declaration_must_be_minimal')
        return 'disabled'
    if raw.get('mode') == 'native':
        fields(raw, ('schema', 'enabled', 'mode', 'native'))
        item = raw['native']
        fields(item, ('path', 'scope', 'response_envelope'), ('tenant_required',))
        safe_path(item['path'])
        match(IDENTIFIER, item['scope'])
        if item['response_envelope'] not in {'direct', 'common-result'} or type(item.get('tenant_required', False)) is not bool:
            raise ValueError('contract_invalid')
        return 'native'
    if raw.get('mode') != 'sidecar':
        raise ValueError('contract_invalid')
    fields(raw, ('schema', 'enabled', 'mode', 'checks'))
    if not isinstance(raw['checks'], list) or not 1 <= len(raw['checks']) <= 16:
        raise ValueError('contract_invalid')
    keys = set()
    for item in raw['checks']:
        fields(item, ('key', 'kind', 'target', 'path', 'required', 'assertion'))
        match(IDENTIFIER, item['key'])
        match(IDENTIFIER, item['target'])
        if item['key'] in keys or item['kind'] not in KINDS or type(item['required']) is not bool:
            raise ValueError('contract_invalid')
        keys.add(item['key'])
        safe_path(item['path'])
        rule = item['assertion']
        fields(rule, ('type',), ('pointer', 'expected', 'maximum'))
        kind = rule['type']
        if kind == 'http_status':
            fields(rule, ('type',))
            continue
        match(r'(?:/[A-Za-z0-9_.~-]{1,80}){1,8}', rule.get('pointer'))
        if kind == 'json_equals':
            fields(rule, ('type', 'pointer', 'expected'))
            if type(rule['expected']) not in (str, int, float, bool) or len(str(rule['expected'])) > 120:
                raise ValueError('contract_invalid')
            if type(rule['expected']) in (int, float) and not math.isfinite(rule['expected']):
                raise ValueError('contract_invalid')
        elif kind in {'json_number_max', 'json_age_seconds'}:
            fields(rule, ('type', 'pointer', 'maximum'))
            if type(rule['maximum']) not in (int, float) or not math.isfinite(rule['maximum']) or not 0 <= rule['maximum'] <= 2**53 - 1:
                raise ValueError('contract_invalid')
        else:
            raise ValueError('contract_invalid')
    return 'sidecar'


def inspect(root):
    path = root / '.maw/runtime-health.json'
    result = {'schema': 'mawflow.runtime_health_declaration_check.v1', 'status': 'success',
              'adoption': 'not_adopted', 'summary': '未接入可选运行健康，不影响项目评分。',
              'next_action': 'continue', 'changed_paths': [], 'evidence_refs': [], 'log_path': '',
              'runtime_verified': False, 'score_effect': 'none'}
    try:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError('contract_invalid')
        if not path.exists():
            return result
        if path.stat().st_size > 32768:
            raise ValueError('contract_invalid')
        raw = json.loads(path.read_text(encoding='utf-8'))
        mode = validate(raw)
        result.update(adoption=mode, summary='可选运行健康声明有效；未探测实际环境。', evidence_refs=[{'path': '.maw/runtime-health.json', 'kind': 'config'}])
    except (OSError, ValueError, TypeError, KeyError):
        result.update(status='failed', adoption='invalid', summary='运行健康声明无效，请按契约检查。', next_action='ai_takeover')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--format', choices=('json', 'text', 'markdown'), default='json')
    args = parser.parse_args()
    result = inspect(args.root)
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status']}: {result['summary']} ({result['adoption']})")
    return 0 if result['status'] == 'success' else 20


if __name__ == '__main__':
    raise SystemExit(main())
