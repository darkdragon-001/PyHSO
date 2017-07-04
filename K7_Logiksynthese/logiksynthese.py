# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 21:49:33 2017

@author: Marcel
"""

### Types ###

# Literal: a,b,c,...
# Inverted Literal: A=!a, B=!b, ...
class lit(int):
    def __new__(cls, v):
        if isinstance(v, int):
            if (0 <= v and v < 26) or (100 <= v and v < 126): # 0..25 (a-z) and 100..125 (!a-!z)
                return int.__new__(cls, v)
            else:
                raise ValueError("Only literals 0..25 (a-z) and 100..125(!a-!z) are supported for compact printing.")
        elif isinstance(v, str):
            o = ord(v)
            if ord('a') <= o and o <= ord('z'):
            return int.__new__(cls, ord(v)-ord('a'))
            elif ord('A') <= o and o <= ord('Z'):
                return int.__new__(cls, 100+ord(v)-ord('A'))
        else:
            raise TypeError("Literals must be either integers or characters.")
    # TODO overload other set operators: https://docs.python.org/2/library/stdtypes.html#set
    def __or__(self, c): # set union
        if isinstance(c, cube):
            return c | self
        elif isinstance(c, lit):
            return cube([c]) | self
        else:
            raise TypeError("Can only make union of literal and cube.")
    def __mul__(self, l): # logic and # lit('a')*lit('b')=cube('ab')
        return cube([self, l])
    def __str__(self):
        return chr(ord('a')+self)
# Cube: abc
class cube(frozenset): # set of literals
    def __new__(cls, s): # TODO use *argv to allow calling without arguments for empty set
        if isinstance(s, str):
            s = [lit(c) for c in s]
        elif isinstance(s, lit):
            return frozenset.__new__(cls, [s])
        return frozenset.__new__(cls, s)
    # TODO overload other set operators: https://docs.python.org/2/library/stdtypes.html#set
    def __or__(self, c): # set union
        if isinstance(c, func):
            return c | self
        elif isinstance(c, lit):
            c = cube([c])
        return cube(frozenset.__or__(self,c))
    def __add__(self, c): # logic or # cube('ab')+cube('cd')=func('ab+cd')
        return func([self, c])
    def __sub__(self, c): # set substract # cube('abc')-cube('c')=cube('ab')
        return cube(frozenset.__sub__(self,c))
    def __str__(self):
        res = [str(f) for f in list(self)]
        res.sort()
        return "".join(res);
# Function: abc+de
class func(frozenset): # set of cubes
    # constructor
    def __new__(cls, s): # TODO use *argv to allow calling without arguments for empty set
        if isinstance(s, str):
            return frozenset.__new__(cls, [cube(c) for c in s.split('+')])
        elif isinstance(s, cube):
            return frozenset.__new__(cls, [s])
        else:
            return frozenset.__new__(cls, s)

    # custom functions
    def num_lit(self): # number of literals -> highest used literal
        res = 0;
        for c in self:
            for l in c:
                if l > res:
                    res = l
        return res+1 # indices start at 0

    # set operators
    def __or__(self, f): # set union
        if isinstance(f, lit):
            f = cube([f])
        if isinstance(f, cube):
            f = func([f])
        if not isinstance(f, func):
            raise TypeError("Set operations only possible for same type [here: func] (implicit upcasts supported: lit->cube->func).")
        return func(frozenset.__or__(self,f))
    def __and__(self, f): # set intersection
        if isinstance(f, lit):
            f = cube([f])
        if isinstance(f, cube):
            f = func([f])
        if not isinstance(f, func):
            raise TypeError("Set operations only possible for same type [here: func] (implicit upcasts supported: lit->cube->func).")
        return func(frozenset.__and__(self,f))
    def __sub__(self, f): # set difference
        if isinstance(f, lit):
            f = cube([f])
        if isinstance(f, cube):
            f = func([f])
        if not isinstance(f, func):
            raise TypeError("Set operations only possible for same type [here: func] (implicit upcasts supported: lit->cube->func).")
        return func(frozenset.__sub__(self,f))
    def __xor__(self, f): # set symmetric difference (elements only in one but not in both)
        if isinstance(f, lit):
            f = cube([f])
        if isinstance(f, cube):
            f = func([f])
        if not isinstance(f, func):
            raise TypeError("Set operations only possible for same type [here: func] (implicit upcasts supported: lit->cube->func).")
        return func(frozenset.__xor__(self,f))

    # algebraic functions on logic expressions
    def __add__(self, f): # algebraic "+" = logic "OR"
        return self.__or__(f) # same as set union
    def __mul__(self, cc): # algebraic "*" = logic "AND"
        if isinstance(cc, lit):
            cc = cube([cc])
        if not isinstance(cc, cube):
            raise TypeError("Functions can only be multiplied by cubes or literals.")
        f = func([])
        for c in self:
            f = f | (c | cc)
        return f
    # TODO handle case func('c')/cube('c') -> need lit('1')?
    #      -> currently cube([]) is interpreted as '1'
    def __truediv__(self, cc): # algebraic "/" without rest: q=f/g <=> f=q*g+r
        if isinstance(cc, lit):
            cc = cube([cc])
        if not isinstance(cc, cube):
            raise TypeError("Functions can only be multiplied by cubes or literals.")
        f = func([])
        for c in self:
            if cc <= c: # without rest
                f = f | (c - cc)
        return f
    def __mod__(self, cc): # algebraic/logic division rest
        f = func([])
        for c in self:
            if not (cc <= c): # rest
                f = f | c
        return f

    # representation
    def __str__(self):
        res = [str(f) if len(f)>0 else '1' for f in list(self)]
        res.sort()
        return "+".join(res)

### Tests ###
        
def test():
    assert lit(0) == lit('a')
    assert lit('c') in cube('abc')
    assert lit('a')|lit('b') == cube('ab')
    assert lit('a')|cube('bc') == cube('abc')
    assert cube([lit('a'),lit('b')]) == cube('ab')
    assert cube('aaa') == cube('a')
    assert cube('ab')|lit('c') == cube('abc')
    assert cube('ab')|cube('bc') == cube('abc')
    assert cube('ab')|func('bc+cd') == func('ab+bc+cd')
    assert func([cube([lit('a'),lit('b')]),cube([lit('a'),lit('c')])]) == func('ab+ac')
    assert func('ab+ac+ab') == func('ab+ac')
    assert func('ab+cd')|cube('ef') == func('ab+cd+ef')
    assert func('ab+cd')|func('ef') == func('ab+cd+ef')
    assert func('a+b+cd')*cube('d') == func('ad+bd+cd')
    assert func('abc+acd+ad')/cube('ac') == func('b+d')
    assert func('abc+acd+ad')%cube('ac') == func('ad')
    assert func('abc')/lit('c') == func('ab')
    assert func('c')/cube('c') == func(cube([]))


### Helpers ###

import itertools
def powerset(items):
    return [x for length in range(len(items)+1) for x in itertools.combinations(items, length)]

# sort literals based on number of occurences
from collections import Counter
from functools import reduce
# count number of occurences for all literals
def count(f): # count
    return reduce((lambda x, y : x + Counter(y)), f, Counter()) # use Counter to merge cube-sets
# sort literals based on number of occurences
def cs(f): # count, sort
    return [e[0] for e in count(f).most_common()] # sort counts desc (most_common), get literals without counts


### Algorithm ###

def _level0kernels(f,ls,j): # function, sorted literals, literal number
    #print('call:', f, ';', ls, ';', j)
    k = set()
    for i in range(len(ls)):
        li = ls[i]
        # literal ls[i] contained in more than one cubes of f
        if len([1 for c in f if li in c]) > 1:
            #print('li:', li)
            f2 = f / li
            #print('f2:',f2)
            # largest cube dividing f2 without rest 
            # => cube consisting of all literals which occur in all cubes of f2
            # -> number of occurences equal to number of cubes in f2
            c = cube([e[0] for e in count(f2).most_common() if e[1] == len(f2)])
                #print('c:',c)
            if not any([ls[k] in c for k in range(i)]):
                k |= _level0kernels(f/(li|c), ls, i+1)
    if len(k) < 1:
        k.add(f)
    #print('return:',k)
    return k
     
def level0kernels(f):
    return _level0kernels(f, cs(f), 0)
    
### Main ###
        
def main(argv):
    # run tests
    test()
    
    # process data
    # NOTE inverted literals are written with capital letteres
    result = level0kernels(func('adf+aef+bdf+bef+cdf+cef+g')) # slide 29
    #result = level0kernels(func('abeG+abfg+abgE+aceG+acfg+acgE+deG+dfg+dgE+bh+bi+ch+ci')) # slide 31
    for r in result:
        print(r)

if __name__ == "__main__":
    from sys import argv
    main(argv)
