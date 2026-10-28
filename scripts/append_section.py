"""Safely append a section to a markdown report.

Why this exists: several rounds on 2026-07-28 used

    open(path, 'w').write(open(path).read().rstrip() + section)

which TRUNCATES the file before the inner read runs — Python evaluates `open(path,'w')` first, so the
inner `open(path).read()` returns an empty string and the file is replaced by the section alone. Seven
reports lost their history that way and had to be reconstructed from git. Use this instead.

Usage:
    from append_section import append
    append('reports/foo.md', '## New section\n...')
"""
import os


def append(path: str, section: str) -> int:
    """Append `section` to `path`, preserving existing content. Returns the new line count."""
    prev = ''
    if os.path.exists(path):
        with open(path) as fh:                 # read fully and CLOSE before opening for write
            prev = fh.read()
    out = (prev.rstrip('\n') + '\n\n' + section.strip('\n') + '\n') if prev.strip() else section.strip('\n') + '\n'
    with open(path, 'a' if False else 'w') as fh:
        fh.write(out)
    return len(out.splitlines())


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('usage: append_section.py <file>   (section on stdin)')
    print(append(sys.argv[1], sys.stdin.read()))
