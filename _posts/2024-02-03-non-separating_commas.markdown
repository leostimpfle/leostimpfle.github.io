---
layout: post
title:  "Non-separating commas in comma separated values"
date:   2024-02-03 16:24:48 +0100
categories: python
---
	
Ill-formatted csv files are not uncommon.  This post explores how to deal with a particular problem in [`python`](https://www.python.org) using [`pandas`](https://pandas.pydata.org) and regular expressions.
	
# The Problem
I recently encountered files that contained enumerations or even full sentences which, unsurprisingly, contained multiple commas.  The files' creators seemed to have thought of enclosing those fields with double quotes to make clear that the comma is not a separator.  They have not, however, thought of the possibility that the enumerations themselves can contain double quotes resulting in a malformed csv file of the form

{% highlight ruby %}
sample = '''column1,column2,column3
1,"text without quote, but comma",1
2,"text quoting "a sentence, words, and more" in a single cell",2'''
{% endhighlight %}

Now, when reading the file with [<code>pandas</code>](https://pandas.pydata.org) the parser thinks that the third row consists of five columns instead of three and will throw a <code>ParseError</code>:

{% highlight ruby %}
import io
import pandas as pd
pd.read_csv(io.StringIO(sample))  # this throws ParserError: Error tokenizing data. C error: Expected 3 fields in line 3, saw 5
{% endhighlight %}
	
# The Solution
To the human eye it is clear that the sample contains three columns and that the second field in the third row contains nested doublequotes rather than three separate fields. So, the goal should be to replace the inner double quotes to enable the parser to read the field from the first double quote to the last without being thrown off by the additional commas.

### TL;DR
{% highlight ruby %}
import re
pattern = '(?:^|,)(?P<keep1>"[^"]*)(?P<innerQuote1>")(?!,)(?P<keep2>[^"]+)(?P<innerQuote2>")(?P<keep3>[^"]*")(?:,|$)'

def deal_with_inner_quotes(string):
	# for example replace double quotes with single quotes
	return string.replace('"', "'")
	
def repl(m):
    parts  = [
		m.group('keep1'),
		deal_with_inner_quotes(m.group('innerQuote1')),
		m.group('keep2'),
		deal_with_inner_quotes(m.groups('innerQuote2')),
		m.group('keep3'),
        ]
    return ''.join(parts)
	
print(re.sub(pattern, repl, sample))
{% endhighlight %}

### Identifying the Problematic Strings
This is the kind of task that is perfect to be tackled with [*regular expressions*](https://en.wikipedia.org/wiki/Regular_expression). The Python Standard Library comes with the module [`re`](https://docs.python.org/3/library/re.html#module-re) providing regular expression operations. The first step is to define a regular expression that matches the problematic fields.

#### The Outer Double Quotes
Let's start with identifying the fields enclosed by double (and checking for commas or beginning/end of strings using the *non-capturing groups* `(?:...)`):

{% highlight ruby %}
pattern = '(?:^|,)".*"(?:,|$)'
{% endhighlight %}

Applying the `pattern` to our `sample`, shows that it captures the relevant substrings:

{% highlight ruby %}
import re
pattern = '(?:^|,)"(?!,).*"(?:,|$)'
matches = re.findall(pattern, sample)
print(matches)  # a list of two strings: [',"text without quote, but comma",', ',"text quoting "a sentence, words, and more" in a single cell",']
{% endhighlight %}

#### The Inner Double Quotes
We now can identify all fields that are enclosed by double quotes.  But we don't need to actually modify all of them as the parser only gets confused by those that also contain inner double quotes.  Let's therefore modify the inner part of the `pattern` to something more restrictive.

- We start by noting that the first outer and first inner double quote can directly follow each other or be separated by an arbitrary string that is not a double quote. This corresponds to the expression `[^"]*`.
- Because the first inner double quote is the start of a new quote it must not be followed by a comma, so we add a *negative lookahead* `"(?!,)`.
- Following the first inner double quote is an arbitrary but non-empty string that must not contain double quotes `[^"]+`.[^1]
- This should be followed by the second inner double quote which can be followed by an arbitrary, possibly empty string without double quotes before we arrive at the closing outer double quote `"[^"]*`.

Putting it all together yields the `pattern`:

{% highlight ruby %}
pattern = '(?:^|,)"[^"]*"(?!,)[^"]+"[^"]*"(?:,|$)'
{% endhighlight %}

Let's apply it to our `sample`:
{% highlight ruby %}
pattern = '(?:^|,)"[^"]*"(?!,)[^"]+"[^"]*"(?:,|$)'
matches = re.findall(pattern, sample)
print(matches)  # a list of a single string: [',"text quoting "a sentence, words, and more" in a single cell",']
{% endhighlight %}

### Sanitising the Problematic Strings
Once we have identified the problematic strings, we still have to sanitise them to make them digestible for the parser. We will use the built-in function `re.sub` to replace the inner double quotes.  The trick for me was to realise that `re.sub` can take a function that takes the `re.Match` object captured by `pattern` as an argument.  This enables a dynamic replacement of capturing groups in the string as opposed to a static replacement by a fixed value.

Let's first look at what the function has to do. It takes a single argument `m` which is a `re.Match` object constructed from matching the `pattern` in the string `sample`.  The captured groups in the `re.Match` object can be accessed via `re.Match.groups`, so we can select the groups that we want to change (the inner double quotes) and that we want to keep (everything else).

For better readibility, let's update `pattern` to use *named capturing groups* using the syntax `(?P<name>...)`.

{%highlight ruby %}
pattern = '(?:^|,)(?P<keep1>"[^"]*)(?P<innerQuote1>")(?!,)(?P<keep2>[^"]+)(?P<innerQuote2>")(?P<keep3>[^"]*")(?:,|$)'
{% endhighlight %}

We can use the group names to get a captured group from the `re.Match` object and apply a custom function `deal_with_inner_quotes` to selected groups. This will look something like this:

{% highlight ruby %}
def deal_with_inner_quotes(string):
	# for example replace double quotes with single quotes
	return string.replace('"', "'")
	
def repl(m):
    parts  = [
		m.group('keep1'),
		deal_with_inner_quotes(m.group('innerQuote1')),
		m.group('keep2'),
		deal_with_inner_quotes(m.groups('innerQuote2')),
		m.group('keep3'),
        ]
    return ''.join(parts)
	
print(re.sub(pattern, repl, sample))  # 'column1, column2, column3\n1,"text without quote, but comma", 1\n2"text quoting \'a sentence, words, and more\' in a single cell" 2\n'
{% endhighlight %}


# Footnotes
[^1]: Let's for simplicity assume that there is no third nested level of double quotes.
[^2]:
