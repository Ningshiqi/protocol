import numpy as np
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class RandomSplit(object):

    def __init__(self,
                 df,
                 sub_sample,
                 num_iter,
                 col_name='Tumor_Sample',
                 with_replacement=False):
        self.df = df
        self.set_sub_sample(sub_sample)
        self.set_num_iter(num_iter)
        self.with_replacement = with_replacement
        self.COLUMN_NAME = col_name
        drop_dups = self.df.copy()[['Tumor_Sample', 'Tumor_Type']].drop_duplicates()
        self.sample_names = drop_dups.set_index('Tumor_Sample').groupby('Tumor_Type').groups
        self.num_sample_names = len(self.sample_names)
        self.colname2ix = self.df.groupby(self.COLUMN_NAME).groups

    def dataframe_generator(self):
        """Generate subsampled data frames according to the sub_sample
        and num_iter arguments. The tumor type composition is respect, i.e.
        the relative amount of each tumor type for a specific sample will
        always reflect the relative amount in aggregate.
        """
        #n = int(self.sub_sample * self.total_count)  # number of counts to sample

        for i in range(self.num_iter):
            logger.info('Mutation split: Iteration={1} . . .'.format(self.sub_sample, i))
            left_samples = []
            right_samples = []

            # randomly split sample names while respecting tumor type
            # composition
            prng = np.random.RandomState()
            for tmp_ttype, tmp_samples in self.sample_names.iteritems():
                tmp_num_samps = len(tmp_samples)
                if not self.with_replacement:
                    # sample with out replacement
                    prng.shuffle(tmp_samples)  # shuffle order of samples
                    split_pos = int(tmp_num_samps*self.sub_sample)
                    tmp_left = tmp_samples[:split_pos]
                    tmp_right = tmp_samples[split_pos:]
                else:
                    # sample with replacement
                    tmp_num_samps = int(tmp_num_samps*self.sub_sample)
                    tmp_left = prng.choice(tmp_samples, tmp_num_samps, replace=True)
                    tmp_right = prng.choice(tmp_samples, tmp_num_samps, replace=True)
                left_samples += tmp_left
                right_samples += tmp_right

            # get data frame split
            if not self.with_replacement:
                # simple sample without replacment case
                left_df = self.df[self.df[self.COLUMN_NAME].isin(left_samples)].copy()
                right_df = self.df[self.df[self.COLUMN_NAME].isin(right_samples)].copy()
            else:
                # sample with replacement case
                # count occurrences of samples
                left_cts = Counter(left_samples)
                right_cts = Counter(right_samples)

                # identify data frame indices for samples
                left_ixs, right_ixs = [], []
                left_names, right_names = [], []
                for cname in left_cts:
                    for k in range(left_cts[cname]):
                        left_names += [cname + '.{0}'.format(k)
                                       for _ in range(len(self.colname2ix[cname]))]
                        left_ixs += self.colname2ix[cname]
                for cname in right_cts:
                    for k in range(right_cts[cname]):
                        right_names += [cname + '.{0}'.format(k)
                                        for _ in range(len(self.colname2ix[cname]))]
                        right_ixs += self.colname2ix[cname]

                # get samples from original data frame
                left_df = self.df.ix[left_ixs,:].copy()
                right_df = self.df.ix[right_ixs,:].copy()
                left_df[self.COLUMN_NAME] = left_names
                right_df[self.COLUMN_NAME] = right_names

            logger.info('Finished mutation split: Iteration={1}'.format(self.sub_sample, i))
            yield left_df, right_df

    def set_sub_sample(self, sub_sample):
        """Set the fraction of the original total mutations to actually sample.

        Sampling is done without replacement.

        Parameters
        ----------
        sub_sample : float
            0 < sub_sample <= 1.0
        """
        if 0 <= sub_sample <= 1:
            self.sub_sample = sub_sample
        else:
            raise ValueError('Subsample should be between zero and one.')

    def set_num_iter(self, num_iter):
        """Set number of times to sample w/o replacement.

        Parameters
        ----------
        num_iter : int
            do sample w/o replacement, num_iter number of times
        """
        if iter > 0:
            self.num_iter = num_iter
        else:
            raise ValueError('Number of iterations should be positive.')
