import os
import sys
sys.path.append(".")
import pandas as pd
import numpy as np
import statistics as stats


class CTRHelper:

    def __init__(self, df, impression_column, click_column) -> None:
        self.df = df
        self.impression_column = impression_column
        self.click_column = click_column
    
    def _calc_ctr_raw(self):
        self.df = self.df.copy()
        self.df["ctr_raw"] = self.df[self.click_column] / self.df[self.impression_column]

    def _calc_mean_and_var(self, df):
        self.mean_ctr = stats.mean(df["ctr_raw"])
        self.var_ctr = stats.variance(df["ctr_raw"])
        self.stdev_ctr = stats.stdev(df["ctr_raw"])

    def _seperate_dataframe_by_click(self):
        # seperate dataframe with click(> 0) and nonclick
        click_df = self.df[self.df[self.click_column] > 0]
        nonclick_df = self.df[self.df[self.click_column] == 0]
        return click_df, nonclick_df

    def regularize(self):
        self._calc_ctr_raw()
        click_df, nonclick_df = self._seperate_dataframe_by_click()
        # NOTE: zero click인 문서는 0.0으로 변경하고 정규화에 참여하지 않도록 한다.
        self._calc_mean_and_var(click_df)
        click_df, nonclick_df = self.by_beta_distribution(click_df, nonclick_df)
        click_df, nonclick_df = self.by_gaussian_distribution(click_df, nonclick_df)
        # concat (by index) and reorder
        df = pd.concat([click_df, nonclick_df], axis=0).sort_values(["search_keyword"])
        df = self.by_modify_factor(df)
        return df

    def by_modify_factor(self, df):
        df = df.copy()
        df["mctr"] = (df[self.click_column] + 1) / (df[self.impression_column] + 99)
        return df

    # def by_modify_factor_small(self, df):
    #     def _modify(row):
    #         if row[self.click_column] > 10:
    #     df = df.copy()
    #     df["mctr"] = (df[self.click_column] + 1) / (df[self.impression_column] + 99)
    #     return df
            
    def by_beta_distribution(self, click_df, nonclick_df):
        """ estimate alpha, beta parameter by using sample distribution
        https://stats.stackexchange.com/a/12239 

        assume sample data distribution can be explained by beta distribution
        TODO: fit test: https://en.wikipedia.org/wiki/Kolmogorov–Smirnov_test
        """
        # calculate sum(alpha, beta)
        alpha_beta = (self.mean_ctr * (1 - self.mean_ctr) / self.var_ctr) - 1
        # calculate alpha
        alpha = self.mean_ctr * alpha_beta
        # calculate beta
        beta = (1 - self.mean_ctr) * alpha_beta
        # calulate expected CTR
        expected_ctr_beta = alpha / (alpha + beta)
        # adjust ctr
        # TODO: 여긴 잘 이해가 안됨
        # TODO: alpha, beta가 일종의 조정 factor로 쓰이는 것 같은데, 둘다 형상모수에 해당함
        click_df = click_df.copy()
        nonclick_df = nonclick_df.copy()
        click_df["ctr_beta"] = (alpha + click_df[self.click_column]) / (alpha + beta + click_df[self.impression_column])
        nonclick_df["ctr_beta"] = [0.0] * len(nonclick_df)
        # for access
        self.alpha = alpha
        self.beta = beta
        self.alpha_beta = alpha_beta
        self.expected_ctr_beta = expected_ctr_beta
        return click_df, nonclick_df

    def by_gaussian_distribution(self, click_df, nonclick_df):
        click_df = click_df.copy()
        nonclick_df = nonclick_df.copy()
        click_df["ctr_gaussian"] = (click_df["ctr_raw"] - self.mean_ctr) / self.stdev_ctr
        nonclick_df["ctr_gaussian"] = (nonclick_df["ctr_raw"] - self.mean_ctr) / self.stdev_ctr
        return click_df, nonclick_df


class ClickModels:
    pass


if __name__ == "__main__":
    print("todo")