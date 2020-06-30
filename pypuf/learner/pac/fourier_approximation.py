"""
This module contains the Low Degree Algorithm.
"""
from itertools import combinations

import numpy as np
from scipy.special import comb as ncr

from pypuf import tools
from pypuf.learner.base import Learner
from pypuf.simulation.fourier_based.fourier_expansion import FourierExpansionSign, FourierCoefficient


class FourierCoefficientApproximation(Learner):
    """
    Probabilistic algorithm to create a model of a Boolean function using a `training_set`. It approximates
    all Fourier coefficients listed in the `chi_set` parameter. If the training_set has size `get_training_set_size`
    and the function is epsilon/2-concentrated on the monomials given in `chi_set`, the algorithm returns a model that
    with probability 1-`delta` has accuracy 1-`epsilon`.
    """

    def __init__(self, training_set, chi_set, debug=False):
        """
        :param training_set: pypuf.tools.TrainingSet
                             The trainings set generated by tools.TrainingSet
        :param degree: int
                       The degree up to which the Fourier coefficients are approximated
        :param debug: boolean
                      If true, a progress message with ETA will be periodically printed to stdout
        """
        self.training_set = training_set
        self.n = len(training_set.challenges[0])
        self.monomial_count = len(chi_set)
        self.fourier_coefficients = []
        self.chi_set = chi_set
        self.debug = debug

    @staticmethod
    def get_training_set_size(epsilon, delta, chi_set_size=0):
        """
        This function calculates the training set size that is needed to satisfy the theoretical requirements of the
        Low Degree Algorithm such that the compliance of the epsilon and delta parameters is guaranteed.
        :param n: int
                  Input length
        :param chi_set_size: int
                       The number of Fourier coefficients to be approximated.
        :param epsilon: float
                        The maximum error rate of the model
        :param delta: float
                      The maximum failure rate of the algorithm, where epsilon is not satisfied
        :return:
        """
        return int((4 * chi_set_size * np.log(2 * chi_set_size / delta) / epsilon) + 1)

    def learn(self):
        """
        Compute a model according to the given training set.
        Note that this function can take long to return.
        :return: The computed model.
        """
        self.fourier_coefficients = [self.approx_fourier_coefficient(chi) for chi in self.chi_set]
        return FourierExpansionSign(self.fourier_coefficients)

    def approx_fourier_coefficient(self, subset):
        """
        Approximate the Fourier coefficient of the function on `subset`
        :param subset: list of int
                       A {0,1}-array indicating the coefficient's index set
        :param block: int Index of the training set partition to use.

        :return float
                The approximated value of the coefficient
        """
        return FourierCoefficient(subset, tools.approx_fourier_coefficient(subset, self.training_set))


class LowDegreeAlgorithm(FourierCoefficientApproximation):
    """
    Probabilistic algorithm to create a model of a Boolean function using a `training_set`. It approximates
    all Fourier coefficients of degree up to `degree`. If the training_set has size `get_training_set_size`
    and the function is epsilon/2-concentrated up to degree `degree` the algorithm returns a model that with
    probability 1-`delta` has accuracy 1-`epsilon`.
    """

    def __init__(self, training_set, degree, debug=False):
        _, n = training_set.challenges.shape
        super().__init__(training_set, self.low_degree_chi(n, degree), debug)

    @staticmethod
    def low_degree_chi(n, degree):
        """
        Returns an iterator for the sets s (represented as {0,1}-arrays that represent monomials with degree exactly
        `degree`.
        :param degree: n Challenge-length.
        :param degree: int
                       The desired degree of the subsets
        :return iterator of arrays of length n
        """
        return np.array([
            [1 if i in indices else 0 for i in range(n)]
            for indices in combinations(range(n), degree)
        ], dtype=tools.BIT_TYPE)

    @staticmethod
    def get_training_set_size(epsilon, delta, n=0, degree=0):
        return FourierCoefficientApproximation.get_training_set_size(
            epsilon=epsilon,
            delta=delta,
            chi_set_size=sum([ncr(n, k) for k in range(degree + 1)]),
        )