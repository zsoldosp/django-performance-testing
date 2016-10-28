from collections import OrderedDict as odict


print(odict(a='a', b='b'))
print(odict(b='b', a='a'))
print(odict([('a', 'a'), ('b', 'b')]))
print(odict([('b', 'b'), ('a', 'a')]))
