#!/usr/bin/python
#       Convert Fink (Debian Packaging system) data to RDF
# 
# See http://fink.sourceforge.net/doc/packaging/reference.php
#   and http://fink.sourceforge.net/doc/packaging/format.php#format
# See http://www.w3.org/DesignIssues/Notation3.html
#
# To run:
#        The notation3.py files must be in your PYTHONPATH (or installed)
# TODO:
#       - Recursive Splitoffs convert nicely to N3. Remember parent,  fink:child relation
#       - Version number qualifiers on dependecies   [fink:thisOrSuccesso xxx]
#
import sys
import string
import os
import re

PREFIX="/sw"

version = "$Id$"[1:-1]
macros = { "N": "_parent", "n":"Package",  "v":"Version", "r": "Revision",
            "p": "_prefix", "P": "_prefix"}

comment = re.compile(r'^(.*?)#.*$')
header = re.compile(r'^\s*([-A-Za-z0-9]*):\s*(.*)\s*$')
contact = re.compile(r'([-A-Za-z0-9]+) +([-A-Za-z0-9-]+) *<([-_A-Za-z0-9@\.+]*)>')
contact2 = re.compile(r'None *<([-_A-Za-z0-9@\.+]*)>')
contact3 = re.compile(r'^.*(.*?) *<([-_A-Za-z0-9@\.+]*)>')  # @@@@@@@ I18n
qualified = re.compile(r'(.*)(\(.*\)) *')
terminator = re.compile(r'^ *<< *$')   # must be on a line all by itself, save whitespace
blank = re.compile(r'[ \t]*')
commaEnd = re.compile(r'.*, *$')

from swap import  notation3  # http://www.w3.org/2000/10/swap

def ss(str):
    """Format string for output"""
    return notation3.stringToN3(str)

def makeId(str):
    res = ""
    for c in str.strip():
        x = string.find("-.", c)
        if x <0:
            res=res+c
        else:
            res=res+"_" # @@ loose info
    return res

def expand(str, dict):
    str = str.strip()
    while 1:
        x = str.find("%")
        if x < 0: break
        c = str[x+1]
        try:
            str = str[:x] + dict[macros[c]].strip() + str[x+2:]
        except KeyError:
            print "@@@@@ dict is", dict
            print "@@@@@ macros are", macros
            raise RuntimeError("Macros fails with"+str[x+1]+`dict`)
#    print "#@@ expanded to", str
    return str

def makePackageList(str, dict):
    """Strip spaces and expand %N %v %r macros in module name"""
    if str.find("|")>=0:
        res = "["
        while 1:
            x = str.find("|")
            if x<0 : break
            res = res + "fink:option %s; " % makePackageList(str[:x], dict)
            str = str [x+1:]
        return res + "fink:option %s]" % makePackageList(str, dict)

    str = str.strip()
    m = qualified.match(str)
    if m:
        str = m.group(1)   # strip off qualifications @@@@@@@@ losing info here

    if str.find("(") >=0:
        raise RuntimeError("Qualifier stripping failed for '%s'\nwith m=%s"%(str,m))
    str = expand(str,dict)

    while 1:
        x = str.find("-")
        if x<0:break
        str = str[:x] + "_" + str[x+1:]
    while 1:
        x = str.find("+")
        if x<0:break
        str = str[:x] + "_plus" + str[x+1:]
    return "pkg:"+str[0].lower()+str[1:]
    
def prefixes():
    print "# http://www.w3.org/DesignIssues/Notation3"
    print "# Generated by  ", version
    print
    print "@prefix fink: <http://www.w3.org/2000/10/swap/util/fink#>."
    print "@prefix con: <http://www.w3.org/2000/10/swap/pim/contact#>."
    print "@prefix pkg:  <http://www.w3.org/2000/10/swap/util/fink-pkg#>."   # package names
    print "@prefix lic:  <http://www.w3.org/2000/10/swap/util/fink-lic#>."   # licenses
    print


def convert(path):
    print "# Start of info from", path
    input = open(path, "r")
    buf = input.read()  # Read the file
    input.close()
    print "# End of info from", path
    return convertString(buf, path)
    
def convertString(buf, path, nested=0, i=0, parent=None):
    """Convert Fink info format to n3"""
    global nochange
    global verbose
    current = { "_prefix": PREFIX}
    if parent: current["_parent"] = parent
    currentPackage = None
    dict = {}

    result = []   # list of property, value pairs

    while 1:
        j = buf.find("\n", i)
        if j <0: break
        e = j
        if e>i and buf[e-1]=='\r':
            e = e-1
        line = buf[i:e]
        i = j+1

        k = line.find("#") # Chop comments
        if k >= 0:
            comment = line[k:]
            line = line[:k]
        else:
            comment = ""

        if nested and terminator.match(line):
            return i, currentPackage

        m = header.match(line)
        if m:
            head = m.group(1)
            property = m.group(1)
            property = "fink:" + property[0].lower()+property[1:]
            value = m.group(2)
            multiline = 0
            if value == "<<":
                if head[:8].lower() == "splitoff":
                    # print "."
                    print "# SplitOff level:", nested+1, "from", current["Package"]
                    i, child = convertString(buf, path, nested=nested+1, i=i, parent=current["Package"])
                    result.append("# .  %s fink:child %s;\n" % (currentPackage, child))
                    continue

                j = buf.find("<<", i)  # Not always at beginning of line. Sometimes no following \n
                if j<0: raise RuntimeError("In "+path+", no trailing delimiter to multiline value: "+buf[i:])
                value = buf[i:j]
                i = j+3  # skip <<\n
                multiline = 1

