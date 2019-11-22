#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from .utils import to_list
from pathlib import Path

ROOT = str(Path(__file__).parent.parent.parent.absolute())
IMDB_MOVIES_PICLE = ROOT + '/data/imdb_movies.pkl'
IMDB_COVERS_PICLE = ROOT + '/data/imdb_covers.pkl'
IMDB_TITLE_GZIP = 'https://datasets.imdbws.com/title.basics.tsv.gz'
IMDB_RATING_GZIP = 'https://datasets.imdbws.com/title.ratings.tsv.gz'
IMDB_COVERS_CSV = ROOT + '/data_static/movie_covers.csv'


class Imdb(object):

    def __init__(self):

        imdb_covers = pd.read_pickle(IMDB_COVERS_PICLE)

        imdb = pd.read_pickle(IMDB_MOVIES_PICLE)
        imdb = imdb.dropna(subset=['startYear', 'originalTitle'])
        imdb = imdb[imdb['titleType']=='movie']

        # imdb_covers['tconst'] = 'tt' + imdb_covers['imdbId'].astype(str)
        # imdb = pd.merge(imdb, imdb_covers, how='left', on='tconst')

        self.imdb = imdb

    @staticmethod
    def prepare():
        pd.merge(
            pd.read_csv(IMDB_TITLE_GZIP, sep='\t'),
            pd.read_csv(IMDB_RATING_GZIP, sep='\t'),
            how='left',
            on='tconst').to_pickle(IMDB_MOVIES_PICLE)
        pd.read_csv(IMDB_COVERS_CSV).to_pickle(IMDB_COVERS_PICLE)

    @staticmethod
    def get_similarity(row):
        text_list_eng = to_list(row['genre_eng'])
        text_list_genres = to_list(row['genres'])
        # product of those lists
        commons = set(text_list_eng) & set(text_list_genres)
        return len(commons)

    @staticmethod
    def change_type(t):
        match = {
            'akcja': 'action',
            'dramat': 'drama',
            'animowany': 'cartoon',
            'romans': 'romance',
            'drogi': 'road',
            'biograficzny': 'biographic',
            'romantyczny': 'romantic',
            'wojenny': 'war',
            'katastroficzny': 'disaster',
            'kryminał': 'crime',
            'komedia': 'comedy',
            'dokumentalny': 'documentary',
            'pełnometrażowy': 'full-length',
            'krótkometrażowy': 'short',
            'niemy': 'silent',
            'historyczny': 'historical',
            'edukacyjny': 'educational',
            'kostiumowy': 'costume',
            'obyczajowy': 'drama'
        }
        arr = [match[s.lower()] if s.lower() in match else s.lower() for s in to_list(t)]
        return ", ".join(arr)

    def merge(self, df):
        df['originalTitle'] = df['Tytuł oryginalny']
        df['startYear'] = df['Rok produkcji'].astype(str)
        df['originalTitle'] = df['originalTitle'].fillna(df['Tytuł polski'])

        df['Gatunek'] = df['Gatunek'].fillna('')
        df['startYear'] = df['startYear'].astype(float).fillna(0).astype(int).astype(str)

        df['genre_eng'] = df.apply(lambda x: self.change_type(x['Gatunek']), axis=1)

        merged = pd.merge(
            df,
            self.imdb,
            how='inner',
            on=['startYear','originalTitle'])

        merged['similarity'] = merged.apply(self.get_similarity, axis=1)

        top1 = merged.groupby(['ID']).apply(lambda x: x.sort_values(["similarity"], ascending = False)).reset_index(drop=True)
        merged = top1.groupby('ID').head(1).copy()

        merged[['averageRating']] = merged[['averageRating']].fillna(value=0)
        merged[['averageRating_int']]  = merged[['averageRating']].round().astype(int)

        return merged
