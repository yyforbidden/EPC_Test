import unittest
from EPCTest.checklist import CheckList, CheckItem, ExpressionParser, CheckFunctions
from EPCTest.checklist import TestFail, CheckExprSyntaxError

class TestCheckList(unittest.TestCase):


    def setUp(self):
        self.c = CheckList()


    def tearDown(self):
        pass


    def testCheck(self):
        self.c.check('1+1==2', 'test of check')
        self.assertEqual(len(self.c.check_list), 1)
        self.assertEqual(self.c.check_list[0].expr, '1+1==2')
        self.assertEqual(self.c.check_list[0].info, 'test of check')
        
        
    def testSaveVariable(self):
        self.c.save_variable({"var1": 1})
        self.c.save_variable({"var2": "x"})
        self.assertEqual(len(self.c.variable), 2)
        self.assertEqual(self.c.variable['var1'], 1.0)
        self.assertEqual(self.c.variable['var2'], 'x')
        
        
    def testSaveReport(self):
        report = {"var1": 1,
                  "var2": "x",
                  "var3": {"sub1": 2,
                           "sub2": "y",
                           "sub3.item": 3}}
        self.c.save_report(report)
        self.assertEqual(len(self.c.variable), 3)
        self.assertEqual(self.c.variable['var1'], 1.0)
        self.assertEqual(self.c.variable['var2'], 'x')
        self.assertEqual(len(self.c.variable['var3']), 3)
        self.assertEqual(self.c.variable['var3']['sub1'], 2.0)
        self.assertEqual(self.c.variable['var3']['sub2'], 'y')
        self.assertEqual(self.c.variable['var3']['sub3.item'], 3.0)
        
        
    def testException(self):
        self.assertRaises(TestFail, self.c.exception, 'test exeception')
        
        
    def testStartCheckPass(self):
        self.c.check('"a"=="a" && !1==2')
        self.c.check('1!=2')
        self.c.check('"a"=="a"')
        self.c.start_check()
        
    def testStartCheckFail(self):
        self.c.check('"a"=="a" && !1==2')
        self.c.check('1==2')
        self.c.check('"a"!="a"')
        self.assertRaises(TestFail, self.c.start_check)

    def testStartCheckError(self):
        self.c.check('"a"=="a" && !1==2')
        self.c.check('1!=2')
        self.c.check('"a"!="a')
        self.assertRaises(TestFail, self.c.start_check)

class TestCheckItem(unittest.TestCase):
    
    
    def setUp(self):
        pass
        
        
    def tearDown(self):
        pass
    
    
    def testEvaluatePass(self):
        c = CheckItem('1==1', 'Test Pass')
        c.evaluate(None)
        self.assertEqual(c.result, True)
        self.assertEqual(c.expr, '1==1')
        self.assertEqual(c.info, 'Test Pass')
        
        
    def testEvaluateFail(self):
        c = CheckItem('1!=1', 'Test Fail')
        c.evaluate(None)
        self.assertEqual(c.result, False)
        self.assertEqual(c.expr, '1!=1')
        self.assertEqual(c.info, 'Test Fail')
    
    
    def testEvaluateError(self):
        c = CheckItem('1=1=1', 'Test Error')
        c.evaluate(None)
        self.assertEqual(c.result, None)
        self.assertEqual(c.expr, '1=1=1')
        self.assertEqual(c.info, 'Test Error')
        
        
    def testReportPass(self):
        c = CheckItem('1==1', 'Test Pass')
        c.evaluate({})
        r = c.report()
        self.assertEqual(r,
                         '\n'
                         'Check Test Pass: 1==1\n'
                         'Result: Pass\n'
                         'Detail: \n'
                         'Variables: \n')


    def testReportFail(self):
        c = CheckItem('1!=1', 'Test Fail')
        c.evaluate({})
        r = c.report()
        self.assertEqual(r,
                         '\n'
                         'Check Test Fail: 1!=1\n'
                         'Result: Fail\n'
                         'Detail: \n'
                         'Variables: \n')


    def testReportError(self):
        c = CheckItem('1=1', 'Test Error')
        c.evaluate({})
        r = c.report()
        self.assertEqual(r,
                         '\n'
                         'Check Test Error: 1=1\n'
                         'Result: Error\n'
                         'Detail: Illegal character in check: =\n'
                         'Variables: \n')


