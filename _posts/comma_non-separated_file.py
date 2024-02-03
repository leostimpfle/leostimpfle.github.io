#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 17:29:25 2024

@author: leonardstimpfle
"""
#%%
import io
import re
import pandas as pd

#%%
sample = '''column1, column2, column3
1,"text without quote, but comma", 1
2,"text quoting "a sentence, words, and more" in a single cell", 2
'''

# pd.read_csv(io.StringIO(sample))
#

pattern = '(?:^|,)(?P<keep1>"[^"]*)(?P<replace1>")(?!,)(?P<keep2>[^"]+)(?P<replace2>")(?P<keep3>[^"]*")(?:,|$)'


#%%
def repl(m):
    
    join = [
		m.group('keep1'),
        m.group('replace1').replace('"', "'"),
        m.group('keep2'),
        m.group('replace2').replace('"', "'"),
        m.group('keep3'),
        ]
    return ''.join(join)