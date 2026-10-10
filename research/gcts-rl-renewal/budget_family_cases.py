"""Disjoint statement-only donors/training and shared evaluation controls."""
from quantifier_family_cases import case
from dependency_budget_cases import registry as previous


def registry():
    donors=[case('quantifier-donor-budget-one'),
            case('quantifier-donor-budget-two',hops=2),
            case('quantifier-donor-budget-three',hops=3)]
    training=[case('budget-family-train-one'),
              case('budget-family-train-ground-two',hops=2,ground=True),
              case('budget-family-train-compound-two',hops=2,compound=True),
              case('budget-family-train-three',hops=3),
              case('budget-family-train-missing',missing=True)]
    prior=previous()
    evaluation=[prior[i] for i in (0,3,7,9,10,11,12,13)]
    return donors,training,evaluation
