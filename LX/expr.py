"""Classes for storing and manipulating arbitrary expressions in the
form of abstract syntax trees (ASTs).

Expressions are always immutable.  If you want mutability, use a KB or
copy to/from a python list.  Use == for comparison instead of "is";
whether interning is done is an implementation issue.  Compound
expressions are equal if their parts are equal; simple expressions can
only be assumed to be equal if they are the same python object.  (But
some subclasses might offer additional equality conditions.)

There's a fairly clear hierarchy split between CompoundExpr and
SimpleExpr, but there are many classifications one could do of Expr's
that do not fit a single hierarchy. 

"""
__version__ = "$Revision$"
# $Id$

import LX
from string import split

def virtual():
    raise RuntimeError, "Function should have been implemented in subclass"

opTable = { }       # gets filled in later, using things not yet defined

class Expr:

    def __and__(self, other):    return CompoundExpr(opTable["and"], self, other)
    def __or__(self, other):     return CompoundExpr(opTable["or"],  self, other)
    def __rshift__(self, other): return CompoundExpr(opTable[">>"], self, other)
    def __neg__(self, other):    return CompoundExpr(opTable["-"],  self)
    def __call__(self, *args):   return apply(CompoundExpr, (self,)+args)  # (need apply() the handle varargs)

class CompoundExpr(Expr):
    """An internal branch node in an abstract syntax tree,
    representing the application of some function (or operator or
    connective) to one or more expressions.

    """

    def __init__(self, function, *args):
        """Initialize the compound expression (immutably) with
        a function expression and one or more argument expressions.

        Why don't we allow nullary functions?  Because it confuses me
        and I can't think of a reason for it.  Since functions can't
        have side effects, the value of f() is always some constant,
        so just use that constant.

        Why do we allow CompoundExpr's to be the function?  Because
        I'm brave, and I want to allow things like Currying.
        """
        assert(isinstance(function, Expr))
        self.__function = function
        assert(len(args) >= 1) 
        for arg in args:
            assert(isinstance(function, Expr))
        if hasattr(function, "checkArgs"):
            function.checkArgs(args)
        self.__args = tuple(args)
        
    def getFunction(self):
        """Return the function (also called operator, predicate, functor,
        ...) of this expression; the function is a SimpleValueExpr.
        In first-order formulas, it's a Constant.

        """
        return self.__function

    function = property(getFunction)

    def getArgs(self):
        """Return a sequence of zero or more arguments (operands) to
        the function.

        Hows is a CompoundExpr with zero arguments different from a
        simpleExpr?  There's still a level of indirection, but I don't
        know when/why you'd want that.  Perhaps we should forbid it
        until we have a good reason for it.
        """
        return self.__args

    args = property(getArgs)

    def getAll(self):
        return (self.__function,) + self.__args

    all = property(getAll)
    
    def __str__(self):
        return str(self.function)+"("+", ".join(map(str, self.args))+")"


class SimpleExpr(Expr):

    def __init__(self, suggestedName="<unnamed>"):
        self.suggestedName = suggestedName
        
    def __str__(self):
        return self.suggestedName

    def getLocallyUnambiguousName(self, nameTable):
        try:
            return nameTable[self]
        except KeyError: pass
        for extra in xrange(1, 100000000):
            if extra == 1:
                newName = self.suggestedName
            else:
                newName = self.suggestedName + str(extra)
            if newName not in nameTable.values:      # @ linear performance hit
                nameTable[self] = newName
                return newName
        raise RuntimeError, "wayyyyy to many similarly named expressions"


class Variable(SimpleExpr):
    """

    sometimes these things (maybe expr's on the whole!) have URIRefs
    -- some symbol that identifies THEM (the expr).   That's what cwm
    handed us.   Where do we keep that info?
          - in some KB or other table, outside
            (mappings URIRef -> Expr, and Expr -> URIRef; note that
            a URIRef *is* and Expr, so we could get confused really
            easily.   What is the URIRef of a URIRef?)

           **** URI GOES INTO METADATA
    """
    
    # @@@ what to do with the URIRef???
    def __init__(self, name=None, uriref=None):
        self.name = name
        self.value = uriref

class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass
             
class SimpleConstant(SimpleExpr):
    pass

class URIRef(SimpleConstant):
    """We know a URIRef which identifies the same thing as this
    Constant.  Should we allow many of these, therefor?"""

    def __init__(self, u):
        try:
            self.racine, self.fragment = split(u, "#")
            #print "initialized URIRef to %s, %s" % (self.racine, self.fragment)
        except ValueError:
            self.racine = u; self.fragment = None
        self.value = u

class String(SimpleConstant):

    def __init__(self, u):
        self._u = u

    def value(self):
        return self._u

    
class RDFLiteral(SimpleConstant):

    def __init__(self, text, lang=None, isXML=0):
        pass

import LX.firstOrderLogic

opTable["and"] = LX.firstOrderLogic.AND
# ... or something.

def _test_expr_setup():
    """
    >>> import LX.expr
    >>> print LX.expr._test_expr[1]
    or(and(p, q), pp(a))
    """
    p = Proposition("p")
    q = Proposition("q")
    pp = ConstantPredicate("pp")
    a = Constant("a")
    return {
        1: (p & q | pp(a)),
        }

_test_expr = _test_expr_setup()

def _test():
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()




# $Log$
# Revision 1.2  2002-09-02 20:10:44  sandro
# factored FOL code out of expr.py (and into firstOrderLogic.py), to try to keep it simple enough.  Lost propositions, doctests.
#
# Revision 1.1  2002/08/31 19:43:23  sandro
# a new factoring, combining Term and Formula; not quite ready to replace the others, but passing its unit tests (I just discovered doctest)
#
# Revision 1.4  2002/08/29 21:56:54  sandro
# remove debugging print left in accidentally
#
# Revision 1.3  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 