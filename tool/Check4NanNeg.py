from numpy import isnan, array, ndarray
from warnings import warn


# function S=Check4NanNeg(S,pickOne)
# Checks variables in a structure S for NaNs and negative values
# If any are found, it returns an error
# optional input "pickOne" can be set to "nan" or "neg" to only check for one of these
# Also forces all non-character fields in the structure to be column vectors


# 该脚本主要用于判断输入参数S中是否有nan与neg，nan：not a number, neg: negative负数


def Check4NanNeg(S, *pickOne):
    # input:
    # S={'',}
    # pickOne='nan' or 'neg'

    # output:
    # S_new={'',}

    Snames = S.keys()

    if len(pickOne) != 0:
        pickOne = str(pickOne).lower()
        if pickOne == 'nan':
            NAN = 1
            NEG = 0
        elif pickOne == 'neg':
            NAN = 0
            NEG = 1
        else:
            NAN = 1
            NEG = 1
            warn('Check4NanNeg: InvalidOption, pickOne input not recongnized. Will screen for both Nan and Neg.',
                 Warning)
    else:
        NAN = 1
        NEG = 1

    for i in Snames:
        if isinstance(S[i], (list, ndarray)):  # 如果S的元素类型为列表或numpy数组：ndarray
            if NAN and any(isnan(S[i])):  # 如果NAN为1，且S中包含了任意数量nan
                raise ValueError('nan found in variable {0}.'.format(i))
            elif NEG and any(array(S[i]) < 0):  # 如果NEG为1，且S中包含了任意数量neg
                raise ValueError("negative found in variable {0}.".format(i))
            # if all(S[i]):
            #   raise ValueError('[]s in variable {0}.'.format(Snames))
        elif isinstance(S[i], (int, float)):  # 如果S的元素为整型int或浮点型float
            if NAN and isnan(S[i]):
                raise ValueError("NaN in variable {0}.".format(Snames))
            elif NEG and S[i] < 0:
                raise ValueError('Negative values in variable {0}.'.format(Snames))
        elif isinstance(S[i], str) and i != 'SavePath':  # 如果S的元素类型为字符串str
            raise ValueError('String found in variable {0}.'.format(Snames))
    # S = {i: array(j).reshape(-1, 1) for i, j in S.items()}

    return S
