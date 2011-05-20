import re
import cgi

modifiers = {}
def modifier(symbol):
    """Decorator for associating a function with a Mustache tag modifier.

    @modifier('P')
    def render_tongue(self, tag_name=None, context=None):
        return ":P %s" % tag_name

    {{P yo }} => :P yo
    """
    def set_modifier(func):
        modifiers[symbol] = func
        return func
    return set_modifier

class Template(object):
    # The regular expression used to find a #section
    section_re = None

    # The regular expression used to find a tag.
    tag_re = None

    # Opening tag delimiter
    otag = '{{'

    # Closing tag delimiter
    ctag = '}}'

    def __init__(self, template, context=None):
        self.template = template
        self.context = context or {}
        self.compile_regexps()

    def render(self, template=None, context=None):
        """Turns a Mustache template into something wonderful."""
        template = template or self.template
        context = context or self.context

        template = self.render_sections(template, context)
        return self.render_tags(template, context)

    def compile_regexps(self):
        """Compiles our section and tag regular expressions."""
        tags = { 'otag': re.escape(self.otag), 'ctag': re.escape(self.ctag) }

        section = r"%(otag)s\#([^\}]*)%(ctag)s\s*(.+?)\s*%(otag)s/\1%(ctag)s"
        self.section_re = re.compile(section % tags, re.M|re.S)

        tag = r"%(otag)s(#|=|!|>|\{)?(.+?)\1?%(ctag)s+"
        self.tag_re = re.compile(tag % tags)

    def render_sections(self, template, context):
        """Expands sections."""
        while 1:
            match = self.section_re.search(template)
            if match is None:
                break

            section, section_name, inner = match.group(0, 1, 2)
            section_name = section_name.strip()

            it = context.get(section_name, None)
            replacer = ''
            if it and not hasattr(it, '__iter__'):
                replacer = inner
            elif it:
                insides = []
                for item in it:
                    insides.append(self.render(inner, item))
                replacer = ''.join(insides)

            template = template.replace(section, replacer)

        return template

    def render_tags(self, template, context):
        """Renders all the tags in a template for a context."""
        while 1:
            match = self.tag_re.search(template)
            if match is None:
                break

            tag, tag_type, tag_name = match.group(0, 1, 2)
            tag_name = tag_name.strip()
            func = modifiers[tag_type]
            replacement = func(self, tag_name, context)
            template = template.replace(tag, replacement)

        return template

    @modifier(None)
    def render_tag(self, tag_name, context):
        """Given a tag name and context, finds, escapes, and renders the tag."""
        return cgi.escape(str(context.get(tag_name, '')))

    @modifier('!')
    def render_comment(self, tag_name=None, context=None):
        """Rendering a comment always returns nothing."""
        return ''

    @modifier('{')
    def render_unescaped(self, tag_name=None, context=None):
        """Render a tag without escaping it."""
        return context.get(tag_name, '')

    @modifier('>')
    def render_partial(self, tag_name=None, context=None):
        """Renders a partial within the current context."""
        # Import view here to avoid import loop
        from pystache.view import View

        view = View(context=context)
        view.template_name = tag_name

        return view.render()

    @modifier('=')
    def render_delimiter(self, tag_name=None, context=None):
        """Changes the Mustache delimiter."""
        self.otag, self.ctag = tag_name.split(' ')
        self.compile_regexps()
        return ''
