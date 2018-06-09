#!/usr/bin/env python
"""
Usage: python flow_cheatsheet.py

"""
import math
import os.path
import re
import urllib2
from collections import namedtuple


Result = namedtuple('Result', ['name', 'line_no', 'members', 'filename', 'type'])
Version = namedtuple('Version', ['minor'])

# Global variables set by main()
GITHUB_DIR = None
RAW_DIR = None

# Constants
COMMITS = [
    'v0.74.0',
    'v0.73.0',
    'v0.72.0',
    'v0.71.0',
    'v0.70.0',
    'v0.69.0',
    'v0.68.0',
    'v0.67.0',
    'v0.66.0',
    'v0.65.0',
    'v0.64.0',
    'v0.63.1',
    'v0.62.0',
    'v0.61.0',
    'v0.60.1',
    'v0.59.0',
    'v0.58.0',
    'v0.57.3',
    'v0.56.0',
    'v0.55.0',
    'v0.54.0',
    'v0.53.1',
    'v0.52.0',
    'v0.51.1',
    'v0.50.0',
    'v0.49.1',
    'v0.48.0',
    'v0.47.0',
    'v0.46.0',
    'v0.45.0',
]

FILES = [
    ('lib/core.js', 'Core', None),
    ('lib/react.js', 'React', None),
    ('lib/react-dom.js', 'React DOM', Version(55)),
    ('lib/dom.js', 'Document Object Model (DOM)', None),
    ('lib/bom.js', 'Browser Object Model (BOM)', None),
    ('lib/cssom.js', 'CSS Object Model (CSSOM)', None),
    ('lib/indexeddb.js', 'indexedDB', None),
    ('lib/node.js', 'Node.js', None),
    ('lib/serviceworkers.js', 'Service Workers', None),
    ('lib/streams.js', 'Streams', None),
    ('lib/intl.js', 'International', Version(72)),
]

BUILTINS = [
    ('any', 'https://flow.org/en/docs/types/any/', None),
    ('boolean', 'https://flow.org/en/docs/types/primitives/#toc-booleans', None),
    ('null', 'https://flow.org/en/docs/types/primitives/#toc-null-and-void', None),
    ('number', 'https://flow.org/en/docs/types/primitives/#toc-numbers', None),
    ('mixed', 'https://flow.org/en/docs/types/mixed/', None),
    ('string', 'https://flow.org/en/docs/types/primitives/#toc-strings', None),
    ('void', 'https://flow.org/en/docs/types/primitives/#toc-null-and-void', None),
    ('Arrays ([] syntax)', 'https://flow.org/en/docs/types/arrays/', None),
    ('Class<T>', 'https://flow.org/en/docs/types/utilities/#toc-class', None),
    ('Classes', 'https://flow.org/en/docs/types/classes/', None),
    ('Covariant (read-only) (+ syntax)', 'https://flow.org/en/docs/types/interfaces/#toc-covariant-read-only-properties-on-interfaces', Version(34)),
    ('Contravariant (write-only) (- syntax)', 'https://flow.org/en/docs/types/interfaces/#toc-contravariant-write-only-properties-on-interfaces', Version(34)),
    ('Exact objects ({||} syntax)', 'https://flow.org/en/docs/types/objects/#toc-exact-object-types', Version(32)),
    ('Existential types (* syntax)', 'https://flow.org/en/docs/types/utilities/#toc-existential-type', None),
    ('Functions', 'https://flow.org/en/docs/types/functions/', None),
    ('Generics (Polymorphic or Abstract types) (<> syntax)', 'https://flow.org/en/docs/types/generics/', None),
    ('Interfaces', 'https://flow.org/en/docs/types/interfaces/', None),
    ('Intersection types (& syntax)', 'https://flow.org/en/docs/types/intersections/', None),
    ('Literal types', 'https://flow.org/en/docs/types/literals/', None),
    ('Maybe types (? syntax)', 'https://flow.org/en/docs/types/maybe/', None),
    ('Objects', 'https://flow.org/en/docs/types/objects/', None),
    ('Opaque types', 'https://flow.org/en/docs/types/opaque-types/', Version(51)),
    ('Tuples', 'https://flow.org/en/docs/types/tuples/', None),
    ('Type aliases', 'https://flow.org/en/docs/types/aliases/', None),
    ('Typeof', 'https://flow.org/en/docs/types/typeof/', None),
    ('Union types (| syntax)', 'https://flow.org/en/docs/types/unions/', None),
    ('Variable types', 'https://flow.org/en/docs/types/variables/', None),
]

