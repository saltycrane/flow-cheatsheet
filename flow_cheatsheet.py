#!/usr/bin/env python
"""
Usage: python flow_cheatsheet.py

"""
import math
import os.path
import re
import urllib2
from collections import namedtuple


COMMIT = 'v0.48.0'
GITHUB_DIR = 'https://github.com/facebook/flow/tree/{commit}/'.format(commit=COMMIT)
RAW_DIR = 'https://raw.githubusercontent.com/facebook/flow/{commit}/'.format(commit=COMMIT)
FILES = [
    ('lib/core.js', 'Core'),
    ('lib/react.js', 'React'),
    ('lib/dom.js', 'Document Object Model (DOM)'),
    ('lib/bom.js', 'Browser Object Model (BOM)'),
    ('lib/cssom.js', 'CSS Object Model (CSSOM)'),
    ('lib/indexeddb.js', 'indexedDB'),
    ('lib/node.js', 'Node.js'),
    ('lib/serviceworkers.js', 'Service Workers'),
    ('lib/streams.js', 'Streams'),
]
BUILTINS = [
    ('* (Existential type)', 'https://flow.org/en/docs/types/utilities/#toc-the-existential-type'),
    ('any', 'https://flow.org/en/docs/types/any/'),
    ('boolean', 'https://flow.org/en/docs/types/primitives/#toc-booleans'),
    ('null', 'https://flow.org/en/docs/types/primitives/#toc-null-and-void'),
    ('number', 'https://flow.org/en/docs/types/primitives/#toc-numbers'),
    ('mixed', 'https://flow.org/en/docs/types/mixed/'),
    ('string', 'https://flow.org/en/docs/types/primitives/#toc-strings'),
    ('void', 'https://flow.org/en/docs/types/primitives/#toc-null-and-void'),
    ('Arrays', 'https://flow.org/en/docs/types/arrays/'),
    ('Class<T>', 'https://flow.org/en/docs/types/utilities/#toc-class'),
    ('Classes', 'https://flow.org/en/docs/types/classes/'),
    ('Exact objects ({||} syntax)', 'https://flow.org/en/docs/types/objects/#toc-exact-object-types'),
    ('Functions', 'https://flow.org/en/docs/types/functions/'),
    ('Generics', 'https://flow.org/en/docs/types/generics/'),
    ('Interfaces', 'https://flow.org/en/docs/types/interfaces/'),
    ('Intersection types', 'https://flow.org/en/docs/types/intersections/'),
    ('Literal types', 'https://flow.org/en/docs/types/literals/'),
    ('Maybe types', 'https://flow.org/en/docs/types/maybe/'),
    ('Objects', 'https://flow.org/en/docs/types/objects/'),
    ('Tuples', 'https://flow.org/en/docs/types/tuples/'),
    ('Type aliases', 'https://flow.org/en/docs/types/aliases/'),
    ('Typeof', 'https://flow.org/en/docs/types/typeof/'),
    ('Union types', 'https://flow.org/en/docs/types/unions/'),
    ('Variable types', 'https://flow.org/en/docs/types/variables/'),
]

BUILTINS_PRIVATE = [
    ('$Abstract<T>', 'https://flow.org/en/docs/types/utilities/#toc-abstract'),
    ('$Diff<A, B>', 'https://flow.org/en/docs/types/utilities/#toc-diff'),
    ('$Exact<T>', 'https://flow.org/en/docs/types/utilities/#toc-exact'),
    ('$Keys<T>', 'https://flow.org/en/docs/types/utilities/#toc-keys'),
    ('$ObjMap<T, F>', 'https://flow.org/en/docs/types/utilities/#toc-objmap'),
    ('$PropertyType<T, x>', 'https://flow.org/en/docs/types/utilities/#toc-propertytype'),
    ('$Subtype<T>', 'https://flow.org/en/docs/types/utilities/#toc-subtype'),
    ('$Supertype<T>', 'https://flow.org/en/docs/types/utilities/#toc-supertype'),
]
OUTPUT_FILE = 'dist/index.html'

Result = namedtuple('Result', ['name', 'line_no', 'members', 'filename', 'type'])

def main():
    builtin_results = [('builtins', 'Built-ins', BUILTINS)]
    builtin_magic_results = [('builtins-private', 'Built-in "private" types', BUILTINS_PRIVATE)]
    lib_results = get_lib_results()
    write_output(builtin_results + builtin_magic_results + lib_results)

def get_builtin_magic_results():
    FILENAME = 'src/typing/type_annotation.ml'
    url = RAW_DIR + FILENAME
    print url
    body = download_file(url)

    # parse file
    results = []
    for line_no, line in enumerate(body.splitlines()):
        match = re.search(r'\(\*\s*(\$.*)\s*\*\)', line)
        if match:
            results.append(Result(match.group(1), line_no, None, FILENAME, None))

    # post-process results
    results = [
        result for result in results
        if not result.name.startswith((
                '$Either', '$All', '$Tuple', '$Type',
        ))]
    results = sorted(results, key=lambda result: result.name.lower())

    return [('builtins-private', 'Built-in "private" types', results)]

def get_lib_results():
    results = []
    for filename, heading in FILES:
        url = os.path.join(RAW_DIR, filename)
        print url
        body = download_file(url)
        file_results = parse_file(body, filename)
        file_results = post_process(file_results)
        public_results = [result for result in file_results if not is_magic(result)]
        magic_results = [result for result in file_results if is_magic(result)]
        results.append((filename, heading, public_results))
        results.append((filename + '-private', heading + ' "private" types', magic_results))
    return results

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
        match = re.search(r'^declare (module) (?P<type>.+) {', line)
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
        match = re.search(r'^}', line)
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

def is_magic(result):
    # https://github.com/facebook/flow/issues/2197#issuecomment-238001710
    # http://sitr.us/2015/05/31/advanced-features-in-flow.html
    return '$' in result.name

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
    fout.write('<a href="https://flow.org/">Flow</a> is a static type checker for Javascript.\n')
    fout.write('This is a list of Flow types generated from the source code in ')
    fout.write('<a href="{GITHUB_DIR}">{GITHUB_DIR}</a>\n'.format(GITHUB_DIR=GITHUB_DIR))
    fout.write('The script to generate this list is on <a href="https://github.com/saltycrane/flow-cheatsheet">github</a>.\n')
    fout.write('Fixes welcome.\n')
    fout.write('</p>\n')
    fout.write('<p>Note: I created a separate section for "private" or "magic" types with a <code>$</code> in the name.\n')
    fout.write('See the <a href="http://sitr.us/2015/05/31/advanced-features-in-flow.html">note here</a> and <a href="https://github.com/facebook/flow/issues/2197#issuecomment-238001710">comment here</a>. <em>Update</em>: Some these types are now <a href="https://flow.org/en/docs/types/utilities/">documented here</a>.</p>')
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
