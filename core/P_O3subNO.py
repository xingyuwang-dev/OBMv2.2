# 该脚本是RIR模块计算有关数据的核心脚本
# 用来计算臭氧生成速率，臭氧消耗速率，当model为False时候计算OH反应活性
# 其中k为反应速率，里面的数字为对应反应的位置


def P_O3subNO(result, model=False):
    Conc = {i: float(j) for i, j in result["Conc"].items()}
    k = result["Chem"]["k"][0]
    M = float(result["Met"]["M"]) * 1e-9

    R1 = Conc["HO2"] * Conc["NO"] * 3600 * M * k[29]  # R1:HO2+NO  R2:XO2+NO MEO2+NO TO2+NO 表示RO2与NO的反应
    R2 = (Conc["XO2"] * k[53] + Conc["XO2N"] * k[54] + Conc["MEO2"] * k[66] + Conc["TO2"] * k[128]) * Conc[
        "NO"] * 3600 * M

    R3 = Conc["O1D"] * 3600 * k[10]  # 臭氧光解反应
    R4 = Conc["O3"] * Conc["OH"] * k[11] * 3600 * M  # O3+OH
    R5 = Conc["O3"] * Conc["HO2"] * k[12] * 3600 * M  # O3+HO2
    R6 = Conc["NO2"] * Conc["OH"] * k[27] * 3600 * M  # NO2+OH  # IOLE+O3 OLE+O3 ETH+O3 ISOP+O3 TERP+O3 表明烯烃与O3反应
    R7 = (Conc["IOLE"] * k[125] + Conc["OLE"] * k[117] + Conc["ETH"] * k[121] + Conc["ISOP"] * k[142] + Conc["TERP"] *
          k[150]) * \
         Conc["O3"] * 3600 * M

    R_of_O3 = R1 + R2
    D_of_O3 = -R3 - R4 - R5 - R6 - R7
    component = [R1, R2, -R3, -R4, -R5, -R6, -R7]

    if model:
        OH1 = Conc["SO2"] * k[152] * M  # SO2与OH的反应活性  # 芳香烃与OH反应活性
        OH2 = (Conc["XYL"] * k[137] + Conc["TOL"] * k[127] + Conc["MGLY"] * k[138] + Conc["OPEN"] * k[135]) * M
        OH3 = Conc["PAR"] * k[111] * M  # 烷烃与OH反应活性  # 烯烃与OH反应活性
        OH4 = (Conc["IOLE"] * k[124] + Conc["OLE"] * k[116] + Conc["ETH"] * k[120] + Conc["ISOP"] * k[141] + Conc[
            "TERP"] * k[149]) * M
        OH5 = Conc["NO2"] * k[27] * M  # NO2与OH反应活性
        OH6 = Conc["HNO3"] * k[28] * M  # HNO3与OH反应活性
        OH7 = Conc["NO"] * k[23] * M  # NO与OH反应活性
        OH8 = Conc["PNA"] * k[32] * M  # PNA与OH反应活性
        OH9 = Conc["HONO"] * k[25] * M  # HONO与OH反应活性
        OH10 = Conc["HO2"] * k[42] * M  # HO2与OH反应活性
        OH11 = Conc["CO"] * k[64] * M  # CO与OH反应活性
        OH12 = Conc["CH4"] * k[65] * M  # CH4与OH反应活性  # OVOCs与OH反应活性
        OH13 = (Conc["ALD2"] * k[83] + Conc["ETOH"] * k[153] + Conc["ALDX"] * k[98] + Conc["FORM"] * k[72] + Conc[
            "MEOH"] * k[71] +
                Conc["FACD"] * k[81] + Conc["ROOH"] * k[62] + Conc["AACD"] * k[96] + Conc["PACD"] * k[94] + Conc[
                    "CRES"] * k[130]) * M

        OH = [OH1, OH2, OH3, OH4, OH5, OH6, OH7, OH8, OH9, OH10, OH11, OH12, OH13]
        return R_of_O3, D_of_O3, component, OH

    return R_of_O3, D_of_O3, component