BUILTINS_PRIVATE = [
    # ('$Abstract<T>', 'https://flow.org/en/docs/types/utilities/#toc-abstract', None),
    ('$Call<F>', 'https://flow.org/en/docs/types/utilities/#toc-call', Version(55)),
    ('$Diff<A, B>', 'https://flow.org/en/docs/types/utilities/#toc-diff', None),
    ('$ElementType<T, K>', 'https://flow.org/en/docs/types/utilities/#toc-elementtype', Version(49)),
    ('$Exact<T>', 'https://flow.org/en/docs/types/utilities/#toc-exact', None),
    ('$Keys<T>', 'https://flow.org/en/docs/types/utilities/#toc-keys', None),
    ('$ObjMap<T, F>', 'https://flow.org/en/docs/types/utilities/#toc-objmap', None),
    ('$PropertyType<T, k>', 'https://flow.org/en/docs/types/utilities/#toc-propertytype', None),
    ('$ReadOnly<T>', 'https://flow.org/en/docs/types/utilities/#toc-readonly', Version(59)),
    ('$Rest<A, B>', 'https://flow.org/en/docs/types/utilities/#toc-rest', Version(56)),
    # ('$Subtype<T>', 'https://flow.org/en/docs/types/utilities/#toc-subtype', None),
    # ('$Supertype<T>', 'https://flow.org/en/docs/types/utilities/#toc-supertype', None),
    ('$TupleMap<T, F>', 'https://flow.org/en/docs/types/utilities/#toc-tuplemap', None),
    ('$Values<T>', 'https://flow.org/en/docs/types/utilities/#toc-values', Version(50)),
]

REACT_TYPES = [
    ('ChildrenArray<T>', 'https://flow.org/en/docs/react/types/#toc-react-childrenarray'),
    ('ComponentType<Props>', 'https://flow.org/en/docs/react/types/#toc-react-componenttype'),
    ('Element<typeof Component>', 'https://flow.org/en/docs/react/types/#toc-react-element'),
    ('ElementProps<typeof Component>', 'https://flow.org/en/docs/react/types/#toc-react-elementprops'),
    ('ElementRef<typeof Component>', 'https://flow.org/en/docs/react/types/#toc-react-elementref'),
    ('ElementType', 'https://flow.org/en/docs/react/types/#toc-react-elementtype'),
    ('Key', 'https://flow.org/en/docs/react/types/#toc-react-key'),
    ('Node', 'https://flow.org/en/docs/react/types/#toc-react-node'),
    ('Ref<typeof Component>', 'https://flow.org/en/docs/react/types/#toc-react-ref'),
    ('StatelessFunctionalComponent<Props>', 'https://flow.org/en/docs/react/types/#toc-react-statelessfunctionalcomponent'),
]
PUBLISH_BASE_URL = '/flow-type-cheat-sheet'


def main():
    global GITHUB_DIR
    global RAW_DIR

    for commit in COMMITS:
        GITHUB_DIR = 'https://github.com/facebook/flow/tree/{commit}/'.format(commit=commit)
        RAW_DIR = 'https://raw.githubusercontent.com/facebook/flow/{commit}/'.format(commit=commit)

        builtin_results = [('builtins', 'Built-ins', BUILTINS)]
        builtin_magic_results = get_builtin_magic_results()
        lib_results = get_lib_results(commit)
        results = builtin_results + builtin_magic_results + lib_results
        write_output(results, commit)


def get_builtin_magic_results():
    FILENAME = 'src/typing/type_annotation.ml'
    url = RAW_DIR + FILENAME
    print url
    body = download_file(url)

    # parse file
    results = []
    for line_no, line in enumerate(body.splitlines()):
        match = re.search(r'\(\*\s*(\$.*)$', line)
        if match:
            name = match.group(1).replace('*)', '')
            results.append(Result(name, line_no, None, FILENAME, None))

    # post-process results
    def is_documented(type_name):
        documented_builtin_names = [x[0] for x in BUILTINS_PRIVATE]
        documented_builtin_names = [x.split('<')[0] for x in documented_builtin_names]
        return type_name.startswith(tuple(documented_builtin_names))

    results = [x for x in results if not is_documented(x.name)]
    results += BUILTINS_PRIVATE
    results = sorted(results, key=lambda result: result[0].lower())

    return [('builtins-private', 'Built-in "private" types', results)]


