---
layout: post
title:  "Visualising Fixed Effects"
date:   2024-02-10
categories: econometrics
---
[Fixed effect models](https://en.wikipedia.org/wiki/Fixed_effects_model) are a popular tool to deal with unobserved heterogeneity.  This post tries to illustrate how they work in a non-technical way.
<!--more-->

## Illustration

Let's illustrate a fixed effects with some beautifully well-behaved synthetic data.[^3]  Consider a population of individuals characterised by a dummy variable $\verb\|property_dummy\|$ indicating exposure to a treatment that occurs in $t=2017$.  For each individual $i$, we have a time series of observations that follows a linear two-way fixed effects model:

$$
y_{it} = \verb|property_dummy|_i*\delta_t^{2017} + \nu_i + \tau_t + \epsilon_{it},\text{ where }\delta^{2017}_i=\begin{cases}1,&\text{if }t\geq 2017,\\0,&\text{otherwise}.\end{cases}
$$

{% include 2024-02-10-fixed_effects/sample.html %}

For the sake of illustration, let's introduce some unobserved heterogeneity between the individuals receiving treatment and the ones not receiving treatment.  We define the individual fixed effects $\nu_i$ to depend on $\verb\|property_dummy\|_i$ via an ubobserved variable $\verb\|property_alpha\|_i$:

$$\nu_i=\verb|property_alpha|_i=\begin{cases}
	2,&\text{if }\verb|property_dummy|_i=1,\\
	3,&\text{if }\verb|property_dummy|_i=0,
	\end{cases}$$

Clearly, the effect of treatment on $y_{it}$ in this model is equal to 1.  Let's see how pooled ordinary least squares (POLS) compares to a fixed effects model.

### POLS
POLS estimates the effect of the treatment by the difference in averages of the dependent variable with and without treatment.  Because we assume $\verb|property_alpha|_i$ to be unobservable, our estimate can only rely on the observable difference in $\verb|property_dummy|_i$ alone:

{% include 2024-02-10-fixed_effects/box1.html %}

The difference in means before and after treatment is nowhere near what it should.  Now, we know that the synthetic data is generated from an unobservable $\verb\|property_alpha\|_i$.  Splitting our sample into sub-samples for $\verb\|property_alpha\|_i=A$ and $\verb\|property_alpha\|_i=B$, we see that only the former is affected by treatment (what a nasty surprise!).  Because the mean of the latter is higher than the pre-treatment mean of the former, POLS would likely understimate the treatment effect.  This is why unobserved heterogeneity is bad:

{% include 2024-02-10-fixed_effects/box2.html %}

In the real world where we usually have observational rather than synthetic data, we may not have the luxury of looking under the hood of the data generating process and simply observe $\verb\|property_alpha\|_i$ (it's meant to be unobservable after all).  But under certain conditions there is actually no need to observe this property.  This is where fixed effects come into play.

### Fixed Effects

Fixed effects models are designed to eliminate unobserved heterogeneity which is fixed at a certain level (individuals, time periods, schools, industrial sectors, etc.).  The simplest implementation of fixed effects models demeans the data at the level of the fixed effects[^1].  A fixed effects model with individual and time fixed effects is also called *two-way fixed effects model*.

Demeaning ensures that terms fixed at the individual or time level $\nu_i$ and $\tau_i$ drop out of of the model.  This can be seen nicely when plotting the synthetic data as above at the different stages of demeaning:

{% include 2024-02-10-fixed_effects/sample_fe.html %}

After eliminating the individual and time fixed effects, there are only two sources of variation remaining: The treatment $\delta_t^{2017}$ and the error term $\epsilon_{it}$.

Clearly, the treatment increases the dependent variable for  the individuals with $\verb\|propert_dummy\|_i=1$ (the blue lines).  But it looks as if the effect is only roughly half of what we expect (0.5 versus 1).  And why does the treatment seem to *decrease* the dependent variable for $\verb\|propert_dummy\|_i=0$ (the red lines)? 

The reason is that the transformed data is a *relative* measure:  For each observation it is relative to the mean of that observation's individual (individual fixed effects are eliminated) and relative to the mean of that observation's time period (time fixed effects are eliminated).  So if it increases for half the population (blue), it decreases for the other half (red).

Consequently, the treatment effect is given by the difference in means before and after treatment and between individuals with different $\verb\|propert_dummy\|_i$.[^2]  Eyballing the last graph, the means before and after treatment within both groups change by 0.5 but in opposite directions, so the total treatment effect is 1 as expected.



# Footnotes
[^3]: The code to generate the data and graphs in this post is available [here](https://github.com/leostimpfle/leostimpfle.github.io/blob/main/_code/2024-02-10-fixed_effects.py).
[^1]: For details see, e.g., [(Imai & Kim, 2021)](https://www.cambridge.org/core/journals/political-analysis/article/abs/on-the-use-of-twoway-fixed-effects-regression-models-for-causal-inference-with-panel-data/F10006D0210407C5F9C7CAC1EEE3EF0D).
[^2]: In fact, the two-way fixed effects estimator "is equivalent to the difference-in-differences estimator under the simplest setting with two groups and two time periods". [(Imai & Kim, 2021)](https://www.cambridge.org/core/journals/political-analysis/article/abs/on-the-use-of-twoway-fixed-effects-regression-models-for-causal-inference-with-panel-data/F10006D0210407C5F9C7CAC1EEE3EF0D)
