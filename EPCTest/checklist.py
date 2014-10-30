from utils import keyword, logger
import ply.lex as lex
import ply.yacc as yacc
import re

class TestFail(Exception):
    """
    Implies that the current test case is failed or met an error.
    """
    pass

class CheckExprSyntaxError(Exception):
    """
    Implies that there are syntax errors in the check expression.
    """
    pass

class CheckList:
    """
    A series of check items.
    
    Variables and reports are saved to this object. Saved variables and reports
    can be used by the checking process.
    
    Keywords:
    check - Add a check item to the check list.
    
    Methods:
    save_variable - save a variable to the check list.
    save_report - save a report to the variable buffer of the check list.
    exception - called when an exception is recieved from one of the test tools.
                This method will terminate all pending check items.
    start_check - triggers the check process of all the check items.
    """
    
    def __init__(self):
        self.check_list = []
        self.variable = {}
        
        
    def save_variable(self, var):
        """
        Save variable to the check list.
        """
        
        # Assuming that json is used to transfer data between RF and TOOLS
        self.variable.update(var)
        
    
    def save_report(self, report):
        """
        Save report to the variable buffer of the check list.
        """
        
        # Assuming that json is used to transfer data between RF and TOOLS
        self.variable.update(report) 
        
    
    def exception(self, info):
        """
        Terminate the test check and raises TestFail.
        """
        
        raise TestFail(info)
    
    
    def check(self, expression, info=''):
        """
        Add a check item to the check list.
        
        The check list will be examined after all Tools report to RF.
        
        expression - the expression to be used to check.
        info - brief information of the check expression.
        """
        
        self.check_list.append(CheckItem(expression, info))
    
    
    def start_check(self):
        """
        Triggers the checking procedure of all the check items in the
        check list.
        """
        
        fail_info = []
        for check in self.check_list:
            check.evaluate(self.variable)
            s = check.report()
            logger.info(s)
            if check.result is not True:
                fail_info.append(s)
            
        if fail_info:
            raise TestFail(''.join(fail_info))
        
    
class CheckItem:
    def __init__(self, expr, info):
        self.expr = expr
        self.info = info
        self.result = None
        self.exception_info = None
        
        
    def evaluate(self, var):
        """
        Use the parser to evaluate the result of the expression.
        """
        
        self.var = var
        parser = ExpressionParser(var)
        try:
            self.result = parser.parse(self.expr)
        except CheckExprSyntaxError as e:
            self.result = None
            self.exception_info = e.args[0]
    
    
    def report(self):
        """
        The text summary of the result of the check expression.
        """
        
        template = ("\nCheck %s: %s\n"
                    "Result: %s\n"
                    "Detail: %s\n"
                    "Variables: %s\n")
        
        # Resolve the test result to text representation.
        result = dict(((True, 'Pass'),
                       (False, 'Fail'),
                       (None, 'Error')))
        if self.exception_info is None:
            self.exception_info = ''
        s = template % (self.info,
                        self.expr,
                        result[self.result],
                        self.exception_info,
                        ', '.join('%s=%s' % (str(k), str(v)) 
                                  for k, v in self.var.items()))
        return s
    
class CheckFunctions:
    """
    Check functions that can be called in the check expression.
    Argument and retruen data types are limited to float and string. 
    
    All these functions must be static.
    A prefix of "f_" must be used to indicate a function calling
    in the check expression. 
    """
    
    @staticmethod
    def length(s):
        """
        Length of a string.
        """
        
        return 1.0 * len(s)
    
    @staticmethod
    def match(pat, s):
        """
        Search a regular expression pattern in a string.
        """
        
        p = re.compile(pat)
        r = p.search(s)
        if r is not None:
            return True
        else:
            return False
    
    @staticmethod
    def filter(pat, s):
        """
        Extract substring according to given regular expression.
        """
        
        pat = '(%s)' % pat
        p = re.compile(pat)
        r = p.search(s)
        if r is not None:
            return r.groups()[0]
        else:
            return ''
         
    
    @staticmethod
    def slice(s, start=0, end=None):
        """
        Extract substring indicated by the given indexes.
        """
        
        start = int(start)
        if end is None:
            return s[start : ]
        end = int(end)
        return s[start : end]
    
    