def get_lib_results(commit):
    cheatsheet_version_minor = parse_version_string(commit)
    results = []
    for filename, heading, min_version in FILES:
        if min_version and cheatsheet_version_minor < min_version.minor:
            print "cheatsheet version:", cheatsheet_version_minor, "is less than feature min version:", min_version, "skipping..."
            continue

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
    multiline = False
    for single_line_no, single_line in enumerate(body.splitlines()):

        # multi-line handling... if the line starts a type declaration but
        # finishes on a subsequent line, enter multiline state and start
        # concatenating lines until the final character is found.
        CHAR_DENOTING_END_OF_MULTILINE = {
            'declare class': '{',
            'type': '=',
        }

        # start of multi-line
        match = re.search(r'^\s*(declare class|type) .+', single_line)
        if match and CHAR_DENOTING_END_OF_MULTILINE[match.group(1)] not in single_line:
            multiline = True
            line_no = single_line_no
            line = single_line
            end_char = CHAR_DENOTING_END_OF_MULTILINE[match.group(1)]
            continue

        # in multiline state
        elif multiline:
            line = line + single_line
            # end of multiline
            if end_char in single_line:
                multiline = False
            # still in multiline state
            else:
                continue

        # not a multiline, treat as normal
        else:
            line_no = single_line_no
            line = single_line

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

        match = re.search('^' + indentation + r'declare (export )?(class) (?P<type>.+) {', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "class"))
            continue

        match = re.search('^' + indentation + r'declare (export )?(interface) (?P<type>.+) {', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "interface"))
            continue

        match = re.search('^' + indentation + r'declare (export )?var (?P<type>.+)', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "var"))
            continue

        match = re.search('^' + indentation + r'(declare )?(export )?type (?P<type>.+) =', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "type"))
            continue

        match = re.search('^' + indentation + r'(declare )?(export )?opaque type (?P<type>.+);', line)
        if match:
            appender.append(Result(match.group('type'), line_no, None, filename, "opaque type"))
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
        if '>' in name:
            name = re.sub(r'^(.*\>)', r'\1', name)
        else:
            name = re.sub(r'=.*$', '', name)
            name = re.sub(r': .*$', '', name)

        name = re.sub(r'extends.*$', '', name)
        # remove quotes
        name = name.strip('\'"')

        return Result(name, line_no, members, filename, type)

    results = [transform_result(result) for result in results]
    results = sorted(results, key=lambda result: result.name.lower())
    return results


def write_output(results, commit):
    version_list = []
    for index, version in enumerate(COMMITS):
        if index == 0:
            slug = 'latest'
        else:
            slug = version

        if version == commit:
            version_list.append(
                ' <strong style="font-size: 120%">{version}</strong>'.format(
                    version=version))
        else:
            version_list.append(
                ' <a href="{base_url}/{slug}/">{version}</a>'.format(
                    base_url=PUBLISH_BASE_URL, slug=slug, version=version))

    OUTPUT_FILE = 'dist/{commit}.html'.format(commit=commit)
    fout = open(OUTPUT_FILE, 'w')
    fout.write('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">\n\n')
    fout.write('<p>\n')
    fout.write('<a href="https://flow.org/"><strong>Flow</strong></a> is a static type checker for JavaScript.\n')
    fout.write('This is a list of Flow types generated from the source code in ')
    fout.write('<a href="{GITHUB_DIR}">{GITHUB_DIR}</a>\n'.format(GITHUB_DIR=GITHUB_DIR))
    fout.write('The script to generate this list is <a href="https://github.com/saltycrane/flow-cheatsheet">on github</a>.\n')
    fout.write('Fixes welcome.\n')
    fout.write('</p>\n')
    fout.write('<ul>\n')
    fout.write('<li>There are separate sections for "private" or "magic" types with a <code>$</code> in the name.\n')
    fout.write('See the <a href="http://sitr.us/2015/05/31/advanced-features-in-flow.html">note here</a> and <a href="https://github.com/facebook/flow/issues/2197#issuecomment-238001710">comment here</a>. <em>Update</em>: Some these types are now <a href="https://flow.org/en/docs/types/utilities/"><strong>documented here</strong></a>.</li>')
    fout.write('<li>Links in <strong>bold</strong> point to the Flow documentation. Other links point to the Flow source code.</li>\n')
    fout.write('</ul>\n')
    fout.write('<p>Flow version: {versions}</p>\n'.format(versions=''.join(version_list)))
    fout.write('<h4 id="contents">Contents</h4>\n')
    fout.write('<ul class="list-unstyled">\n')
    fout.write('  <li><a href="#builtins">Built-in types</a></li>')

    cheatsheet_version_minor = parse_version_string(commit)
    for filename, heading, min_version in FILES:
        if min_version and cheatsheet_version_minor < min_version.minor:
            print "cheatsheet version:", cheatsheet_version_minor, "is less than feature min version:", min_version, "skipping..."
            continue

        fout.write('  <li><a href="#{filename}">{heading}</a></li>\n'.format(
            filename=filename, heading=heading))
    fout.write('</ul>\n')

    for id_attr, heading, file_results in results:

        if not file_results:
            continue

        lines = generate_output_lines(file_results, id_attr, commit)
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


