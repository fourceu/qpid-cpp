#!/usr/bin/env python

#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http:#www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from xml.dom.minidom import parse, parseString, Node
from cStringIO       import StringIO

#=====================================================================================
#
#=====================================================================================
class SchemaType:
  def __init__ (self, node):
    self.name     = None
    self.base     = None
    self.cpp      = None
    self.encode   = None
    self.decode   = None
    self.style    = "normal"
    self.accessor = None
    self.init     = "0"

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'base':
        self.base = val

      elif key == 'cpp':
        self.cpp = val

      elif key == 'encode':
        self.encode = val

      elif key == 'decode':
        self.decode = val

      elif key == 'style':
        self.style = val

      elif key == 'accessor':
        self.accessor = val

      elif key == 'init':
        self.init = val

      else:
        raise ValueError ("Unknown attribute in type '%s'" % key)

    if self.name == None or self.base == None or self.cpp == None or \
       self.encode == None or self.decode == None:
      raise ValueError ("Missing required attribute(s) in type")

  def getName (self):
    return self.name

  def genAccessor (self, stream, varName, changeFlag = None):
    if self.accessor == "direct":
      stream.write ("    inline void set_" + varName + " (" + self.cpp + " val){\n");
      stream.write ("        " + varName + " = val;\n");
      if self.style == "wm":
        stream.write ("        if (" + varName + "Low  > val)\n")
        stream.write ("            " + varName + "Low  = val;\n");
        stream.write ("        if (" + varName + "High < val)\n")
        stream.write ("            " + varName + "High = val;\n");
      if changeFlag != None:
        stream.write ("        " + changeFlag + " = true;\n")
      stream.write ("    }\n");
    elif self.accessor == "counter":
      stream.write ("    inline void inc_" + varName + " (" + self.cpp + " by = 1){\n");
      stream.write ("        " + varName + " += by;\n")
      if self.style == "wm":
        stream.write ("        if (" + varName + "High < " + varName + ")\n")
        stream.write ("            " + varName + "High = " + varName + ";\n")
      if changeFlag != None:
        stream.write ("        " + changeFlag + " = true;\n")
      stream.write ("    }\n");
      stream.write ("    inline void dec_" + varName + " (" + self.cpp + " by = 1){\n");
      stream.write ("        " + varName + " -= by;\n")
      if self.style == "wm":
        stream.write ("        if (" + varName + "Low > " + varName + ")\n")
        stream.write ("            " + varName + "Low = " + varName + ";\n")
      if changeFlag != None:
        stream.write ("        " + changeFlag + " = true;\n")
      stream.write ("    }\n");

  def genHiLoStatResets (self, stream, varName):
    if self.style == "wm":
      stream.write ("    " + varName + "High = " + varName + ";\n")
      stream.write ("    " + varName + "Low  = " + varName + ";\n")

  def genWrite (self, stream, varName):
    stream.write ("    " + self.encode.replace ("@", "buf").replace ("#", varName) + ";\n")
    if self.style == "wm":
      stream.write ("    " + self.encode.replace ("@", "buf") \
                    .replace ("#", varName + "High") + ";\n")
      stream.write ("    " + self.encode.replace ("@", "buf") \
                    .replace ("#", varName + "Low") + ";\n")

  def getReadCode (self, varName, bufName):
    result = self.decode.replace ("@", bufName).replace ("#", varName)
    return result

  def getWriteCode (self, varName, bufName):
    result = self.encode.replace ("@", bufName).replace ("#", varName)
    return result

#=====================================================================================
#
#=====================================================================================
class TypeSpec:
  def __init__ (self, file):
    self.types = {}
    dom = parse (file)
    document = dom.documentElement
    if document.tagName != 'schema-types':
      raise ValueError ("Expected 'schema-types' in type file")

    for child in document.childNodes:
      if child.nodeType == Node.ELEMENT_NODE:
        if child.nodeName == 'type':
          stype = SchemaType (child)
          self.types[stype.getName ()] = stype
        else:
          raise ValueError ("Unknown type tag '%s'" % child.nodeName)

  def getType (self, name):
    return self.types[name]


#=====================================================================================
#
#=====================================================================================
class Type:
  def __init__ (self, name, typespec):
    self.type = typespec.getType (name)

