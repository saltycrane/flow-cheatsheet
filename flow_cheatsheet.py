#!/usr/bin/env python
"""
Usage: python flow_cheatsheet.py

"""
import math
import os.path
import re
import urllib2
from collections import namedtuple


COMMIT = 'v0.29.0'
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

Result = namedtuple('Result', ['name', 'line_no', 'members', 'filename', 'type'])

def main():
    results = [('builtins', 'Built-in types', BUILTINS)]
    for filename, heading in FILES:
        url = os.path.join(RAW_DIR, filename)
        print url
        body = download_file(url)
        file_results = parse_file(body, filename)
        file_results = post_process(file_results)
        public_results = [result for result in file_results if not is_private(result)]
        private_results = [result for result in file_results if is_private(result)]
        results.append((filename, heading, public_results))
        results.append((filename, heading + ' "private" types', private_results))

    write_output(results)

def download_file(url):
    f = urllib2.urlopen(url)
    body = f.read()
    return body

def parse_file(body, filename):
    """extract data from the file using regular expressions
    """
    results = []
    indentation = ''
    module = None
    for line_no, line in enumerate(body.splitlines()):
        # start of a module
        match= re.search(r'^declare (module) (?P<type>.+) {', line)
        if match:
            indentation = r'\s+'
            module = Result(
                name=match.group('type'),
                line_no=line_no,
                members=[],
                filename=filename,
                type="module"
            )
            continue

        # end of a module
        match= re.search(r'^}', line)
        if match and module:
            indentation = ''
            results.append(module)
            module = None
            continue

        # choose whether to append matches to module.members or the top-level results list
        if module:
            appender = module.members
        else:
            appender = results

        match = re.search('^' + indentation + r'declare (class) (?P<type>.+) {', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "class"))
            continue

        match = re.search('^' + indentation + r'declare (interface) (?P<type>.+) {', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "interface"))
            continue

        match= re.search('^' + indentation + r'declare var (?P<type>.+)', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "var"))
            continue

        match = re.search('^' + indentation + r'type (?P<type>.+) =', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "type"))
            continue

    return results

def is_private(result):
    # not sure if this is correct, but there was a reference to "$" here:
    # http://sitr.us/2015/05/31/advanced-features-in-flow.html
    return result.name.startswith('_') or '$' in result.name

def post_process(results):
    """sort and clean the results
    """
    def transform_result(result):
        name, line_no, members, filename, type = result

        if members:
            members = post_process(members)

        # remove unwanted stuff at end
        name = re.sub(r'extends.*$', '', name)
        name = re.sub(r'=.*$', '', name)
        name = re.sub(r': .*$', '', name)

        # remove quotes
        name = name.strip('\'"')

        return Result(name, line_no, members, filename, type)

    results = [transform_result(result) for result in results]
    results = sorted(results, key=lambda result: result.name.lower())
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
    fout.write('<p>Note: I guess names with a <code>$</code> are supposed to be private so I separated them into their own section labeled X "private" types. See the note about that in <a href="http://sitr.us/2015/05/31/advanced-features-in-flow.html">http://sitr.us/2015/05/31/advanced-features-in-flow.html</a>.</p>\n')
    fout.write('<p>Flow version: {version}</p>\n'.format(version=COMMIT))
    fout.write('<ul class="list-unstyled">\n')
    fout.write('  <li><a href="#builtins">Built-in types</a></li>')
    for filename, heading in FILES:
        fout.write('  <li><a href="#{filename}">{heading}</a></li>\n'.format(
            filename=filename, heading=heading))
    fout.write('</ul>\n')

    for id_attr, heading, file_results in results:

        if not file_results:
            continue

        lines = generate_output_lines(file_results)
        grouped = group_in_columns(lines)

        fout.write('<div class="panel panel-default">\n')
        fout.write('<div class="panel-heading"><h4 id={id_attr}>{heading}</h4></div>\n'.format(
            id_attr=id_attr, heading=heading, count=len(lines)))
        fout.write('<div class="panel-body">\n')
        fout.write('<div class="row">\n')

        ul_tag_count = 0
        for group in grouped:

            extra_ul_tags = '<ul>' * ul_tag_count
            fout.write('<div class="col-sm-4"><ul>' + extra_ul_tags + '\n')
            for line in group:
                if '<ul>' in line:
                    ul_tag_count += 1
                if '</ul>' in line:
                    ul_tag_count -= 1
                fout.write(line + '\n')

            extra_ul_tags = '</ul>' * ul_tag_count
            fout.write(extra_ul_tags + '</ul></div>\n')

        fout.write('</div></div></div>\n')

    fout.close()

def generate_output_lines(results):
    """generate html output lines to write given a list of results
    """
    output= []
    for result in results:
        if len(result) == 2:
            # result is a built-in result
            name, url = result
            link = generate_alink(name, url, None)
            output.append('<li>{link}</li>'.format(link=link))
        else:
            lines = generate_result(result)
            output.extend(lines)
    return output

def generate_result(result):
    """recursively generate html lines to write starting at a single result
    """
    lines = []
    name, line_no, members, filename, type = result
    url = create_github_url(line_no, filename)
    if members:
        link = generate_alink(name, url, type)
        lines.append('<li>{link}<ul>'.format(link=link))
        for child_result in members:
            child_lines = generate_result(child_result)
            lines.extend(child_lines)
        # mutate list so that <ul> tags don't count as items in the list when grouping columns
        lines[-1] = '{last_line}</ul></li>'.format(last_line=lines[-1])
    else:
        link = generate_alink(name, url, type)
        lines.append('<li>{link}</li>'.format(link=link))
    return lines

def generate_alink(name, url, type=None):
    """return html for a single <a> link
    """
    alink = '<a href="{url}">{name}</a>'.format(url=url, name=html_escape(name))
    if type:
        alink += ' <small>({type})</small>'.format(type=type)
    return alink

def create_github_url(line_no, filename):
    return '{github_url}#L{line_no}'.format(
        github_url=(GITHUB_DIR + filename), line_no=(line_no + 1))

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