class TestCheckFunctions(unittest.TestCase):
    
    
    def setUp(self):
        pass
    
    
    def tearDown(self):
        pass
    

    def testLength(self):
        l = CheckFunctions.length('aaa')
        self.assertEqual(l, 3)
        
        
    def testLengthOnInt(self):
        self.assertRaises(TypeError, CheckFunctions.length, 1)
        
        
    def testMatch(self):
        r = CheckFunctions.match(r'\w+', 'abcdefg')
        self.assertTrue(r)
        
        r = CheckFunctions.match(r'\w+', '    ')
        self.assertFalse(r)
        
        
    def testMatchOnInt(self):
        self.assertRaises(TypeError, CheckFunctions.match, '.*', 1)
        
        
    def testFilter(self):
        r = CheckFunctions.filter(r'\w+', 'abcdefg xyz xyz')
        self.assertEqual(r, 'abcdefg')
        
        r = CheckFunctions.filter(r'\w+', '    ')
        self.assertEqual(r, '')
        
        
    def testFilterOnInt(self):
        self.assertRaises(TypeError, CheckFunctions.filter, '.*', 1)
    

    def testSlice(self):
        r = CheckFunctions.slice('abc')
        self.assertEqual(r, 'abc')
        
        r = CheckFunctions.slice('abcdefg', 1, 3)
        self.assertEqual(r, 'bc')
        
        r = CheckFunctions.slice('abcdefg', 2)
        self.assertEqual(r, 'cdefg')
        
        r = CheckFunctions.slice('abcdefg', end=4)
        self.assertEqual(r, 'abcd')
        
        
    def testSliceOnInt(self):
        self.assertRaises(TypeError, CheckFunctions.slice, 1)
        
        
