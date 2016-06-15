#!/usr/bin/env python
import os.path
import re
import urllib2


COMMIT = 'v0.26.0'
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
OUTPUT_FILE = 'output.html'
BUILTINS_SECTION = '''
<h4 id="builtins">Built-in types</h4>
<ul>
  <li><a href="https://flowtype.org/docs/builtins.html#boolean">boolean</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#number">number</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#string">string</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#null-and-void">null</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#null-and-void">void</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#any">any</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#mixed">mixed</a></li>
  <li><a href="https://flowtype.org/docs/builtins.html#literal-types">literal types</a></li>
</ul>
'''

def main():
    fout = open(OUTPUT_FILE, 'w')
    fout.write('<p>Flow version: {version}</p>\n'.format(version=COMMIT))
    fout.write('<p>Jump to:</p>\n')
    fout.write('<ul>\n')
    fout.write('  <li><a href="#builtins">Built-in types</a></li>')
    for filename, heading in FILES:
        fout.write('  <li><a href="#{filename}">{heading}</a></li>\n'.format(
            filename=filename, heading=heading))
    fout.write('  <li><a href="#python-script">Python script</a></li>')
    fout.write('</ul>\n')
    fout.write(BUILTINS_SECTION)

    for filename, heading in FILES:
        url = os.path.join(RAW_DIR, filename)
        print url
        body = download_file(url)
        results = parse_file(body)
        results = sorted(results, key=lambda item: item[0].lower())
        write_output(fout, results, filename, heading)

    fout.close()

def download_file(url):
    f = urllib2.urlopen(url)
    body = f.read()
    return body

def parse_file(body):
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

    results = [
        (more_cleanup(item), line_no) for (item, line_no) in results]

    return results

def write_output(fout, results, filename, heading):
    fout.write('\n<h4 id={filename}>{heading} ({count})</h4>\n'.format(
        filename=filename, heading=heading, count=len(results)))

    fout.write('<ul>\n')
    for item, line_no in results:
        print line_no, item
        fout.write(
            '  <li><a href="{github_link}#L{line_no}">{item}</a></li>\n'.format(
                github_link=(GITHUB_DIR + filename),
                line_no=line_no + 1,
                item=html_escape(item),
            ))

    fout.write('</ul>\n')

def html_escape(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

if __name__ == '__main__':
    main()
