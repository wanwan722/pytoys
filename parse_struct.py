#!/usr/bin/env python

import sys
from shlex import *

def lexer(input_file):
  return list(shlex(open(input_file)))

VAR_TYPE_INT, VAR_TYPE_DOUBLE, VAR_TYPE_CHAR = range(3)

class UnknownToken(Exception):
  def __init__(self, token):
    msg = "Unknown token: {0}".format(token)
    self.token = token
    super(UnknownToken, self).__init__(msg)

class Variable(object):
  def __init__(self, type, name, size=0):
    self.type = type
    self.name = name
    self.size = size

class Structure(object):
  def __init__(self, name):
    self.name = name
    self.vars = []

class Grammer(object):
  STATE_SCOPE_FILE, STATE_SCOPE_STRUCTURE = range(2)

  def __init__(self, lexers):
    self.parse(lexers)

  def __consume_token(self):
    if self.__is_done():
      raise ValueError('EOL')
    token = self.__tokens[self.__index]
    #print "Token: {0}".format(token)
    self.__index += 1
    return token

  def __verify_next_token(self, token):
    next = self.__consume_token()
    if next != token:
      raise UnknownToken(next)

  def __is_done(self):
    return self.__index == len(lexers) - 1

  def __token2var(self, token):
    table = {"int":(VAR_TYPE_INT, 8), "double":(VAR_TYPE_DOUBLE, 8), "char":(VAR_TYPE_CHAR, 0)}
    if token not in table:
      raise UnknownToken(token)
    return table[token]

  def __parse_var(self, token):
    var, size = self.__token2var(token)
    name = self.__consume_token()
    if var == VAR_TYPE_CHAR:
      self.__verify_next_token("[")
      size = int(self.__consume_token())
      self.__verify_next_token("]")
    self.__verify_next_token(";")
    return Variable(var, name, size)

  def parse(self, lexers):
    self.__reset_state(lexers)
    structure = None
    while not self.__is_done():
      token = self.__consume_token()
      if self.__state == Grammer.STATE_SCOPE_FILE:
        if token == "struct":
          name = self.__consume_token()
          structure = Structure(name)
          self.__verify_next_token("{")
          self.__state = Grammer.STATE_SCOPE_STRUCTURE
        else:
          raise UnknownToken(token)
      elif self.__state == Grammer.STATE_SCOPE_STRUCTURE:
        if token == "}":
          self.structures.append(structure)
          self.__state = Grammer.STATE_SCOPE_FILE
          structure = None
        else:
          structure.vars.append(self.__parse_var(token))

  def __reset_state(self, lexers):
    self.__state = Grammer.STATE_SCOPE_FILE
    self.__index = 0
    self.__tokens = lexers
    self.structures = []

def output_struct_def(structures, filename):
  def __to_type(type):
    table = {VAR_TYPE_INT:"VarType::Int", VAR_TYPE_DOUBLE:"VarType::Double", VAR_TYPE_CHAR:"VarType::Char"}
    return table[type]

  with open(filename, "w") as f:
    f.write("""\
#include <string>
#include <array>

enum class VarType { Int, Double, Char };
struct FieldDef
{
  std::string name;
  VarType type;
  unsigned int size;
  unsigned int offset;
};
#define FIELD_DEFINE(c, n, t, s) {#n, t, s, offsetof(c, n)}

""")

    for s in structures:
      f.write("const std::array<FieldDef, {1}> {0}_Fields = {{{{\n".format(s.name, len(s.vars)))
      for v in s.vars:
        f.write("\tFIELD_DEFINE({0}, {1}, {2}, {3}),\n".format(s.name, v.name, __to_type(v.type), v.size))
      f.write("}};\n")

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "USAGE: {0} src_file fields_file".format(sys.argv[0])
    sys.exit(0)

  try:
    lexers = lexer(sys.argv[1])
    gramer = Grammer(lexers)
    output_struct_def(gramer.structures, sys.argv[2])
  except Exception as e:
    print e
