# function Sout=CheckStructure(Sin,FieldInfo,ignorePrefix)
# Checks the fields in a structure for the following:
# 1) all fields in the structure are valid
# 2) any required fields (based on the application) are present
# 3) assignment of default values if needed
# If tests 1 or 2 fail, an error is returned
#
# INPUTS:
# Sin: a structure containing fields to check
# FieldInfo: A cell array containing info for all fields
# Has three columns, with one row for each field to check:
# 1) Names: strings containing all valid field names:
# 2) Required/Optional: Flag for whether variable is required (1) or optional (0)
# 3) Default Values: Default values for any optional fields.
# ignorePrefix: optional input specifying a prefix for ignored fields
# any fileds in Sin starting with this prefix will not be sujected to checks


# 该脚本用来判断输入Dict是否满足默认Dict2的格式，如果不满足则进行修改


def CheckDict(Dict, Dict2, *ignorePrefix):
    # input:
    # Dict={'':,}
    # Dict2={'':,}
    # ignorePrefic={'',}

    # output:
    # Dict_new={'':,}

    Sfields = Dict.keys()  # 提取字典Dict的键
    ValidFields = Dict2.keys()  # 提取字典Dict2的键
    Required = [i[0] for i in
                Dict2.values()]  # after Python3.6, the read order is same as input order, keys' order is same as values'
    # Defaults = [i[1] for i in Dict2.values()]
    #  这里需要提出一个值得注意的点就是，在python版本3.6之后，字典dict是默认有序的，即创建的顺序与提取顺序一致，key的顺序与value顺序一致

    if len(ignorePrefix) != 0:  # ignore fields if desired
        Sfields = [item for item in Sfields if ignorePrefix[0] not in item]

    if not set(Sfields).issubset(set(ValidFields)):  # check for valid fields
        sec = set(Sfields).difference(set(ValidFields))
        raise KeyError(
            'CheckDict: Key(s) {0} in dict {1} not valid, valid keys are: {2}.'.format(sec, Sfields, ValidFields))

    RequiredFields = [i for i, j in zip(ValidFields, Required) if j == 1]  # check for required fields
    if len(RequiredFields) != 0:
        if not set(RequiredFields).issubset(set(Sfields)):
            sec = set(RequiredFields).difference(set(Sfields))
            raise KeyError('CheckDic: Required Key(s) {0} in dict {1} not found, required keys are: ' +
                           '{2}.'.format(sec, Sfields, ValidFields))

    OptionalFields = [i for i, j in zip(ValidFields, Required) if j == 0]  # assign default
    # Defaults = [i for i, j in zip(Defaults, Required) if j == 0]
    check = [i for i in OptionalFields if i not in Sfields]
    Dict.update({i: Dict2[i][1] for i in check})

    return Dict
