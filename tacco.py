'''

  Tacco
  =====

  Talk is cheap.  Tacco is free.

  <img src='http://farm4.static.flickr.com/3217/2725569605_57c3d6a41a.jpg' />

  [Source] [1], [Image] [2]

  [1]: http://farm4.static.flickr.com/3217/2725569605_57c3d6a41a.jpg
  [2]: http://www.flickr.com/photos/alanjcastonguay/2725569605/

  Introduction
  ------------
  Tacco is a docco-inspired documenter for Python, attempting compliance with
  [PEP 257] [1].
  
  ### Why stick to just Python?
  Most docco-style parsers merely grep for comment strings to find 
  documentation.  This works great for a general purpose documenter (see pycco
  if this is what you're looking for), but Tacco's design philosphy is to 
  stick to pick a niche and excel at it.  By sticking with just Python, we 
  can take advantage of the language's awesome, pre-existing documentation 
  patterns and produce beautiful documentation while staying within the PEP 
  style guidelines.

  [1]: http://www.python.org/dev/peps/pep-0257/ "PEP 257"

'''

import ast
from   ast import NodeVisitor
import imp
import inspect
from   itertools import izip_longest
import os
import re
import sys

#~ External Dependencies
#~ ---------------------
#~ 

import deps.markdown as markdown
import deps.pystache as pystache
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

formatter = HtmlFormatter(cssclass="source")


class DocVisitor(NodeVisitor):
  '''Visits python file AST to grab docstrings.

     Docstring Parsing
     =================

  '''
  def __init__(self, *args):
    NodeVisitor.__init__(self, *args)
    self._docs = {}

  def recurse(self, node):
    self._docs[node.lineno] = ast.get_docstring(node)
    NodeVisitor.generic_visit(self, node)

  def getDoc(self):
    assert self._docs
    return self._docs

  def generic_visit(self, node):
    ''' Generic visitor function.
    '''
    NodeVisitor.generic_visit(self, node)

  def visit_ClassDef(self, node):
    ''' Visits class definitions, grab docstrings.

       Metacircular Class Docstring
       ----------------------------
       This function gets all class docstrings.
       Please see this documentation for more information.
    '''
    self.recurse(node)
    
  def visit_FunctionDef(self, node):
    '''
       Metacircular Function Docstring
       -------------------------------
       This function returns docstrings associated to functions.  For example,
       this function is grabbed by itself and returns this docstring.

       Please see this documentation for more information.
    '''
    self.recurse(node)
  
class SectionContainer(object):
  ''' Stores documentation and code and outputs HTML.
      
      Code Sections
      =============

  '''
  def __init__(self):
    self._doc= {}

  def addDoc(self, cmtOrSection):
    assert type(cmtOrSection) == type(())
    assert len(cmtOrSection)  == 2
    self._doc.update([cmtOrSection])
    
  def addDict(self, dict):
    assert type(dict) == type({})
    self._doc.update(dict.iteritems())

  def getDoc(self):
    assert self._doc
    return self._doc

  def getDocLength(self):
    assert self._doc
    return self._doc.__len__()

