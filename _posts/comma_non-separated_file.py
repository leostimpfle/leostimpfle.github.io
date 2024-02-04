#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: leonardstimpfle
"""
#%%
import io
import re
import pandas as pd
import pandas.errors

#%%
sample = '''column1, column2, column3
1,"text without quote, but comma", 1
2,"text quoting "a sentence, words, and more" in a single cell", 2
'''

try:
    pd.read_csv(io.StringIO(sample))
except pandas.errors.ParserError:
    print('Parser unable to read file')

pattern = r'(?P<keep1>^|,"[^"]*)(?P<innerQuote1>")(?!,)(?P<keep2>[^"]+)(?P<innerQuote2>")(?P<keep3>[^"]*",|$)'

def deal_with_inner_quotes(string):
	# for example replace double quotes with single quotes
	return string.replace('"', "'")
	
def repl(m):
    parts  = [
		m.group('keep1'),
		deal_with_inner_quotes(m.group('innerQuote1')),
		m.group('keep2'),
		deal_with_inner_quotes(m.group('innerQuote2')),
		m.group('keep3'),
        ]
    return ''.join(parts)
	
sample_fixed = re.sub(pattern, repl, sample)
pd.read_csv(io.StringIO(sample_fixed))  # this works as expected