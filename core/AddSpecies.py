# 该脚本根据原有m文件改写，主要作用是添加新的物种名称到Cnames中，添加新的RO2名称到RO2names中


# Add species to Cnames and RO2name


def AddSpecies(SpeciesToAdd: list, Cnames=None, RO2names=None, *RO2ToAdd):
    # input:
    # SpeciesToAdd=['',]
    # RO2ToAdd=['',]
    # Cnames=['',]
    # RO2names=['',]

    # output:
    # Cnames_new=['',]
    # RO2names_new=['',]
    # fstr=['',]
    # f_dict={'':,}
    if Cnames is None:
        Cnames = []
    if RO2names is None:
        RO2names = []

    Cnames.extend([SpNow for SpNow in SpeciesToAdd if SpNow not in Cnames])
    # fstr=fstr.extend([f"{i}" for i in Cnames])
    # len_of_sparse=len(Cnames)

    if len(RO2ToAdd) != 0:
        RO2ToAdd = RO2ToAdd[0]
        RO2names += [SpNow for SpNow in RO2ToAdd if SpNow not in RO2names]

    return Cnames, RO2names