class ExpressionParser:
    """
    Syntax of check expression:
    
    logic_expr : logic_expr AND logic_expr
              | logic_expr OR logic_expr
              | NOT logic_expr
              | assertion
              
    assertion : val_expr GT val_expr
              | val_expr LT val_expr
              | val_expr EQ val_expr
              | val_expr GE val_expr
              | val_expr LE val_expr
              | val_expr NE val_expr
              | '(' logic_expr ')'
          
    val_expr : val_expr PLUS val_expr
             | val_expr SUB val_expr
             | val_expr MUL val_expr
             | val_expr DIV val_expr
             | SUB val_expr
             | '(' val_expr ')'
             | function
             | value
             
    value : DIGIT
          | STRING
          | VARIABLE
           
    function : FUNCTION '(' para_list ')'
    para_list : val_expr
              | val_expr ',' para_list
    """
    
    def __init__(self, var, debug=False):
        self.var = var
        self._debug = debug
        
        # Build the parser
        self.lexer = lex.lex(module=self, debug=self._debug)
        self.parser = yacc.yacc(module=self, debug=self._debug, tabmodule='checklist_parse_tab')
        
    def debug(self, s):
        if self._debug:
            logger.info(s)
        
    tokens = ('DIGIT',
            'STRING',
            'FUNCTION',
            'VARIABLE',
            'PLUS',
            'SUB',
            'MUL',
            'DIV',
            'GT',
            'GE',
            'LT',
            'LE',
            'EQ',
            'NE',
            'AND',
            'OR',
            'NOT')
    
    t_DIGIT = r'\d+\.?\d*|\.\d+'
    t_STRING = r'"[^"]*"'
    t_FUNCTION = r'f_\w+'
    t_VARIABLE = r'@\w+\.?[\w.]*'
    t_PLUS = r'\+'
    t_SUB = r'\-'
    t_MUL = r'\*'
    t_DIV = r'/'
    t_GT = r'\>'
    t_GE = r'\>='
    t_LT = r'\<'
    t_LE = r'\<='
    t_EQ = r'=='
    t_NE = r'\!='
    t_AND = r'&&'
    t_OR = r'\|\|'
    t_NOT = r'\!'
    
    t_ignore = ' \t\n\r'
    
    literals = ',()'
    
    precedence = (('left', 'AND', 'OR'),
                  ('right', 'NOT'),
                  ('nonassoc', 'GT', 'LT', 'EQ', 'GE', 'LE', 'NE'),
                  ('left', 'PLUS', 'SUB'),
                  ('left', 'MUL', 'DIV'),
                  ('right', 'UMINUS'),)

    def t_error(self, t):
        raise CheckExprSyntaxError("Illegal character in check: "
                                   "%s" % (t.value[0]))
    
    def p_logic_and(self, p):
        "logic_expr : logic_expr AND logic_expr"
        p[0] = (p[1] and p[3])
        self.debug("logic_expr : logic_expr AND logic_expr -> "
                   "%s : %s && %s" % (p[0], p[1], p[3]))
         
    def p_logic_or(self, p):
        "logic_expr : logic_expr OR logic_expr"
        p[0] = (p[1] or p[3])
        self.debug("logic_expr : logic_expr OR logic_expr -> "
                   "%s : %s || %s" % (p[0], p[1], p[3]))
         
    def p_logic_not(self, p):
        "logic_expr : NOT logic_expr"
        p[0] = not p[2]
        self.debug("logic_expr : NOT logic_expr -> "
                   "%s : ! %s" % (p[0], p[2]))
         
    def p_logic_assert(self, p):
        "logic_expr : assertion"
        p[0] = p[1]
        self.debug("logic_expr : assertion -> "
                   "%s: %s" % (p[0], p[1]))
     
    def p_assertion_gt(self, p):
        "assertion : val_expr GT val_expr"
        p[0] = (p[1] > p[3])
        self.debug("assertion : val_expr GT val_expr -> "
                   "%s : %s > %s" % (p[0], p[1], p[3]))
         
    def p_assertion_lt(self, p):
        "assertion : val_expr LT val_expr"
        p[0] = (p[1] < p[3])
        self.debug("assertion : val_expr LT val_expr -> "
                   "%s : %s < %s" % (p[0], p[1], p[3]))
         
    def p_assertion_eq(self, p):
        "assertion : val_expr EQ val_expr"
        p[0] = (p[1] == p[3])
        self.debug("assertion : val_expr EQ val_expr -> "
                   "%s : %s == %s" % (p[0], p[1], p[3]))
          
    def p_assertion_ge(self, p):
        "assertion : val_expr GE val_expr"
        p[0] = (p[1] >= p[3])
        self.debug("assertion : val_expr GE val_expr -> "
                   "%s : %s >= %s" % (p[0], p[1], p[3]))
         
    def p_assertion_le(self, p):
        "assertion : val_expr LE val_expr"
        p[0] = (p[1] <= p[3])
        self.debug("assertion : val_expr LE val_expr -> "
                   "%s : %s <= %s" % (p[0], p[1], p[3]))
         
    def p_assertion_ne(self, p):
        "assertion : val_expr NE val_expr"
        p[0] = (p[1] != p[3])
        self.debug("assertion : val_expr NE val_expr -> "
                   "%s : %s != %s" % (p[0], p[1], p[3]))
 
    def p_assertion_parenthesis(self, p):
        "assertion : '(' logic_expr ')'"
        p[0] = p[2]
        self.debug("assertion : '(' logic_expr ')' -> "
                   "%s : (%s)" % (p[0], p[2]))
         
    def p_val_expr_plus(self, p):
        "val_expr : val_expr PLUS val_expr"
        p[0] = p[1] + p[3]
        self.debug("val_expr : val_expr PLUS val_expr -> "
                   "%s : %s + %s" % (p[0], p[1], p[3]))
          
    def p_val_expr_minus(self, p):
        "val_expr : val_expr SUB val_expr"
        p[0] = p[1] - p[3]
        self.debug("val_expr : val_expr SUB val_expr -> "
                   "%s : %s - %s" % (p[0], p[1], p[3]))
         
    def p_val_expr_multiply(self, p):
        "val_expr : val_expr MUL val_expr"
        p[0] = p[1] * p[3]
        self.debug("val_expr : val_expr MUL val_expr -> "
                   "%s : %s * %s" % (p[0], p[1], p[3]))
         
    def p_val_expr_divide(self, p):
        "val_expr : val_expr DIV val_expr"
        p[0] = p[1] / p[3] 
        self.debug("val_expr : val_expr DIV val_expr -> "
                   "%s : %s / %s" % (p[0], p[1], p[3]))
         
    def p_val_expr_minus_uno(self, p):
        "val_expr : SUB val_expr %prec UMINUS"
        p[0] = -p[2]
        self.debug("val_expr : SUB val_expr %%prec UMINUS -> "
                    "%s : -%s" % (p[0], p[2]))

    def p_val_expr_function(self, p):
        "val_expr : function"
        p[0] = p[1]
        self.debug("val_expr : function -> "
                   "%s : %s" % (p[0], p[1]))
         
    def p_val_expr_parenthesis(self, p):
        "val_expr : '(' val_expr ')'"
        p[0] = p[2]
        self.debug("val_expr : '(' value_expr ')' -> "
                   "%s : (%s)" % (p[0], p[2]))
         
    def p_val_expr_value(self, p):
        "val_expr : value"
        p[0] = p[1]
        self.debug("val_expr : value -> "
                   "%s : %s" % (p[0], p[1]))
        
    def p_value_digit(self, p):
        "value : DIGIT"
        p[0] = float(p[1])
        self.debug("value : DIGIT -> "
                   "%s : %s" % (p[0], p[1]))
        
    def p_value_string(self, p):
        "value : STRING"
        p[0] = str(p[1][1:-1])
        self.debug("value : STRING -> "
                   "%s : %s" % (p[0], p[1]))
         
    def p_value_variable(self, p):
        "value : VARIABLE"
        v = p[1][1:]
        v = v.split('.', 1)
        try:
            if len(v) == 1:
                p[0] = self.var[v[0]]
            else:
                p[0] = self.var[v[0]][v[1]]
        except KeyError:
            raise CheckExprSyntaxError("Unknown variable in check: "
                                       "%s'" % v)
        self.debug("value : VARIABLE -> "
                   "%s : %s" % (p[0], p[1]))
         
    def p_function(self, p):
        "function : FUNCTION '(' para_list ')'"
        f = getattr(CheckFunctions, p[1][2:])
        p[0] = f(*p[3])
        self.debug("function: FUNCTION '(' para_list' ')' -> "
                   "%s : %s(%s)" % (p[0], p[1], ', '.join(map(str, p[3]))))
         
    def p_para_list_single(self, p):
        "para_list : val_expr"
        p[0] = [p[1]]
        self.debug("para_list : val_expr -> "
                   "%s : %s" % (p[0], p[1]))
         
    def p_para_list(self, p):
        "para_list : val_expr ',' para_list"
        p[0] = p[3]
        p[0].reverse()
        p[0].append(p[1])
        p[0].reverse()
        self.debug("para_list : val_expr ',' para_list -> "
                   "%s : %s, %s" % (p[0], p[1], p[3]))
         
    def p_error(self, p):
        if p is None:
            raise CheckExprSyntaxError
        raise CheckExprSyntaxError('Syntax Error: line %d, '
                                   '"%s"' % (p.lexer.lineno, p.value))
        
    def parse(self, expr):
        r = self.parser.parse(expr, lexer=self.lexer)
        return r
        
        