#=====================================================================================
#
#=====================================================================================
class SchemaConfig:
  def __init__ (self, node, typespec):
    self.name        = None
    self.type        = None
    self.access      = "RO"
    self.isIndex     = 0
    self.isParentRef = 0
    self.unit        = None
    self.min         = None
    self.max         = None
    self.maxLen      = None
    self.desc        = None

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'type':
        self.type = Type (val, typespec)
        
      elif key == 'access':
        self.access = val
        
      elif key == 'index':
        if val != 'y':
          raise ValueError ("Expected 'y' in index attribute")
        self.isIndex = 1
        
      elif key == 'parentRef':
        if val != 'y':
          raise ValueError ("Expected 'y' in parentRef attribute")
        self.isParentRef = 1
        
      elif key == 'unit':
        self.unit = val
        
      elif key == 'min':
        self.min = val
        
      elif key == 'max':
        self.max = val
        
      elif key == 'maxlen':
        self.maxLen = val
        
      elif key == 'desc':
        self.desc = val
        
      else:
        raise ValueError ("Unknown attribute in configElement '%s'" % key)

    if self.name == None:
      raise ValueError ("Missing 'name' attribute in configElement")
    if self.type == None:
      raise ValueError ("Missing 'type' attribute in configElement")

  def getName (self):
    return self.name

  def isConstructorArg (self):
    if self.access == "RC" and self.isParentRef == 0:
      return 1
    return 0

  def genDeclaration (self, stream):
    stream.write ("    " + self.type.type.cpp + " " + self.name + ";\n")

  def genFormalParam (self, stream):
    stream.write (self.type.type.cpp + " _" + self.name)

  def genAccessor (self, stream):
    self.type.type.genAccessor (stream, self.name, "configChanged")

  def genSchema (self, stream):
    stream.write ("    ft = FieldTable ();\n")
    stream.write ("    ft.setString (NAME,   \"" + self.name + "\");\n")
    stream.write ("    ft.setInt    (TYPE,   TYPE_" + self.type.type.base +");\n")
    stream.write ("    ft.setInt    (ACCESS, ACCESS_" + self.access + ");\n")
    stream.write ("    ft.setInt    (INDEX,  " + str (self.isIndex) + ");\n")
    if self.unit != None:
      stream.write ("    ft.setString (UNIT,   \"" + self.unit   + "\");\n")
    if self.min != None:
      stream.write ("    ft.setInt    (MIN,    " + self.min    + ");\n")
    if self.max != None:
      stream.write ("    ft.setInt    (MAX,    " + self.max    + ");\n")
    if self.maxLen != None:
      stream.write ("    ft.setInt    (MAXLEN, " + self.maxLen + ");\n")
    if self.desc != None:
      stream.write ("    ft.setString (DESC,   \"" + self.desc   + "\");\n")
    stream.write ("    buf.put (ft);\n\n")

  def genWrite (self, stream):
    self.type.type.genWrite (stream, self.name)


#=====================================================================================
#
#=====================================================================================
class SchemaInst:
  def __init__ (self, node, typespec):
    self.name = None
    self.type = None
    self.unit = None
    self.desc = None

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'type':
        self.type = Type (val, typespec)
        
      elif key == 'unit':
        self.unit = val
        
      elif key == 'desc':
        self.desc = val
        
      else:
        raise ValueError ("Unknown attribute in instElement '%s'" % key)

    if self.name == None:
      raise ValueError ("Missing 'name' attribute in instElement")
    if self.type == None:
      raise ValueError ("Missing 'type' attribute in instElement")

  def getName (self):
    return self.name

  def genDeclaration (self, stream):
    stream.write ("    " + self.type.type.cpp + "  " + self.name + ";\n")
    if self.type.type.style == 'wm':
      stream.write ("    " + self.type.type.cpp + "  " + self.name + "High;\n")
      stream.write ("    " + self.type.type.cpp + "  " + self.name + "Low;\n")

  def genAccessor (self, stream):
    self.type.type.genAccessor (stream, self.name, "instChanged")

  def genHiLoStatResets (self, stream):
    self.type.type.genHiLoStatResets (stream, self.name)

  def genSchemaText (self, stream, name, desc):
    stream.write ("    ft = FieldTable ();\n")
    stream.write ("    ft.setString (NAME,   \"" + name + "\");\n")
    stream.write ("    ft.setInt    (TYPE,   TYPE_" + self.type.type.base +");\n")
    if self.unit != None:
      stream.write ("    ft.setString (UNIT,   \"" + self.unit   + "\");\n")
    if desc != None:
      stream.write ("    ft.setString (DESC,   \"" + desc   + "\");\n")
    stream.write ("    buf.put (ft);\n\n")

  def genSchema (self, stream):
    self.genSchemaText (stream, self.name, self.desc)
    if self.type.type.style == "wm":
      descHigh = self.desc
      descLow  = self.desc
      if self.desc != None:
        descHigh = descHigh + " (High)"
        descLow  = descLow  + " (Low)"
      self.genSchemaText (stream, self.name + "High", descHigh)
      self.genSchemaText (stream, self.name + "Low",  descLow)

  def genWrite (self, stream):
    self.type.type.genWrite (stream, self.name)

  def genInitialize (self, stream):
    val = self.type.type.init
    stream.write ("    " + self.name + " = " + val + ";\n")
    if self.type.type.style == "wm":
      stream.write ("    " + self.name + "High = " + val + ";\n")
      stream.write ("    " + self.name + "Low  = " + val + ";\n")


