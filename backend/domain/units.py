"""Переведення одиниць до системних: креатинін — мкмоль/л, гемоглобін — г/л."""

UMOL_L_PER_MG_DL = 88.4
G_L_PER_G_DL = 10


def creatinine_mg_dl_to_umol_l(creatinine_mg_dl: float) -> float:
    return creatinine_mg_dl * UMOL_L_PER_MG_DL


def creatinine_umol_l_to_mg_dl(creatinine_umol_l: float) -> float:
    return creatinine_umol_l / UMOL_L_PER_MG_DL


def hemoglobin_g_dl_to_g_l(hemoglobin_g_dl: float) -> float:
    return hemoglobin_g_dl * G_L_PER_G_DL
