---
layout: post
title:  "Non-separating commas in comma separated values"
date:   2024-02-03 16:24:48 +0100
categories: python
---
	
Ill-formatted csv files are not uncommon.  This post explores how to deal with a particular problem in [`python`](https://www.python.org) using [regular expressions](https://docs.python.org/3/howto/regex.html).
	
## The Problem
The ill-formatted csv files contained values that represented enumerations or even full sentences which, unsurprisingly, themselves contained multiple commas.  The files' creators seemed to have thought of enclosing those fields with double quotes to make clear that the comma is not a separator.  They have not, however, thought of the possibility that the enumerations themselves can contain double quotes resulting in a malformed csv file of the form

{% highlight ruby %}
sample = '''column1,column2,column3
1,"text without quote, but comma",1
2,"text quoting "a sentence, words, and more" in a single cell",2'''
{% endhighlight %}

Now, when reading the file with [<code>pandas</code>](https://pandas.pydata.org) the parser thinks that the third row consists of five columns instead of three and will throw a <code>ParseError</code>:[^2]

{% highlight ruby %}
import io
import pandas as pd
pd.read_csv(io.StringIO(sample))  # this throws ParserError: Error tokenizing data. C error: Expected 3 fields in line 3, saw 5
{% endhighlight %}
	
## The Solution
To the human eye it is clear that the sample contains three columns and that the second field in the third row contains nested double quotes rather than three separate fields. The objective is to replace the inner double quotes to enable the parser to identify the string within the outer double quotes as a single field.  This is achieved with a regular expression and a dynamic replacement of the string matched by the expression.  Keep on reading for an explanation of the solution.

{% highlight ruby %}
import re
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
{% endhighlight %}

## Explanation

### Identifying the Problematic Strings
  This is the kind of task that is perfect to be tackled with [*regular expressions*](https://en.wikipedia.org/wiki/Regular_expression). The Python Standard Library comes with the module [`re`](https://docs.python.org/3/library/re.html#module-re) providing regular expression operations. The first step is to define a regular expression that matches the problematic fields.

#### The Outer Double Quotes
Let's start with identifying the fields enclosed by double (and checking for commas or beginning/end of strings using the *non-capturing groups* `(?:...)`):

{% highlight ruby %}
pattern = '(?:^|,)".*"(?:,|$)'
{% endhighlight %}

Applying the `pattern` to our `sample`, shows that it captures the relevant sub-strings:

{% highlight ruby %}
import re
pattern = '(?:^|,)"(?!,).*"(?:,|$)'
matches = re.findall(pattern, sample)
print(matches)  # a list of two strings: [',"text without quote, but comma",', ',"text quoting "a sentence, words, and more" in a single cell",']
{% endhighlight %}

#### The Inner Double Quotes
We now can identify all fields that are enclosed by double quotes.  But we don't need to actually modify all of them as the parser only gets confused by those that also contain inner double quotes.  Let's therefore modify the inner part of the `pattern` to something more restrictive.

- The first outer and first inner double quote can be separated by an arbitrary, possibly empty string that is not a double quote which corresponds to the expression `[^"]*`.
- Because the first inner double quote is the start of a new quote it must not be followed by a comma, so we add a *negative lookahead* `"(?!,)`.
- Following the first inner double quote is an arbitrary but non-empty string that must not contain double quotes `[^"]+`.[^1]
-  Finally, the second inner double quote can be followed by an arbitrary, possibly empty string without double quotes `"[^"]*`.

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
Once we have identified the problematic string, we still have to sanitise it to make it palatable for the parser.  The trick for me was to realise that `re.sub` can take a function that takes the `re.Match` object captured by `pattern` as an argument.  This enables a dynamic replacement of capturing groups in the string as opposed to a static replacement by a fixed value.

Let's first look at what the function has to do. It takes a single argument `m` which is a `re.Match` object obtained from matching `pattern` in `sample`.  The captured groups in the `re.Match` object can be accessed via `re.Match.groups`, so we can select the groups that we want to change (the inner double quotes) and the ones we want to keep (everything else).

By default, match groups can be accessed by their integer indices.  But to improve readability, let's update `pattern` with *named capturing groups* using the syntax `(?P<name>...)`.  The matched groups can then be accessed by their name `re.Match.group('<name>')`.

{%highlight ruby %}
pattern = r'(?P<keep1>^|,"[^"]*)(?P<innerQuote1>")(?!,)(?P<keep2>[^"]+)(?P<innerQuote2>")(?P<keep3>[^"]*",|$)'
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
		deal_with_inner_quotes(m.group('innerQuote2')),
		m.group('keep3'),
        ]
    return ''.join(parts)
	
print(re.sub(pattern, repl, sample))  # 'column1, column2, column3\n1,"text without quote, but comma", 1\n2"text quoting \'a sentence, words, and more\' in a single cell" 2\n'
{% endhighlight %}


# Footnotes
[^2]: [`pandas.read_csv`](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) provides an argument `on_bad_lines` which is set to `error` by default.  To avoid the `ParseError` and discard the ill-formed lines the user can simply set it to `warn` or `skip`.
[^1]: Let's for simplicity assume that there is no third nested level of double quotes.
