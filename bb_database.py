from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import sys
import json
from typing import *
from enum import Enum
from bb_config import *

if sys.version_info.minor < 11:
	class StrEnum(str, Enum):
		def __str__(self):
			return self.value
else:
	from enum import StrEnum

class OrderEnum(StrEnum):
	DESC = "DESC"
	ASC = "ASC"

# VALUES
class Value:
	value: any

	def __init__(self, value):
		self.value = value
	
class ValueTableName(Value):
	value: str
	name: str

	def __init__(self, value, name = None):
		self.name = name
		self.value = value

	def __str__(self):
		if self.name:
			return f"{self.value} {self.name}"
		else:
			return self.value

class ValueColumnName(Value):
	value: str
	table: ValueTableName

	def __init__(self, value, table = None):
		self.table = table
		self.value = value
		
	def __str__(self):
		if self.table:
			return f"{self.table}.{self.value}"
		else:
			return self.value

class ValueConstant(Value):
	value: any

	def __str__(self):
		if type(self.value) is str:
			return "'" + str(self.value) + "'"
		else:
			return str(self.value)
	
class Function(Value):
	name: str

	def __init__(self, name, value):
		self.name  = name
		self.value = value

	def __str__(self):
		return self.name + "(" + str(self.value) + ")"

# CONDITIONS
class Condition:
	col: ValueColumnName
	op: str

	def __init__(self, col):
		self.col = col
	
class Condition2OP(Condition):
	val: Union[ValueColumnName, ValueConstant]

	def __init__(self, col, val):
		super().__init__(col)
		self.val = val
	
	def __str__(self):
		return str(self.col) + " " + str(self.op) + " " + str(self.val)

class ConditionEQ(Condition2OP): # =
	op = '='
class ConditionGT(Condition2OP): # >
	op = '>'
class ConditionLT(Condition2OP): # <
	op = '<'
class ConditionGE(Condition2OP): # >=
	op = '>='
class ConditionLE(Condition2OP): # <=
	op = '<='
class ConditionNE(Condition2OP): # !=
	op = '!='
	
class ConditionBETWEEN(Condition): # !=
	op = 'BETWEEN'
	upper: int
	lower: int

	def __init__(self, col, lower, upper):
		super().__init__(col)
		self.lower = lower
		self.upper = upper

	def __str__(self):
		return str(self.col) + " BETWEEN " + \
			   str(self.lower) + " AND " + \
			   str(self.upper)
	
class ConditionLIKE(Condition):
	op = 'LIKE'
	pattern: ValueConstant

	def __init__(self, col, pattern):
		super().__init__(col)
		self.pattern = pattern

	def __str__(self):
		return str(self.col) + " LIKE " + str(self.pattern)
	
class ConditionIN(Condition):
	op = 'IN'
	vals: Set[ValueConstant]
	
	def __init__(self, col, vals):
		super().__init__(col)
		self.vals = vals
		
	def __str__(self):
		return str(self.col) + \
			   " IN ('" + \
			   "','".join({str(val) for val in self.vals}) + \
			   "')"

class ConditionFunction2OP(Condition2OP):
	
	def __init__(self, op, col, val):
		super().__init__(col, val)
		self.op = op
	
# CLAUSES
class Clause:
	name: str
	
	def __strrep__(self):
		raise TypeError(self.name + " may only appear once")
		
	def tostring(self, repeating: bool):
		if repeating:
			return self.__strrep__()
		else:
			return self.__str__()

class ClauseFrom(Clause):
	name = 'FROM'
	table: ValueTableName

	def __init__(self, table):
		self.table = table

	def __str__(self):
		return "FROM " + str(self.table)

class ClauseWhere(Clause):
	name = 'WHERE'
	cond: Condition

	def __init__(self, cond):
		self.cond = cond
	
	def __strrep__(self):
		return "AND " + str(self.cond)

	def __str__(self):
		return "WHERE " + str(self.cond)

class ClauseJoin(Clause):
	name = 'JOIN'
	table: ValueTableName
	cond: Condition

	def __init__(self, table, cond):
		self.table = table
		self.cond = cond
	
	def __strrep__(self):
		return str(self)

	def __str__(self):
		return "JOIN " + str(self.table) + \
			   " ON "  + str(self.cond)
	
class ClauseOrder(Clause):
	name = 'ORDER BY'
	cols: Dict[ValueColumnName, OrderEnum]

	def __init__(self, cols):
		self.cols = cols
	
	def cols_to_str(self):
		return ", ".join(
				list(map(
					lambda t : str(t[0]) + " " + str(t[1]),
					self.cols.items()
				))
			)

	def __strrep__(self):
		return ", " + self.cols_to_str()

	def __str__(self):
		return "ORDER BY " + self.cols_to_str()
	
class ClauseLimit(Clause):
	name = 'LIMIT'
	limit: int

	def __init__(self, limit):
		self.limit = limit
	
	def __str__(self):
		return "LIMIT " + str(self.limit)
	
class ClauseOffset(Clause):
	name = 'OFFSET'
	offset: int

	def __init__(self, offset):
		self.offset = offset
	
	def __str__(self):
		return "OFFSET " + str(self.offset)

# STATEMENTS
class Statement:
	name:	str

class StatementSelect(Statement):
	name = 'SELECT'
	clauses: Set[Clause]
	columns: Set[ValueColumnName]
	distinct: bool

	def __init__(self, columns, clauses, distinct = False):
		self.clauses = clauses
		self.columns = columns
		self.distinct = distinct
	
	def __str__(self):
		s = "SELECT " + \
			("DISTINCT " if self.distinct else "") + \
			','.join(list(map(str, self.columns))) + " "
		
		order = [
			'FROM',
			'JOIN',
			'WHERE',
			'ORDER BY',
			'LIMIT',
			'OFFSET'
		]

		for q in order:
			clauses = list(c for c in self.clauses if c.name == q)
			for i in range(len(clauses)):
				s = s + clauses[i].tostring(i > 0) + " "
				print("\033[34m", i, q, ";", s, "\033[0m")

		return s
