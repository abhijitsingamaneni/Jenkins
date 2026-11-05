#!/usr/bin/env python3
"""Compare a Git branch with main using their merge base."""
import argparse
import json
import subprocess
from pathlib import Path


def git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f'git command failed: {args}')
    return result.stdout


def main():
    p = argparse.ArgumentParser(description='Report changes introduced by a Git branch relative to main')
    p.add_argument('branch', help='Branch to compare')
    p.add_argument('--base', default='main', help='Base branch (default: main)')
    p.add_argument('--format', choices=['text', 'json', 'markdown'], default='text')
    p.add_argument('--output', help='Write report to this path instead of stdout')
    p.add_argument('--full-diff', action='store_true', help='Include unified code diff')
    a = p.parse_args()
    try:
        git('rev-parse', '--is-inside-work-tree')
        base = git('rev-parse', '--verify', a.base + '^{commit}').strip()
        branch = git('rev-parse', '--verify', a.branch + '^{commit}').strip()
        merge_base = git('merge-base', base, branch).strip()
        names = git('diff', '--name-status', '--find-renames', merge_base, branch)
        files = []
        for line in names.splitlines():
            parts = line.split('\t')
            status = parts[0]
            item = {'status': status, 'path': parts[-1]}
            if status.startswith(('R', 'C')) and len(parts) > 2:
                item['old_path'] = parts[1]
            files.append(item)
        commits = git('log', '--format=%h %s', f'{merge_base}..{branch}').splitlines()
        stat = git('diff', '--shortstat', merge_base, branch).strip()
        diff = git('diff', '--find-renames', merge_base, branch) if a.full_diff else None
        report = {'base': a.base, 'branch': a.branch, 'merge_base': merge_base,
                  'summary': stat, 'files': files, 'commits': commits}
        if diff is not None:
            report['diff'] = diff
        if a.format == 'json':
            output = json.dumps(report, indent=2)
        else:
            md = a.format == 'markdown'
            output = f"{'# ' if md else ''}Git branch comparison: {a.branch} vs {a.base}\n"
            output += f"Merge base: {merge_base}\nSummary: {stat or 'No file changes'}\n\n"
            output += ('## ' if md else '') + 'Changed files:\n'
            output += '\n'.join(f"{'- ' if md else ''}{f['status']}: {f['path']}" for f in files) or '(none)'
            output += '\n\n' + ('## ' if md else '') + 'Commits:\n'
            output += '\n'.join(('- ' if md else '') + c for c in commits) or '(none)'
            if diff is not None:
                output += '\n\n' + ('## Full diff\n```diff\n' if md else 'Full diff:\n') + diff + ('\n```' if md else '')
        if a.output:
            Path(a.output).write_text(output + '\n', encoding='utf-8')
            print(f'Report written to {a.output}')
        else:
            print(output)
    except (RuntimeError, OSError) as exc:
        p.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
