#!/usr/bin/env python
import math
import os.path
import re
import urllib2


COMMIT = 'v0.27.0'
GITHUB_DIR = 'https://github.com/facebook/flow/blob/{commit}/lib/'.format(commit=COMMIT)
RAW_DIR = 'https://raw.githubusercontent.com/facebook/flow/{commit}/lib/'.format(commit=COMMIT)
FILES = [
    ('core.js', 'Core'),
    ('react.js', 'React'),
    ('dom.js', 'Document Object Model (DOM)'),
    ('bom.js', 'Browser Object Model (BOM)'),
    ('cssom.js', 'CSS Object Model (CSSOM)'),
    ('indexeddb.js', 'indexedDB'),
    ('node.js', 'Node.js'),
]
BUILTINS = [
    ('any', 'https://flowtype.org/docs/builtins.html#any'),
    ('boolean', 'https://flowtype.org/docs/builtins.html#boolean'),
    ('literal types', 'https://flowtype.org/docs/builtins.html#literal-types'),
    ('mixed', 'https://flowtype.org/docs/builtins.html#mixed'),
    ('null', 'https://flowtype.org/docs/builtins.html#null-and-void'),
    ('number', 'https://flowtype.org/docs/builtins.html#number'),
    ('string', 'https://flowtype.org/docs/builtins.html#string'),
    ('void', 'https://flowtype.org/docs/builtins.html#null-and-void'),
]
OUTPUT_FILE = 'dist/index.html'

def main():
    results = [('builtins', 'Built-in types', BUILTINS)]
    for filename, heading in FILES:
        url = os.path.join(RAW_DIR, filename)
        print url
        body = download_file(url)
        file_results = parse_file(body, filename)
        file_results = sorted(file_results, key=lambda item: item[0].lower())
        results.append((filename, heading, file_results))

    write_output(results)

def download_file(url):
    f = urllib2.urlopen(url)
    body = f.read()
    return body

def parse_file(body, filename):
    results = []
    for line_no, line in enumerate(body.splitlines()):
        match= re.search(r'^declare (class|interface|module) (?P<type>.+) {', line)
        if match:
            results.append((match.group('type'), line_no))
            continue

        match= re.search(r'^declare var (?P<type>.+)', line)
        if match:
            results.append((match.group('type'), line_no))
            continue

        match = re.search(r'type (?P<type>.+) =', line)
        if match:
            results.append((match.group('type'), line_no))
            continue

    # filter out items starting with "_" and "$"
    results = [
        (item, line_no) for (item, line_no) in results
        if not item.startswith('_') and not item.startswith('$')]

    # remove unwanted stuff at end
    def more_cleanup(item):
        item = re.sub(r'extends.*$', '', item)
        item = re.sub(r'=.*$', '', item)
        item = re.sub(r': {$', '', item)
        item = re.sub(r': \S+;$', '', item)
        return item

    def create_github_link(line_no):
        return '{github_link}#L{line_no}'.format(
            github_link=(GITHUB_DIR + filename), line_no=(line_no + 1))

    results = [
        (more_cleanup(item), create_github_link(line_no))
        for (item, line_no) in results]

    return results

def write_output(results):
    fout = open(OUTPUT_FILE, 'w')

    fout.write('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">\n')
    fout.write('<p>\n')
    fout.write('<a href="https://flowtype.org/">Flow</a> is a static type checker for Javascript.\n')
    fout.write('This is a list of Flow types generated from the source code in ')
    fout.write('<a href="{GITHUB_DIR}">{GITHUB_DIR}</a>\n'.format(GITHUB_DIR=GITHUB_DIR))
    fout.write('The script to generate this list is on <a href="https://github.com/saltycrane/flow-cheatsheet">github</a>.\n')
    fout.write('Fixes welcome.\n')
    fout.write('</p>\n')
    fout.write('<p>Flow version: {version}</p>\n'.format(version=COMMIT))
    fout.write('<ul class="list-unstyled">\n')
    fout.write('  <li><a href="#builtins">Built-in types</a></li>')
    for filename, heading in FILES:
        fout.write('  <li><a href="#{filename}">{heading}</a></li>\n'.format(
            filename=filename, heading=heading))
    fout.write('</ul>\n')

    for id_attr, heading, file_results in results:

        grouped = group_in_columns(file_results)

        fout.write('<div class="panel panel-default">\n')
        fout.write('<div class="panel-heading"><h4 id={id_attr}>{heading}</h4></div>\n'.format(
            id_attr=id_attr, heading=heading, count=len(file_results)))
        fout.write('<div class="panel-body">\n')
        fout.write('<div class="row">\n')

        for group in grouped:

            fout.write('<div class="col-sm-4"><ul class="list-unstyled">\n')
            for item, link in group:
                fout.write(
                    '  <li><a href="{link}">{item}</a></li>\n'.format(
                        link=link, item=html_escape(item)))

            fout.write('</div></ul>\n')

        fout.write('</div></div></div>')

    fout.close()

def group_in_columns(items):
    N_COLUMNS = 3.0
    rows_per_col = int(math.ceil(len(items) / N_COLUMNS))
    grouped = []
    group = []
    row_count = 0

    for item in items:
        group.append(item)

        row_count += 1
        if row_count >= rows_per_col:
            grouped.append(group)
            group = []
            row_count = 0

    if group:
        grouped.append(group)

    return grouped

def html_escape(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

if __name__ == '__main__':
    main()
