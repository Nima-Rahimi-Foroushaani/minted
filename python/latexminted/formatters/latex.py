from io import StringIO
from pygments.util import ClassNotFound
from pygments.formatters.latex import LatexFormatter as OriginalLatexFormatter, \
    escape_tex, _get_ttype_name, DOC_TEMPLATE
from ..styles import get_local_style_by_name
from pygments.token import Token, Whitespace

class LatexFormatterError(ValueError): ...
class LatexFormatter(OriginalLatexFormatter):
    def __init__(self, **options):
        if ('style' in options) and isinstance(options['style'], str):
            # Try to load a local style if available
            try:
                options['style'] = get_local_style_by_name(options['style'])
            except ClassNotFound:
                pass  # Ignore if the style isn't found
        super().__init__(**options)

    def format_unencoded(self, tokensource, outfile):
        # TODO: add support for background colors
        t2n = self.ttype2name
        cp = self.commandprefix

        if self.full:
            realoutfile = outfile
            outfile = StringIO()

        begin_env = end_env = ''
        if not self.nowrap:
            begin_env = '\\begin{' + self.envname + '}[commandchars=\\\\\\{\\}'
            if self.linenos:
                start, step = self.linenostart, self.linenostep
                begin_env += (',numbers=left' +
                         (start and ',firstnumber=%d' % start or '') +
                         (step and ',stepnumber=%d' % step or ''))
            if self.mathescape or self.texcomments or self.escapeinside:
                begin_env += (',codes={\\catcode`\\$=3\\catcode`\\^=7'
                         '\\catcode`\\_=8\\relax}')
            if self.verboptions:
                begin_env += (',' + self.verboptions)
            begin_env += (']\n')

            end_env = ('\\end{' + self.envname + '}\n')

        dbg = []
        last_wr = ''
        def write(buf):
            nonlocal last_wr
            if buf:
                outfile.write(buf)
                last_wr = buf
        def write_at_newline(buf):
            write(('' if last_wr.endswith('\n') else '\n') + buf)

        def tokensource_aux(ts):
            buf = []
            tokensource = iter(ts)
            for ttype, value in tokensource:
                if ttype not in Token.Escape.Block.Delimiter:
                    buf.append((ttype, value))
                else:
                    if ttype in Token.Escape.Block.Delimiter.Begin:
                        # Skip all whitespace before the escape block, back to the beginning of the line
                        not_in_nl = True
                        while buf:
                            ttype1, value1 = buf.pop()
                            heading_str = value1.rstrip()
                            trailing_ws = value1[len(heading_str):]
                            b, nl, a = trailing_ws.rpartition('\n')
                            if nl:
                                if heading_str or b:
                                    buf.append((ttype1, heading_str + b))
                                not_in_nl = False
                                break
                            elif heading_str:
                                break

                        if not_in_nl:
                            raise LatexFormatterError(
                                r'''Escape block should start in a new line separated from other parts of the code. 
                                Only white space is allowed before the escape delimiter in the new line''')

                    for tv in buf:
                        yield tv
                    buf = []
                    yield ttype, value

                    if ttype in Token.Escape.Block.Delimiter.End:
                        # Skip all whitespace after the escape block until the next line
                        not_in_nl = True
                        for ttype1, value1 in tokensource:
                            trailing_str = value1.strip()
                            heading_ws = value1[: len(value1) - len(trailing_str)]
                            b, nl, a = heading_ws.partition('\n')
                            if nl:
                                if a or trailing_str:
                                    yield (ttype1, a + trailing_str)
                                not_in_nl = False
                                break
                            elif trailing_str:
                                break
                        if not_in_nl:
                            raise LatexFormatterError(
                                r'''After an escape block the code should start in a new line. 
                                Only white space is allowed after the escape delimiter''')
            for tv in buf:
                yield tv

        write(begin_env)
        is_in_env = True

        for ttype, value in tokensource_aux(tokensource):
            if ttype in Token.Escape.Block:
                dbg.append(rf'''t:{{{ttype}}}, v:{{{value}}}''')
                if is_in_env:
                    if ttype in Token.Escape.Block.Delimiter.Begin:
                        is_in_env = False
                        write_at_newline(end_env)
                    else:
                        raise LatexFormatterError(r'''Escaped content within verbatim environment''')
                else: # in escape
                    if ttype in Token.Escape.Block.Delimiter.End:
                        is_in_env = True
                        write_at_newline(begin_env)
                    else:
                        write(value)
                continue

            # it is not part of an escape block
            if not is_in_env:
                raise LatexFormatterError(r'''Verbatim material outside verbatim environment''')

            if ttype in Token.Comment:
                if self.texcomments:
                    # Try to guess comment starting lexeme and escape it ...
                    start = value[0:1]
                    for i in range(1, len(value)):
                        if start[0] != value[i]:
                            break
                        start += value[i]

                    value = value[len(start):]
                    start = escape_tex(start, cp)

                    # ... but do not escape inside comment.
                    value = start + value
                elif self.mathescape:
                    # Only escape parts not inside a math environment.
                    parts = value.split('$')
                    in_math = False
                    for i, part in enumerate(parts):
                        if not in_math:
                            parts[i] = escape_tex(part, cp)
                        in_math = not in_math
                    value = '$'.join(parts)
                elif self.escapeinside:
                    text = value
                    value = ''
                    while text:
                        a, sep1, text = text.partition(self.left)
                        if sep1:
                            b, sep2, text = text.partition(self.right)
                            if sep2:
                                value += escape_tex(a, cp) + b
                            else:
                                value += escape_tex(a + sep1 + b, cp)
                        else:
                            value += escape_tex(a, cp)
                else:
                    value = escape_tex(value, cp)
            elif ttype not in Token.Escape:
                value = escape_tex(value, cp)

            styles = []
            while ttype is not Token:
                try:
                    styles.append(t2n[ttype])
                except KeyError:
                    # not in current style
                    styles.append(_get_ttype_name(ttype))
                ttype = ttype.parent
            styleval = '+'.join(reversed(styles))
            if styleval:
                spl = value.split('\n')
                for line in spl[:-1]:
                    if line:
                        write(f"\\{cp}{{{styleval}}}{{{line}}}")
                    write('\n')
                if spl[-1]:
                    write(f"\\{cp}{{{styleval}}}{{{spl[-1]}}}")
            else:
                write(value)

        if is_in_env:
            write_at_newline(end_env)
        import platform
        write_at_newline(f'%Latex Formatter with Escape blocks:')
        write_at_newline(f'%Python Version:{{{platform.python_version()}}}')
        write_at_newline(f'%Debug info:')
        for l in (line for di in dbg for line in di.splitlines()):
            write_at_newline('%' + l)

        if self.full:
            encoding = self.encoding or 'utf8'
            # map known existings encodings from LaTeX distribution
            encoding = {
                'utf_8': 'utf8',
                'latin_1': 'latin1',
                'iso_8859_1': 'latin1',
            }.get(encoding.replace('-', '_'), encoding)
            realoutfile.write(DOC_TEMPLATE %
                dict(docclass  = self.docclass,
                     preamble  = self.preamble,
                     title     = self.title,
                     encoding  = encoding,
                     styledefs = self.get_style_defs(),
                     code      = outfile.getvalue()))