class TestExpressionParser(unittest.TestCase):
    
    
    def setUp(self):
        var = {'a': 1,
                'b': 'bbb',
                'c': {'x': 'x',
                      'y': 2,
                      'z.z1': 3}}
        self.p = ExpressionParser(var, debug=True)


    def tearDown(self):
        pass
    
    def testDigit(self):
        data = (('0', 0),
                ('1', 1),
                ('123', 123),
                ('1.03', 1.03),
                ('100.25', 100.25),
                ('100.1', 100.1),
                ('12.', 12.0),
                ('.15', 0.15),
                ('01', 1),
                ('13.100000', 13.1))
        for d in data:
            print 'Verifying %s==%f...' % d
            r = self.p.parse('%s == %f' % d)
            self.assertTrue(r)
            
            
    def testString(self):
        data = ("a", "", "abc", "\t", "\n\n")
        for d in data:
            print 'Verifying "%s"=="%s"...' % (d, d)
            r = self.p.parse('"%s" == "%s"' % (d, d))
            self.assertTrue(r)
            
            
    def testEquals(self):
        r = self.p.parse('1==1')
        self.assertTrue(r)
        
        r = self.p.parse('"a"=="a"')
        self.assertTrue(r)
        
        r = self.p.parse('1==2')
        self.assertFalse(r)
        
        r = self.p.parse('"a" == "b"')
        self.assertFalse(r)


    def testNotEquals(self):
        r = self.p.parse('1!=1')
        self.assertFalse(r)
        
        r = self.p.parse('"a"!="a"')
        self.assertFalse(r)
        
        r = self.p.parse('1!=2')
        self.assertTrue(r)
        
        r = self.p.parse('"a" != "b"')
        self.assertTrue(r)
        
        
    def testGreaterThan(self):
        r = self.p.parse('20>10')
        self.assertTrue(r)
        
        r = self.p.parse('10>20')
        self.assertFalse(r)
        
        r = self.p.parse('"xyz" > "abc"')
        self.assertTrue(r)
        
        r = self.p.parse('"abc" > "xyz"')
        self.assertFalse(r)
        
        
    def testGreaterEqual(self):
        r = self.p.parse('20>=10')
        self.assertTrue(r)
        
        r = self.p.parse('10>=20')
        self.assertFalse(r)
        
        r = self.p.parse('10>=10')
        self.assertTrue(r)
        
        r = self.p.parse('"xyz" >= "abc"')
        self.assertTrue(r)
        
        r = self.p.parse('"abc" >= "xyz"')
        self.assertFalse(r)

        r = self.p.parse('"abc" >= "abc"')
        self.assertTrue(r)


    def testLessThan(self):
        r = self.p.parse('20<10')
        self.assertFalse(r)
        
        r = self.p.parse('10<20')
        self.assertTrue(r)
        
        r = self.p.parse('"xyz" < "abc"')
        self.assertFalse(r)
        
        r = self.p.parse('"abc" < "xyz"')
        self.assertTrue(r)
        
        
    def testLessEqual(self):
        r = self.p.parse('20<=10')
        self.assertFalse(r)
        
        r = self.p.parse('10<=20')
        self.assertTrue(r)
        
        r = self.p.parse('10<=10')
        self.assertTrue(r)
        
        r = self.p.parse('"xyz" <= "abc"')
        self.assertFalse(r)
        
        r = self.p.parse('"abc" <= "xyz"')
        self.assertTrue(r)

        r = self.p.parse('"abc" <= "abc"')
        self.assertTrue(r)
    
    
    def testAnd(self):
        r = self.p.parse('1==1 && "a"=="a"')
        self.assertTrue(r)
        
        r = self.p.parse('1==1 && "a"!="a"')
        self.assertFalse(r)
        
        r = self.p.parse('1==1 && "a"=="a" && 2==2')
        self.assertTrue(r)
    
        r = self.p.parse('1==1 && "a"=="a" && 2!=2')
        self.assertFalse(r)

    
    def testOr(self):
        r = self.p.parse('1==1 || "a"!="a"')
        self.assertTrue(r)
        
        r = self.p.parse('1!=1 || "a"!="a"')
        self.assertFalse(r)
    
        r = self.p.parse('1==1 || "a"=="a" || 2!=2')
        self.assertTrue(r)
    
        r = self.p.parse('1!=1 || "a"!="a" || 2!=2')
        self.assertFalse(r)

    
    def testNot(self):
        r = self.p.parse('! 1==2')
        self.assertTrue(r)
        
        r = self.p.parse('! 1==1')
        self.assertFalse(r)
        
    
    def testPlus(self):
        r = []
        r.append(self.p.parse('10+10+003==23'))
        r.append(self.p.parse('"a"+"b"=="ab"'))
        r.append(self.p.parse('10+20+30 == 60'))
        r.append(self.p.parse('"abc"+"xyz"+"mn" == "abcxyzmn"'))
        r.append(self.p.parse('1.0+10.25+5+0==16.250000'))
        self.assertTrue(all(r))
    
    
    def testMinus(self):
        r = []
        r.append(self.p.parse('100-30==70'))
        r.append(self.p.parse('4321-1-300 == 4020'))
        r.append(self.p.parse('100.43210-0.43-0.0021-0.0000 == 100.0000'))
        self.assertTrue(all(r))
        
        self.assertRaises(TypeError, self.p.parse, '"abc"-"a"=="bc"')
    
    
    def testMultiply(self):
        r = []
        r.append(self.p.parse('10*20==200'))
        r.append(self.p.parse('4*5*100 == 2000'))
        r.append(self.p.parse('5.0*4.0 == 0020.000'))
        self.assertTrue(all(r))
        
        self.assertRaises(TypeError, self.p.parse, '"abc"*"a"=="bc"')
        
        
    def testDivide(self):
        r = []
        r.append(self.p.parse('100/2.0==50'))
        r.append(self.p.parse('002000/0.1 == 20000'))
        r.append(self.p.parse('0.1000/0.20000 == 00.50000'))
        self.assertTrue(all(r))
        
        self.assertRaises(TypeError, self.p.parse, '"abc"/"a"=="bc"')
        self.assertRaises(ZeroDivisionError, self.p.parse, '10/0==1')
    
    
    def testMinusUno(self):
        r = []
        r.append(self.p.parse('-10==-10'))
        r.append(self.p.parse('-0.3==-0.3'))
        r.append(self.p.parse('-0==0'))
        self.assertTrue(all(r))
        
        self.assertRaises(TypeError, self.p.parse, '-"abc"==-"abc"')
    
    
    def testParenthesis(self):
        r = []
        r.append(self.p.parse('3*(1+2)==9'))
        r.append(self.p.parse('6*(4*(1+2)+5)==102'))
        r.append(self.p.parse('3*((1+2)*(4+5))==81'))
        r.append(self.p.parse('(1)==1'))
        r.append(self.p.parse('(1+1)==2'))
        
        r.append(self.p.parse('1==1 && (2!=2 || 3==3)'))
        r.append(self.p.parse('!(1==1 && 2!=2)'))
        
        self.assertTrue(all(r))
        
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '(1==1')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '()')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1==1)')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '((1==1)')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '(1==1))')

        self.assertRaises(CheckExprSyntaxError, self.p.parse, '(1+1==2')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '2==1+1)')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '((1+1)==1')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1==(1+1))')

    def testPrecedance(self):
        r = []
        
        r.append(self.p.parse('1+2*3==7'))
        r.append(self.p.parse('3-4/2==1'))
        r.append(self.p.parse('2*-3==-6'))
        r.append(self.p.parse('2+-3==-1'))
        r.append(self.p.parse('1==1 && !2!=2'))
        r.append(self.p.parse('! 2!=2 || 3==3'))
        self.assertTrue(all(r))
    
    
    def testVariable(self):
        r = []
        r.append(self.p.parse('@a==1'))
        r.append(self.p.parse('@b=="bbb"'))
        r.append(self.p.parse('@c.x=="x"'))
        r.append(self.p.parse('@c.y==2'))
        r.append(self.p.parse('@c.z.z1==3'))
        self.assertTrue(all(r))
        
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '@foobar==1')
    
    
    def testFunction(self):
        r = []
        r.append(self.p.parse('f_length("aaa")==3'))
        r.append(self.p.parse('f_filter("\d+", "abc123ccc")=="123"'))
        r.append(self.p.parse('f_length(f_filter("\d+", "abc123ccc"))==3'))
        r.append(self.p.parse('f_slice("abcdefg", 5-5, 1+3)=="abcd"'))
        self.assertTrue(all(r))
    
    
    def testIllegalChar(self):
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '^1==1')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1==^1')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1==1^')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1^==^1')
    
    
    def testInvalidExpr(self):
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1==>2')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1 2==2')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1++3==2')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '/2==4')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '2==4 & 3==3')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1 && 3')
    
    
    def testIncompleteExpr(self):
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1+2')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1+1==2 &&')
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '1')
    
    
    def testEmptyExpr(self):
        self.assertRaises(CheckExprSyntaxError, self.p.parse, '')
        

if __name__ == "__main__":
    unittest.main()