class Parser(object):
  def __init__(self, file):
    with open(file, 'r') as fileObj:
      self._fileObj = fileObj.read()

    self._code = self._fileObj.split('\n')

    file = os.path.splitext(file) 
    assert file[-1] == '.py'

    self._fileStr  = file[0]
    self._sections = SectionContainer()

    self._docVisitor = DocVisitor()
   
    self._sections.addDoc(self.getModuleDoc())
    self._sections.addDict(self.getDocstrs())

     #~ Add marked documentation (like this line!).
    map(self._sections.addDoc, self.getMarkedDoc())

  def getDocstrs(self):
    '''Gets source code docstrings and preprocesses them
    '''
    #~ Parse source file for docstrings, and add the results to the container.
    self._docVisitor.visit(ast.parse(self._fileObj))

    #~ According to PEP 257, the first docstring line is meant as a quick 
    #~ summary.  Subequently, we trim the first line of the comment if the 
    #~ docstring is greater than one line long, as its inclusion would be
    #~ repetitive.
    pepScrub = lambda x: (len(x) > 1  \
                            and not (x[1].lstrip() not in ['', '\n']) 
                            and x[1:]) or x
                           
    return( dict( map( lambda x: (x[0], '\n'.join( pepScrub(x[1].split('\n')) )),
                       filter ( lambda x: x[1] is not None,
                                self._docVisitor.getDoc().iteritems()
                              ))))

  def renderSection(self, index=0):
    '''Renders a code/comment documentation section into html

       Section Rendering
       -----------------
       Renders documents with markdown, and code sections with pygments.

       Get all sections in this source file and print the rendered results

       >>> parser  = Parser('tacco.py')
       >>> results = parser.getResults()
       >>> print map(parser.renderSection, results)
    '''
    docLength = self._sections.getDocLength()
    results   = self.getResults()

    current, mdTxt = ((index < docLength-1) and results[index+1]) \
                      or results[docLength-1]

    last, _ = results[index]
    #~ ###Parsing Test Code Sections
    #~ Doctest code is often prepended with '>>>' in a document.  We 
    #~ preprocess the docstring with this line to make sure these lines of 
    #~ code are displayed correctly.
    # TODO: Pygmentize code section?

    mdTxt = [re.sub('^[ \t]*>>>', '    ', x) for x in mdTxt.split('\n')]
    #print str((last, last+len(mdTxt), current))
    #~ get code
    code = self._code[last:current]

    print highlight('\n'.join(code), PythonLexer(), formatter)
    # pygmentize code

    # Pop into section.  Bam.
    print markdown.markdown('\n'.join(mdTxt))

  def renderDoc(self):
    '''
       Pushing To Production
       ---------------------
    '''
    return {  'header' : self.renderSection(0),
              'body' : map(self.renderSection, 
                         range(1, self._sections.getDocLength())
                        )}

  def getModuleDoc(self):
    '''Grabs module-level documentation.

       Front Matter: Grabbing Module Documentation
       -------------------------------------------
       Grabbing the docstring from the module with our visitor is unintuitive
       (special case?).  Using inspect is an easy alternative. Below, we add 
       the file path to system path to facilitate easy importation of the 
       source file we want. This lets us grab the module level docstring 
       easily.
    '''
    filePath = os.path.split(os.path.abspath(self._fileStr))[0]
    sys.path.append(filePath)
    module = __import__(self._fileStr)
    return (0, inspect.getdoc(module))

  def getMarkedDoc(self):
    '''Grabs documentation lines which start with `#~`

       What's Up With The Squigly Commments?
       -------------------------------------
       You must mean the lines starting with `#~`.

       Sometimes, a docstring isn't the appropriate place to put documentation.
       You can include a comment as part of the source documentation by starting
       the comment line with `#~`.
    '''
    assert self._fileObj
    lines = self._fileObj.split('\n')
    return [ (line, re.sub('^[ \t]*\#~', '', x)) for 
              line, x in zip(range(len(lines)), lines)
                if x.lstrip().startswith('#~') ]
 
  def getResults(self):
    '''Return parsed document results, sorted by comment.'''
    doc = self._sections.getDoc()
    assert doc
    return(sorted([self.getModuleDoc()] + [x for x in doc.iteritems()]))
    
if __name__ == '__main__':
  print '<style>'
  print formatter.get_style_defs('.source') 
  print '''
  body {float: left; min-width:500px;}
  .source {clear: both; min-width: 700px;float: right;}
  '</style>
  '''
  parser  = Parser('tacco.py')
  #results = range()
  #map(parser.renderSection, results)
  #print parser.getResults()
  #map(parser.renderDoc, range(parser._sections.getDocLength())[1:])
  parser.renderDoc()