#=====================================================================================
#
#=====================================================================================
class SchemaArg:
  def __init__ (self, node, typespec):
    self.name    = None
    self.type    = None
    self.unit    = None
    self.dir     = "I"
    self.min     = None
    self.max     = None
    self.maxLen  = None
    self.desc    = None
    self.default = None

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'type':
        self.type = Type (val, typespec)
        
      elif key == 'unit':
        self.unit = val

      elif key == 'dir':
        self.dir = val.upper ()
        
      elif key == 'min':
        self.min = val
        
      elif key == 'max':
        self.max = val
        
      elif key == 'maxlen':
        self.maxLen = val
        
      elif key == 'desc':
        self.desc = val

      elif key == 'default':
        self.default = val
        
      else:
        raise ValueError ("Unknown attribute in arg '%s'" % key)

    if self.name == None:
      raise ValueError ("Missing 'name' attribute in arg")
    if self.type == None:
      raise ValueError ("Missing 'type' attribute in arg")

  def getName (self):
    return self.name

  def getDir (self):
    return self.dir

  def genSchema (self, stream):
    stream.write ("    ft = FieldTable ();\n")
    stream.write ("    ft.setString (NAME,    \"" + self.name + "\");\n")
    stream.write ("    ft.setInt    (TYPE,    TYPE_" + self.type.type.base +");\n")
    stream.write ("    ft.setString (DIR,     \"" + self.dir + "\");\n")
    if self.unit != None:
      stream.write ("    ft.setString (UNIT,    \"" + self.unit   + "\");\n")
    if self.min != None:
      stream.write ("    ft.setInt    (MIN,     " + self.min    + ");\n")
    if self.max != None:
      stream.write ("    ft.setInt    (MAX,     " + self.max    + ");\n")
    if self.maxLen != None:
      stream.write ("    ft.setInt    (MAXLEN,  " + self.maxLen + ");\n")
    if self.desc != None:
      stream.write ("    ft.setString (DESC,    \"" + self.desc + "\");\n")
    if self.default != None:
      stream.write ("    ft.setString (DEFAULT, \"" + self.default + "\");\n")
    stream.write ("    buf.put (ft);\n\n")

#=====================================================================================
#
#=====================================================================================
class SchemaMethod:
  def __init__ (self, parent, node, typespec):
    self.parent = parent
    self.name   = None
    self.desc   = None
    self.args   = []

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'desc':
        self.desc = val

      else:
        raise ValueError ("Unknown attribute in method '%s'" % key)

    for child in node.childNodes:
      if child.nodeType == Node.ELEMENT_NODE:
        if child.nodeName == 'arg':
          arg = SchemaArg (child, typespec)
          self.args.append (arg)
        else:
          raise ValueError ("Unknown method tag '%s'" % child.nodeName)

  def getName (self):
    return self.name

  def getFullName (self):
    return self.parent.getName().capitalize() + self.name[0:1].upper() +\
           self.name[1:]

  def getArgCount (self):
    return len (self.args)

  #===================================================================================
  # Code Generation Functions.  The names of these functions (minus the leading "gen")
  # match the substitution keywords in the template files.
  #===================================================================================
  def genNameUpper (self, stream, variables):
    stream.write (self.getFullName ().upper ())

  def genNameCamel (self, stream, variables):
    stream.write (self.getFullName ())

  def genArguments (self, stream, variables):
    for arg in self.args:
      ctype  = arg.type.type.cpp
      dirTag = arg.dir.lower() + "_"
      stream.write ("    " + ctype + " " + dirTag + arg.getName () + ";\n")

  def genSchema (self, stream, variables):
    stream.write ("    ft = FieldTable ();\n")
    stream.write ("    ft.setString (NAME,     \"" + self.name + "\");\n")
    stream.write ("    ft.setInt    (ARGCOUNT, " + str (len (self.args)) + ");\n")
    if self.desc != None:
      stream.write ("    ft.setString (DESC,     \"" + self.desc + "\");\n")
    stream.write ("    buf.put (ft);\n\n")
    for arg in self.args:
      arg.genSchema (stream)