def generate_output_lines(results, id_attr, commit):
    """generate html output lines to write given a list of results
    """
    cheatsheet_version_minor = parse_version_string(commit)

    output = []
    for result in results:
        if len(result) <= 3:
            # result is a built-in result
            name, url, min_version = result

            if min_version and cheatsheet_version_minor < min_version.minor:
                print "cheatsheet version:", cheatsheet_version_minor, "is less than feature min version:", min_version, "skipping..."
                continue

            link = generate_alink(name, url, None, None, True, min_version)
            output.append('<li>{link}</li>'.format(link=link))
        else:
            # result is parsed from /lib file
            lines = generate_result(result, id_attr)
            output.extend(lines)
    return output


def generate_result(result, id_attr):
    """recursively generate html lines to write starting at a single result
    """
    lines = []
    name, line_no, members, filename, type = result
    url = create_github_url(line_no, filename)
    if members:
        link = generate_alink(name, url, type, id_attr)
        lines.append('<li>{link}<ul>'.format(link=link))
        for child_result in members:
            child_lines = generate_result(child_result, id_attr)
            lines.extend(child_lines)
        # mutate list so that <ul> tags don't count as items in the list when grouping columns
        lines[-1] = '{last_line}</ul></li>'.format(last_line=lines[-1])
    else:
        link = generate_alink(name, url, type, id_attr)
        lines.append('<li>{link}</li>'.format(link=link))
    return lines


def generate_alink(name, url, type=None, id_attr=None, from_docs=False, min_version=None):
    """return html for a single <a> link
    """
    if id_attr == 'lib/react.js':
        parts = name.split('<')
        base_name = parts[0]
        for name_docs, url_docs in REACT_TYPES:
            parts = name_docs.split('<')
            base_name_docs = parts[0]
            if base_name == base_name_docs:
                alink = '<a href="{url_docs}"><strong>{name_docs}</strong></a> <small><a href="{url}">({type})</a></small>'.format(
                    url_docs=url_docs, name_docs=html_escape(name_docs), url=url, type=type)
                return alink

    if from_docs:
        alink = '<a href="{url}"><strong>{name}</strong></a>'.format(
            url=url, name=html_escape(name))
        if min_version:
            git_tag = 'v0.{min_version.minor}.0'.format(min_version=min_version)
            release_url = 'https://github.com/facebook/flow/releases/tag/{git_tag}'.format(git_tag=git_tag)
            alink += ' <small><em>(<a href="{release_url}">since {git_tag}</a>)</em></small>'.format(
                release_url=release_url, git_tag=git_tag)
    else:
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


def parse_version_string(version_string):
    match = re.search(
        r'v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$', version_string)
    if match:
        version_minor = int(match.group('minor'))
    else:
        raise Exception('Could not parse commit version', commit)
    return version_minor


def html_escape(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


if __name__ == '__main__':
    main()
