from pandas import to_numeric, Series
from numpy import array
from CB05.CB05_transfrom import transfrom


# 此是用来处理RIR模块的数据
# 和EKMA模块下处理数据的部分一致


tem_summer = array([26.1, 26, 25.9, 25.4, 25, 25.1, 25.2, 25.9, 27.7, 28.4, 28.7, 28.2,
                    28, 26.2, 26.7, 27.3, 27.4, 27.2, 26.6, 26.6, 26.4, 26.5, 26.5, 26.5])
tem_winter = array([6.7, 6.4, 6.1, 5.7, 6, 5.9, 5.6, 6.1, 6.5, 7, 7.3, 7.6,
                    7.7, 8, 8.3, 8.5, 8.6, 8.2, 8, 7.7, 7.6, 7.6, 7.6, 7.1])
hum_summer = array([95.2, 93.1, 93.3, 94.2, 95.6, 96.7, 99.2, 95.1, 81.3, 78.5, 77, 79.5,
                    81.3, 95.1, 94.4, 90.6, 90.8, 90.4, 94.2, 96.8, 99.4, 99.8, 98.6, 98])
hum_winter = array([74.7, 76.4, 76.8, 77.3, 75.6, 73.6, 75.6, 72.6, 70.1, 69.1, 68.6, 65.2,
                    66.2, 64.6, 61.6, 59.7, 59.8, 61.5, 64.2, 65.9, 66.9, 68.6, 69.3, 71.2])
threshold = {"C5H8": 5, "HCHO": 50, "CH3CHO": 50, "CH3CL": 10, "VINCL": 10, "CH2CL2": 10, "CH2CLCHCL2": 10,
             "CHCL2CHCL2": 10}


def data_processed(data, compound_name, arg):
    P, T, H = arg
    comparison_dict = {compound_name.iloc[i, 0]: compound_name.iloc[i, 1] for i in range(compound_name.shape[0])}
    data = data.apply(to_numeric, errors="coerce")
    data = transfrom(data)
    data.dropna(how="all", axis=1, inplace=True)
    drop_columns = list(set(data.columns) - set(comparison_dict.keys()))
    data.drop(drop_columns, axis=1, inplace=True)
    data.rename(columns={i: comparison_dict[i] for i in data.columns}, inplace=True)

    data_time = data.index.to_list()
    YEAR = int(data_time[0][:4])
    MONTH = int(data_time[0][5:7])
    DAY = int(data_time[0][8:10])
    HOUR = [int(i[-5:-3]) for i in data_time]
    data.set_index(Series(HOUR), inplace=True)
    if data.shape[0] > 1:
        HOUR_lost = list(set(range(24)) - set(HOUR))
        for i in HOUR_lost:
            data.loc[i] = float("nan")
        data.sort_index(inplace=True)
    M, N = data.shape
    data.interpolate(limit_direction="both", inplace=True)
    data[data < 0] = 0
    #toppb = {"NO": 1.339, "NO2": 2.054, "O3": 2.143, "CO": 0.00125, "SO2": 3.392}
    #toppb_name = set(toppb.keys()) & set(data.columns)
    #for name in toppb_name:
    #    data[name] = data[name] / toppb[name]
    HOUR = data.index.to_list()

    #extra rule
    for i in data.columns:
        if i not in threshold.keys() and i not in {"NO", "NO2", "O3", "CO", "T", "P", "H", "PAR", "NR"}:
            data.loc[data[i] > 30, i] = 30
        elif i in threshold.keys():
            data.loc[data[i] > threshold[i], i] = threshold[i]

    #extra rule2
    PRESSURE = [1001]*M
    if 6 < MONTH <= 10:
        TEMPERATURE = tem_summer[HOUR]
        HUMIDITY = hum_summer[HOUR]
    elif MONTH < 3 or MONTH > 11:
        TEMPERATURE = tem_winter[HOUR]
        HUMIDITY = hum_winter[HOUR]
    else:
        TEMPERATURE = [(i+j)/2 for i, j in zip(tem_summer[HOUR], tem_winter[HOUR])]
        HUMIDITY = [(i+j)/2 for i, j in zip(hum_summer[HOUR], hum_winter[HOUR])]
    if "T" in data.columns:
        TEMPERATURE = data["T"].tolist() if T == -1 else [T]*M
    if "P" in data.columns:
        PRESSURE = (data["P"]*10).tolist() if P == -1 else [P]*M
    if "H" in data.columns:
        HUMIDITY = data["H"].tolist() if H == -1 else [H]*M

    #CB05 model
    """
    columns_set = set(data.columns)
    iole = {"CPENT2ENE", "TBUT2ENE", "CBUT2ENE", "TPENT2ENE"} & columns_set
    ole = {"PENT1ENE", "C3H6", "HEX1ENE", "C4H6", "STYRENE", "C5H8", "BUT1ENE"} & columns_set
    tol = {"TOLUENE", "EBENZ", "IPBENZ", "PBENZ"} & columns_set
    xyl = {"OXYL", "PETHTOL", "METHTOL", "TM124B", "OETHTOL", "TM135B", "TM123B", "PXYL", "MXYL"} & columns_set
    mgly = {"BENZAL", "MACR"} & columns_set
    aldx = {"ACR", "BENZAL", "MACR", "C3H7CHO", "C4H9CHO", "C4ALDB", "C2H5CHO", "MXYLAL"} & columns_set
    par = columns_set - (iole | ole | tol | xyl | mgly | aldx | {"SO2", "O3", "CO", "NO", "NO2", "NO3", "HONO",
                                                                 "CH4", "HCHO", "HCOOH", "C2H2", "C2H4", "T", "P", "H"})
    etha, ispd, eth, isop, ald2, etoh, meoh, form = {"C2H6"} & columns_set, {"MACR"} & columns_set, {"C2H4"} & columns_set, \
    {"C5H8"} & columns_set, {"CH3CHO"} & columns_set, {"C2H5OH"} & columns_set, {"CH3OH"} & columns_set, {"HCHO"} & columns_set
    #RO2: XO2 XO2N MEO2 TO2
    CB05_species = ["IOLE", "OLE", "TOL", "XYL", "MGLY", "ALDX", "PAR",
                    "ETHA", "ISPD", "ETH", "ISOP", "ALD2", "ETOH", "MEOH", "FORM"]
    CB05_species_set = [iole, ole, tol, xyl, mgly, aldx, par, etha,
                        ispd, eth, isop, ald2, etoh, meoh, form]
    for i, j in zip(CB05_species, CB05_species_set):
        data[i] = data[list(j)].sum(axis=1)
    """

    time = {"Y": YEAR, "M": MONTH, "D": DAY, "H": HOUR}
    climate = {"T": TEMPERATURE, "H": HUMIDITY, "P": PRESSURE}

    return data, time, climate