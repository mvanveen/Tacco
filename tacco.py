'''
  Tacco
  =====
  Talk is cheap.  Tacco is free.
'''
import ast
from   ast import NodeVisitor
import imp
import inspect
import os
import sys

class DocVisitor(NodeVisitor):
  '''Docstring Parsing
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
    NodeVisitor.generic_visit(self, node)

  def visit_ClassDef(self, node):
    '''Metacircular Class Docstring
       ----------------------------
       This function gets all class docstrings.
       Please see this documentation for more information.
    '''
    self.recurse(node)
    
  def visit_FunctionDef(self, node):
    '''Metacircular Function Docstring
       -------------------------------
       This function returns docstrings associated to functions.  For example,
       this function is grabbed by itself and returns this docstring.

       Please see this documentation for more information.
    '''
    self.recurse(node)
  
class SectionContainer(object):
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

class Parser(object):
  def __init__(self, file):
    with open(file, 'r') as fileObj:
      self._fileObj = fileObj.read()

    file = os.path.splitext(file) 
    assert file[-1] == '.py'

    self._fileStr  = file[0]
    self._sections = SectionContainer()

    self._docVisitor = DocVisitor()
    
    self._sections.addDoc(self.getModuleDoc())
   
    #~ Parse source file for docstrings, and add the results to the container.
    self._docVisitor.visit(ast.parse(self._fileObj))
    self._sections.addDict(
        dict( filter( lambda x: x[1] is not None,
                      self._docVisitor.getDoc().iteritems()
                    )))

    #~ Add marked documentation (like this line!).
    map(self._sections.addDoc, self.getMarkedDoc())

  def renderSection(self, section):
    # Render doc into markdown  (clean up too)
    # get code
    # pygmentize code
    # Pop into section.  Bam.
    pass

  def renderDoc(self, section):
    return {'body' : map(self.renderSection, self._sections.getDoc())}

  def getModuleDoc(self):
    '''Grabs module-level documentation.
       Module Documentation
       --------------------
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
    '''Grabs documentation lines which start with '#~'
       Marked Documentation
       --------------------
       Sometimes, a docstring isn't the appropriate place to put documentation.
       You can include a comment as part of the source documentation by starting
       the comment line with '#~'.
    '''
    assert self._fileObj
    lines = self._fileObj.split('\n')
    return [ (line, x) for line, x in zip(range(len(lines)), lines)
               if x.lstrip().startswith('#~') ]
  
  def getResults(self):
    '''Return parsed document results, sorted by comment.'''
    doc = self._sections.getDoc()
    assert doc
    return(sorted([x for x in doc.iteritems()]))
    
if __name__ == '__main__':
  print Parser('tacco.py').getResults()