#=====================================================================================
#
#=====================================================================================
class SchemaEvent:
  def __init__ (self, parent, node, typespec):
    self.parent = parent
    self.name   = None
    self.desc   = None
    self.args   = []

    attrs = node.attributes
    for idx in range (attrs.length):
      key = attrs.item(idx).nodeName
      val = attrs.item(idx).nodeValue
      if   key == 'name':
        self.name = val

      elif key == 'desc':
        self.desc = val

      else:
        raise ValueError ("Unknown attribute in event '%s'" % key)

    for child in node.childNodes:
      if child.nodeType == Node.ELEMENT_NODE:
        if child.nodeName == 'arg':
          arg = SchemaArg (child, typespec)
          self.args.append (arg)
        else:
          raise ValueError ("Unknown event tag '%s'" % child.nodeName)

  def getName (self):
    return self.name

  def getFullName (self):
    return self.parent.getName ().capitalize() + self.name.capitalize ()

  def getArgCount (self):
    return len (self.args)

#=====================================================================================
#
#=====================================================================================
class SchemaClass:
  def __init__ (self, node, typespec):
    self.configElements = []
    self.instElements   = []
    self.methods        = []
    self.events         = []

    attrs = node.attributes
    self.name = attrs['name'].nodeValue

    children = node.childNodes
    for child in children:
      if child.nodeType == Node.ELEMENT_NODE:
        if   child.nodeName == 'configElement':
          sub = SchemaConfig (child, typespec)
          self.configElements.append (sub)

        elif child.nodeName == 'instElement':
          sub = SchemaInst (child, typespec)
          self.instElements.append (sub)

        elif child.nodeName == 'method':
          sub = SchemaMethod (self, child, typespec)
          self.methods.append (sub)

        elif child.nodeName == 'event':
          sub = SchemaEvent (self, child, typespec)
          self.events.append (sub)

        else:
          raise ValueError ("Unknown class tag '%s'" % child.nodeName)

  def getName (self):
    return self.name

  def getMethods (self):
    return self.methods

  def getEvents (self):
    return self.events

  #===================================================================================
  # Code Generation Functions.  The names of these functions (minus the leading "gen")
  # match the substitution keywords in the template files.
  #===================================================================================
  def genAccessorMethods (self, stream, variables):
    for config in self.configElements:
      if config.access != "RC":
        config.genAccessor (stream)
    for inst in self.instElements:
      inst.genAccessor (stream)

  def genConfigCount (self, stream, variables):
    stream.write ("%d" % len (self.configElements))

  def genConfigDeclarations (self, stream, variables):
    for element in self.configElements:
      element.genDeclaration (stream)

  def genConfigElementSchema (self, stream, variables):
    for config in self.configElements:
      config.genSchema (stream)

  def genConstructorArgs (self, stream, variables):
    # Constructor args are config elements with read-create access
    result = ""
    first  = 1
    for element in self.configElements:
      if element.isConstructorArg ():
        if first == 1:
          first = 0
        else:
          stream.write (", ")
        element.genFormalParam (stream)

  def genConstructorInits (self, stream, variables):
    for element in self.configElements:
      if element.isConstructorArg ():
        stream.write ("," + element.getName () + "(_" + element.getName () + ")")

  def genDoMethodArgs (self, stream, variables):
    methodCount = 0
    inArgCount  = 0
    for method in self.methods:
      methodCount = methodCount + 1
      for arg in method.args:
        if arg.getDir () == "I" or arg.getDir () == "IO":
          inArgCount = inArgCount + 1

    if methodCount == 0:
      stream.write ("string, Buffer&, Buffer& outBuf")
    else:
      if inArgCount == 0:
        stream.write ("string methodName, Buffer&, Buffer& outBuf")
      else:
        stream.write ("string methodName, Buffer& inBuf, Buffer& outBuf")

  def genEventCount (self, stream, variables):
    stream.write ("%d" % len (self.events))

  def genEventSchema (self, stream, variables):
    pass ###########################################################################

  def genHiLoStatResets (self, stream, variables):
    for inst in self.instElements:
      inst.genHiLoStatResets (stream)

  def genInitializeElements (self, stream, variables):
    for inst in self.instElements:
      inst.genInitialize (stream)

  def genInstChangedStub (self, stream, variables):
    if len (self.instElements) == 0:
      stream.write ("    // Stub for getInstChanged.  There are no inst elements\n")
      stream.write ("    bool getInstChanged (void) { return false; }\n")

  def genInstCount (self, stream, variables):
    count = 0
    for inst in self.instElements:
      count = count + 1
      if inst.type.type.style == "wm":
        count = count + 2
    stream.write ("%d" % count)

  def genInstDeclarations (self, stream, variables):
    for element in self.instElements:
      element.genDeclaration (stream)

  def genInstElementSchema (self, stream, variables):
    for inst in self.instElements:
      inst.genSchema (stream)

  def genMethodArgIncludes (self, stream, variables):
    for method in self.methods:
      if method.getArgCount () > 0:
        stream.write ("#include \"qpid/management/Args" +\
                      method.getFullName () + ".h\"\n")

  def genMethodCount (self, stream, variables):
    stream.write ("%d" % len (self.methods))

  def genMethodHandlers (self, stream, variables):
    for method in self.methods:
      stream.write ("\n    if (methodName == \"" + method.getName () + "\")\n    {\n")
      if method.getArgCount () == 0:
        stream.write ("        ArgsNone ioArgs;\n")
      else:
        stream.write ("        Args" + method.getFullName () + " ioArgs;\n")
      for arg in method.args:
        if arg.getDir () == "I" or arg.getDir () == "IO":
          stream.write ("        " +\
                        arg.type.type.getReadCode ("ioArgs." +\
                                                   arg.dir.lower () + "_" +\
                                                   arg.name, "inBuf") + ";\n")

      stream.write ("        status = coreObject->ManagementMethod (METHOD_" +\
                    method.getName().upper() + ", ioArgs);\n")
      stream.write ("        outBuf.putLong        (status);\n")
      stream.write ("        outBuf.putShortString (Manageable::StatusText (status));\n")
      for arg in method.args:
        if arg.getDir () == "O" or arg.getDir () == "IO":
          stream.write ("        " +\
                        arg.type.type.getWriteCode ("ioArgs." +\
                                                    arg.dir.lower () + "_" +\
                                                    arg.name, "outBuf") + ";\n")
      stream.write ("        return;\n    }\n")


  def genMethodIdDeclarations (self, stream, variables):
    number = 1
    for method in self.methods:
      stream.write ("    static const uint32_t METHOD_" + method.getName().upper() +\
                    " = %d;\n" % number)
      number = number + 1

  def genMethodSchema (self, stream, variables):
    for method in self.methods:
      method.genSchema (stream, variables)

  def genNameCap (self, stream, variables):
    stream.write (self.name.capitalize ())

  def genNameLower (self, stream, variables):
    stream.write (self.name.lower ())

  def genNameUpper (self, stream, variables):
    stream.write (self.name.upper ())

  def genParentArg (self, stream, variables):
    for config in self.configElements:
      if config.isParentRef == 1:
        stream.write (" _parent")
        return

  def genParentRefAssignment (self, stream, variables):
    for config in self.configElements:
      if config.isParentRef == 1:
        stream.write (config.getName () + \
                      " = _parent->GetManagementObject ()->getObjectId ();")
        return

  def genWriteConfig (self, stream, variables):
    for config in self.configElements:
      config.genWrite (stream);

  def genWriteInst (self, stream, variables):
    for inst in self.instElements:
      inst.genWrite (stream);


#=====================================================================================
#
#=====================================================================================
class PackageSchema:
  def __init__ (self, typefile, schemafile):

    self.classes  = []
    self.typespec = TypeSpec (typefile)

    dom = parse (schemafile)
    document = dom.documentElement
    if document.tagName != 'schema':
      raise ValueError ("Expected 'schema' node")
    attrs = document.attributes
    self.packageName = attrs['package'].nodeValue

    children = document.childNodes
    for child in children:
      if child.nodeType == Node.ELEMENT_NODE:
        if child.nodeName == 'class':
          cls = SchemaClass (child, self.typespec)
          self.classes.append (cls)
        else:
          raise ValueError ("Unknown schema tag '%s'" % child.nodeName)

  def getPackageName (self):
    return self.packageName

  def getClasses (self):
    return self.classes
