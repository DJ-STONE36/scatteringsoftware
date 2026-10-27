import numpy as np
import PyMieScatt as ps
import matplotlib.pyplot as plt

def compute_efficiency(m, wavelength, diameter):
    """
    计算球形粒子的效率因子
    参数：
        m: 复折射率 (complex)
        wavelength: 波长 (m)
        diameter: 直径 (m)
    返回：
        Qext, Qsca, Qabs, g (不对称因子)
    """
    Qext, Qsca, Qabs, g, Qpr, Qback, Qratio = ps.MieQ(m, wavelength, diameter, asDict=False)
    return Qext, Qsca, Qabs, g

def compute_scattering_function(m, wavelength, diameter):
    """
    计算散射强度角分布
    返回：
        theta (弧度), SL, SR, SU
    """
    theta, SL, SR, SU = ps.ScatteringFunction(m, wavelength, diameter)
    return theta, SL, SR, SU