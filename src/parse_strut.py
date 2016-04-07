#!/usr/bin/env python

import sys

template_header = """\
#include <string>
#include <array>

%s
struct FieldDef
{
  std::string name;
  VarType type;
  unsigned int size;
  unsigned int offset;
};
#define FIELD_DEFINE(c, n, t, s) {#n, t, s, offsetof(c, n)}

"""

class CVar(object):
  def __init__(self, type, name, size=0):
    self.type = type
    self.name = name
    self.size = size

class CStruct(object):
  def __init__(self, name):
    self.name = name
    self.vars = []

class UnknownToken(Exception):
  def __init__(self, token):
    msg = "Unknown token: {0}".format(token)
    self.token = token
    super(UnknownToken, self).__init__(msg)

class VarType(object):
  """Define the C variable type this support"""
  
  Int, Float, Double, Char = range(4)
  def __init__(self):
    super(VarType, self).__init__()

  @staticmethod
  def token_to_type(token):
    table = {"int":VarType.Int, "float":VarType.Float, "double":VarType.Double, "char":VarType.Char}
    if token not in table:
      raise UnknownToken(token)
    return table[token]

  @staticmethod
  def type_to_enum(type):
    table = ["VarType::Int", "VarType::Float", "VarType::Double", "VarType::Char"]
    return table[type]

  @staticmethod
  def get_enum_def():
    table = ["Int", "Float", "Double", "Char"]
    return "enum class VarType { %s };" % (", ".join(table))

class Grammer(object):
  STATE_SCOPE_FILE, STATE_SCOPE_STRUCTURE = range(2)

  def __init__(self, lexers):
    self.parse(lexers)

  def __consume_token(self):
    if self.__is_done():
      raise ValueError('EOL')
    token = self.__tokens[self.__index]
    self.__index += 1
    return token

  def __verify_next_token(self, token):
    next = self.__consume_token()
    if next != token:
      raise UnknownToken(next)

  def __is_done(self):
    return self.__index == len(lexers)

  def __parse_var(self, token):
    var = VarType.token_to_type(token)
    size = 0
    name = self.__consume_token()
    if var == VarType.Char:
      self.__verify_next_token("[")
      size = int(self.__consume_token())
      self.__verify_next_token("]")
    self.__verify_next_token(";")
    return CVar(var, name, size)

  def parse(self, lexers):
    self.__reset_state(lexers)
    structure = None
    while not self.__is_done():
      token = self.__consume_token()
      if self.__state == Grammer.STATE_SCOPE_FILE:
        if token == "struct":
          name = self.__consume_token()
          structure = CStruct(name)
          self.__verify_next_token("{")
          self.__state = Grammer.STATE_SCOPE_STRUCTURE
        else:
          raise UnknownToken(token)
      elif self.__state == Grammer.STATE_SCOPE_STRUCTURE:
        if token == "}":
          self.__verify_next_token(";")
          self.structures.append(structure)
          self.__state = Grammer.STATE_SCOPE_FILE
          structure = None
        else:
          var = self.__parse_var(token)
          structure.vars.append(var)

  def __reset_state(self, lexers):
    self.__state = Grammer.STATE_SCOPE_FILE
    self.__index = 0
    self.__tokens = lexers
    self.structures = []

def lexer(input_file):
  import shlex
  return list(shlex.shlex(open(input_file)))

def output_struct_def(structures, filename):
  with open(filename, "w") as f:
    f.write(template_header % VarType.get_enum_def())
    for s in structures:
      f.write("const std::array<FieldDef, %d> %s_Fields = {{\n" % (len(s.vars), s.name))
      for v in s.vars:
        f.write("\tFIELD_DEFINE(%s, %s, %s, %d),\n" % (s.name, v.name, VarType.type_to_enum(v.type), v.size))
      f.write("}};\n\n")

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "USAGE: {0} src_file fields_file".format(sys.argv[0])
    sys.exit(0)

  lexers = lexer(sys.argv[1])
  gramer = Grammer(lexers)
  output_struct_def(gramer.structures, sys.argv[2])
