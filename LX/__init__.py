"""
Main LX package import point.

We import most modules here, so users can just use LX.Foo instead of
LX.foo.Foo.  That means we have to be more careful about naming
conflicts, but it also gives us more freedom to move code between
files without affecting the API.
"""
__version__ = "$Revision$"
# $Id$

# To allow "from LX import *", though I'm not sure when/why one would
# want that.
__all__ = ["operator", "language", "formula", "term", "kb"] 

# Let people use LX.Formula instead of LX.formula.Formula, etc, while
# having these parts in separate files
from LX.operator import *
from LX.term import *
from LX.formula import *
from LX.kb import *

from LX.namespace import *
rdfns  = HardNamespace("http://www.w3.org/1999/02/22-rdf-syntax-ns",
                        ["type", "nil", "first", "rest"])
lxns   = SoftNamespace("http://www.w3.org/1999/02/22-rdf-syntax-ns")



# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
