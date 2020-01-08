from surprise.model_selection import train_test_split
from surprise.model_selection import LeaveOneOut
from surprise import KNNBaseline
from surprise import Dataset, KNNBasic
from surprise import Reader

from movies_analyzer.Movies import Movies, RATINGS, LINKS, MOVIES
from movies_recommender.utils import get_popularity_ranking
import pandas as pd


class RecommendationDataSet:
    def __init__(self, movies: Movies):
        # train_test_split(dataset, test_size=test_size, random_state=1)
        self.movies = movies
        self.dataset_df = pd.read_csv(movies.movielens_path / RATINGS)

        reader = Reader(line_format='user item rating timestamp', sep=',', skip_lines=1)
        """
        line_format - list of columns
        sep - separator for csv file
        skip_lines - start from the second line
        """
        self.dataset = Dataset.load_from_file(self.movies.movielens_path / RATINGS, reader=reader)
        self.full_dataset = self.dataset.build_full_trainset()

        # ranking
        self.ratings, self.rankings = get_popularity_ranking(self.full_dataset)

        # TRAINING
        self.train_set, self.test_set = None, None
        self.anti_test_set = None
        self.leave_one_out_train_set = None
        self.leave_one_out_test_set = None
        self.leave_one_out_anti_test_set = None
        self.similarity_algorithm = None

    def get_dataset_with_extended_user(self, moviescore_df, columns):
        """
            Create new dataset with new user, based only on the score of current movies.
        :param
        """
        df = moviescore_df[columns].copy()
        df.rename(columns={
            columns[0]: 'movieId',
            columns[1]: 'rating'
        }, inplace=True)
        new_user_id = max(self.dataset_df['userId']) + 1
        df['userId'] = new_user_id
        df['timestamp'] = 0
        rating_df = self.dataset_df.append(df, ignore_index=True, sort=False)
        reader = Reader(rating_scale=(1, 5))
        dataset = Dataset.load_from_df(rating_df[['userId', 'movieId', 'rating']], reader)
        return new_user_id, dataset

    def build_train_test(self, test_size=.25):
        # Train Set, Test Set to test results
        self.train_set, self.test_set = train_test_split(self.dataset, test_size=test_size, random_state=1)

        # https://surprise.readthedocs.io/en/stable/trainset.html#surprise.Trainset.build_anti_testset
        # Situation when the user u is known, the item is known, but the rating is not in the trainset
        self.anti_test_set = self.full_dataset.build_anti_testset()

        # Cross-validation iterator where each user has exactly one rating in the testset.
        leave_one_out_set = LeaveOneOut(n_splits=1, random_state=1)
        loo_train_set, loo_test_set = list(leave_one_out_set.split(self.dataset))[0]

        self.leave_one_out_train_set = loo_train_set
        self.leave_one_out_test_set = loo_test_set
        self.leave_one_out_anti_test_set = loo_train_set.build_anti_testset()

        # Compute similarity matrix between items so we can measure diversity
        sim_options = {'name': 'cosine', 'user_based': False}
        self.similarity_algorithm = KNNBaseline(sim_options=sim_options)
        self.similarity_algorithm.fit(self.full_dataset)