#               print "    " + property + " " + ss(value) +';'
#               continue

            # RFC822-style line wrap
            else:
                while commaEnd.match(line) and buf[i:i+1] !="" and buf[i:i+1] in " \t":
                    j = buf.find("\n", i)
                    if j <0: break
                    e = j
                    if e>i and buf[e-1]=='\r':
                        e = e-1
                    line2 = buf[i:e]
                    i = j+1
            
                    k = line2.find("#") # Chop comments
                    if k >= 0:
                        comment = comment + line2[k:]
                        line2 = line2[:k]
                    line = line + " " + line2
                    value = value + " " + line2.strip()

            current[head] = value    # track things like package, version, revision

            if head == "Package":
                if currentPackage:
                    raise RuntimeError("Seem to already be in package"+currentPackage)
                    print ". # End of ", currentPackage
                currentPackage = makePackageList(value,current)
                if not parent:
                    current["_parent"] = value  # for macro expansion
                continue

            if head == "Version":
                versionId = currentPackage + "_v" + makeId(value)
                continue

            if head == "Revision":
                revisionId = versionId + "_r" + makeId(value)
                continue

            if head in [ "Depends", "BuildDepends", "Recommends", "Conflicts", "Replaces"]:
                modules = string.split(value, ",")
                if modules[0].strip() == "": continue
                result.append( "    "+property+" "+makePackageList(modules[0], current))
                for mod in modules[1:]:
                    result.append( ", "+makePackageList(mod, current))
                result.append( ";")
                continue

            if head == "Maintainer":
                m = contact.match(value)
                if m != None:
                    result.append( """     %s [con:firstName %s; con:lastName %s; con:mailbox <mailto:%s>];\n"""%(
                        property, ss(m.group(1)), ss(m.group(2)), m.group(3)))
                    continue
                m = contact2.match(value)
                if m != None:
                    result.append( """     %s [con:mailbox <mailto:%s>];\n"""%(
                            property, m.group(1)))
                    continue
                m = contact3.match(value)
                if m != None:
                    result.append( """     %s [con:name "%s"; con:mailbox <mailto:%s>];\n"""%(
                            property, m.group(1), m.group(2)))
                    continue
                result.append( """     %s [con:name %s];\n"""% (property, ss(value)))
                continue

            result.append( "    " + property + " "+ss(value) + ';\n')
            continue

        m = blank.match(line)
        if m:
            result.append(comment+"\n")
            continue
        print "#@@", line, comment
        raise RuntimeError("Unknown line format:"+line)

# Now output the identifiers first:
    h= """%s  fink:packageName "%s";\n""" % (currentPackage, current["Package"])
    if parent:
        h=h+( "    is fink:child of %s;\n" % makePackageList(parent, current))
    h=h+( "        fink:specificVersion %s .\n" % versionId)
    h=h+( "%s fink:version %s;" %(versionId, ss(current["Version"]))) 
    h=h+( "        fink:specificRevision %s .\n" % revisionId)
    h=h+( "%s fink:revision %s;\n" %(revisionId, ss(value)))
    h=h+( "    fink:infoFrom <%s>; " % path)


    print h
    for i in result: print i,
    print ". # End of package ", currentPackage
    print

def do(path, explicit=1):
    """Convert file of tree of files.
    
    Path can be directory.  If explicitly named, files are done anyway"""
    global doall
    global recursive
    global verbose

    if verbose: sys.stderr.write("fink2n3: converting " + path + "\n")
    if os.path.isdir(path) and (path[:7] != "binary-" or doall):
        if recursive:
            for name in os.listdir(path):
                do(path + "/" + name, explicit=0)
    else:
        if doall or explicit or path[-5:] == ".info":
            convert(path)
        else:
            if verbose:
                sys.stderr.write("de-cr: skipping "+path+"\n")
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
        elif arg == "-a": doall=1
        elif arg == "-v": verbose=1
        elif arg == "-?" or arg == "-h" or arg == "--help":
            print """Convert Fink .info format  to n3 format.

Syntax:    python fink2n3.py  [-r] <file>

    where <file> can be omitted and if so defaults to /sw/fink/dists .
    This program was http://www.w3.org/2000/10/swap/util/fink2p3.py
    $Id$
"""
        else:
            print """Bad option argument.""", arg, ". use -? for help."
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "/sw/fink/dists" ] # Default

prefixes()
for path in files:
    do(path)
print "# ends"

# ends
