#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: leonardstimpfle
"""
#%% imports
import enum
import pandas as pd
import numpy as np

#%% properties
class PropertyAlpha(enum.Enum):
    A = 2
    B = 3
    
class PropertyBeta(enum.Enum):
    A = 0.5
    B = 1.5
    
class PropertyDummy(enum.Enum):
    TRUE = 1
    FALSE = 0
    
#%% cluster
class Cluster():
    
    def __init__(self, property_alpha, property_beta, property_dummy):
        self._property_alpha = property_alpha
        self._property_beta = property_beta
        self._property_dummy = property_dummy
        
    def __iter__(self):
        return (prop for prop in dir(self) if prop.startswith('property_'))
    
    @property
    def property_alpha(self):
        return self._property_alpha
    
    @property
    def property_beta(self):
        return self._property_beta  
    
    @property
    def property_dummy(self):
        return self._property_dummy
        

#%% individual
class Effects(enum.Enum):
    Fixed = enum.auto()
    Random = enum.auto()
    
class Noise(enum.Enum):
    TRUE = True
    FALSE = False
    
    
class Individual():
    
    def __init__(self, identifier, cluster, effects=Effects.Fixed, noise=Noise.FALSE):
        self._identifier = identifier
        self._effects_type = effects
        self._noise = noise
        self.cluster = cluster
        
    def __repr__(self):
        return f'Individual{self._identifier}{self.effects}{self.noise}'
    
    @property
    def identifier(self):
        return self._identifier
    
    @property
    def effects_type(self):
        return self._effects_type
    
    @property
    def noise(self):
        return self._noise
        
    @property
    def cluster(self):
        return self._cluster
    
    @cluster.setter
    def cluster(self, cluster):
        if not isinstance(cluster, Cluster):
            raise TypeError(f'Expect {Cluster}, received {cluster}')
        self._cluster = cluster
    
    @property
    def slope(self):
        if self.effects_type is Effects.Fixed:
            return 1.0
        elif self.effects_type is Effects.Random:
            raise NotImplementedError()
            # return  self.cluster.property_alpha.value / self.cluster.property_beta.value
    
    @property
    def intercept(self):
        if self.effects_type is Effects.Fixed:
            return self.cluster.property_alpha.value
        elif self.effects_type is Effects.Random:
            raise NotImplementedError()
    
        
    def time_series(self, start_year, end_year, treatment_year=None):
        if treatment_year is None:
            treatment_year = end_year - (end_year-start_year)//2
        time = pd.Index(range(start_year, end_year), name='Year')
        index = pd.MultiIndex.from_product(
            [
                time
            ]
            + [
                pd.Index([getattr(self.cluster, prop).name], name=prop)
                for prop in self.cluster
            ]
            )
        time_series = pd.DataFrame(
            {
                'Post': (time>=treatment_year),
                'Treatment': (time>=treatment_year) & self.cluster.property_dummy.value,
                'Slope': self.slope,
                'Intercept': self.intercept,
                'FixedEffectIndividual': self._get_individual_fixed_effect(),
                'FixedEffectTime': self._get_time_fixed_effect(size=index.shape[0])
            },
            index=index,
            )
        time_series['Dependent'] = time_series.Slope.multiply(
                time_series.Treatment
            ).add(
                time_series.Intercept
            ).add(
                time_series.FixedEffectIndividual
            ).add(
                time_series.FixedEffectTime
            )
        
        if self.noise.value:
            time_series['Dependent'] += self._get_noise(
                size=time_series.shape[0]
                )
            
        time_series.set_index(
             ['Post', 'Treatment'],
             append=True,
             inplace=True
             )
        return time_series
    
    def _get_individual_fixed_effect(self):
        # rng_max = self.cluster.property_alpha.value
        # rng_min = rng_max - 1
        rng_max = 1
        rng_min = -1
        np.random.seed(seed=self.identifier)
        return np.random.uniform(
            low=rng_min,
            high=rng_max,
            )
    
    def _get_time_fixed_effect(self, size):
        rng = 1.0
        np.random.seed(0)
        data = np.random.uniform(
            low=-rng,
            high=rng,
            size=size
            )
        data.sort()
        return data[::-1]
    
    def _get_noise(self, size, scale=0.1):
        rng = self.slope*scale
        np.random.seed(2*self.identifier)
        return np.random.uniform(
            low=-rng,
            high=rng,
            size=size
            )
        
#%% sample
class Sample():
    
    def __init__(
            self,
            start_year,
            end_year,
            treatment_year=None,
            effects=Effects.Fixed,
            noise=Noise.FALSE
            ):
        self._init_clusters()
        self._init_individuals(
            effects=effects,
            noise=noise
            )
        self._init_sample(
            start_year=start_year,
            end_year=end_year,
            treatment_year=treatment_year
            )
    
    def _init_clusters(self):
        seed_clusters = [
            Cluster(PropertyAlpha.A, PropertyBeta.B, PropertyDummy.TRUE),
            Cluster(PropertyAlpha.A, PropertyBeta.A, PropertyDummy.TRUE),
            Cluster(PropertyAlpha.B, PropertyBeta.A, PropertyDummy.FALSE)
            ]
        np.random.seed(10)
        repeats = np.random.randint(
            low=3,
            high=10,
            size=len(seed_clusters)
            )
        repeats.sort()
        self._clusters = np.repeat(seed_clusters, repeats)
        
    
    def _init_individuals(self, effects, noise):
        self._individuals = [
            Individual(identifier=i, cluster=cluster, effects=effects, noise=noise)
            for i, cluster in enumerate(self.clusters)
            ]
    
    def _init_sample(self, start_year, end_year, treatment_year=None):
        sample = pd.concat(
            {
                individual.identifier: individual.time_series(
                    start_year=start_year,
                    end_year=end_year
                    )
                for individual in self.individuals
            },
            names=['Individual'],
            axis=0
            )
        sample.columns.name = 'Variable'
        self._data = sample
    
    @property
    def clusters(self):
        return self._clusters
    
    @property
    def individuals(self):
        return self._individuals
    
    @property
    def data(self):
        return self._data
    
#%% main
if __name__=='__main__':
    import os
    import plotly.express as px
    output_path = r'/Users/leonardstimpfle/Documents/code/leostimpfle.github.io/_includes/2024-02-10-fixed_effects'
    start_year = 2013
    end_year = 2022
    treatment_year=2017
    effects = Effects.Fixed
    noise = Noise.TRUE
    sample = Sample(
        start_year=start_year,
        end_year=end_year,
        treatment_year=treatment_year,
        effects=effects,
        noise=noise
        )
    
    #%% plot sample
    fig = px.line(
        sample.data.reset_index(),
        x='Year',
        y='Dependent',
        color='property_dummy',
        # line_dash='Individual',
        line_group='Individual',
        markers=True,
        title='Synthetic Sample'
        )
    # fig.update_layout(hovermode='x')
    fig.add_vline(
        treatment_year,
        name='Treatment',
        line=dict(dash='dot')
        )
    fig.write_html(os.path.join(output_path, 'sample.html'))
    
    #%% POLS
    fig_box1 = px.box(
        sample.data.reset_index(),
        color='Treatment',
        # x='property_dummy',
        y='Dependent',
        points='all',
        title='The impact of treatment on the dependent variable...'
        )
    fig_box1.update_traces(boxmean=True)
    fig_box1.write_html(os.path.join(output_path, 'box1.html'))

    fig_box2 = px.box(
        sample.data.reset_index(),
        color='Treatment',
        x='property_alpha',
        y='Dependent',
        points='all',
        title='...is biased by unobserved heterogeneity.'
        )
    fig_box2.update_traces(boxmean=True)
    fig_box2.write_html(os.path.join(output_path, 'box2.html'))
    
    #%% individual fixed effects
    mean_individual = sample.data.Dependent.groupby('Individual').mean()
    mean_time = sample.data.Dependent.groupby('Year').mean()
    mean = sample.data.Dependent.mean()
    sample_individual = sample.data.Dependent.subtract(
            mean_individual
        )
    sample_time = sample.data.Dependent.subtract(
            mean_time
        )
    sample_twfe = sample.data.Dependent.subtract(
            mean_individual
        ).subtract(
            mean_time
        ).subtract(
            mean    
        )
    tmp = pd.concat(
        {
            'raw': sample.data.Dependent,
            'individual': sample_individual,
            'time': sample_time,
            'two-way': sample_twfe
        },
        axis=0,
        names=['Fixed Effects']
        )
    fig = px.line(
        tmp.reset_index(),
        x='Year',
        y='Dependent',
        color='property_dummy',
        line_group='Individual',
        markers=True,
        title='Transformation of Synthetic Sample',
        facet_row='Fixed Effects',
        height=800
        )
    # fig.update_layout(hovermode='x')
    fig.update_yaxes(matches=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.write_html(os.path.join(output_path, 'sample_fe.html'))
        