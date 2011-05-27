from deps.pystache.template import Template
from deps.pystache.view import View

def render(template, context=None, **kwargs):
    context = context and context.copy() or {}
    context.update(kwargs)
    return Template(template, context).render()
