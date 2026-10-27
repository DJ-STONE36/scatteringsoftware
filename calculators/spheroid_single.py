import numpy as np
from scatterpy import calc_T, calc_S, calc_Z
from scatterpy.orientation import calc_S_oa, sph_uniform_pdf, sph_gauss_pdf
from scatterpy import shapes

def compute_spheroid_T(D, wavelength, n_real, n_imag, aspect_ratio=1.0,
                       n_maxorder=70, n_gauss=140):
    """计算椭球粒子的 T 矩阵"""
    D = np.atleast_1d(D)
    wavelength = np.atleast_1d(wavelength)
    mr = np.atleast_1d(n_real + 1j * n_imag)
    ar = np.atleast_1d(aspect_ratio)
    shape_func = lambda D: shapes.spheroid(ar)
    T = calc_T(D, wavelength, mr, sfunc=shape_func, n_maxorder=n_maxorder, n_gauss=n_gauss)
    return T

def compute_spheroid_S(T, theta0_deg, theta_deg, phi0_deg, phi_deg,
                       alpha_deg=0.0, beta_deg=0.0, orientation_avg=False,
                       pdf_type="uniform", std_deg=0.0, n_alpha=5):
    """计算 S 矩阵（支持取向平均）"""
    theta0 = np.deg2rad(theta0_deg)
    theta  = np.deg2rad(theta_deg)
    phi0   = np.deg2rad(phi0_deg)
    phi    = np.deg2rad(phi_deg)
    alpha  = np.deg2rad(alpha_deg)
    beta   = np.deg2rad(beta_deg)

    if orientation_avg:
        if pdf_type == "gaussian":
            pdf = sph_gauss_pdf(std=np.deg2rad(std_deg))
        else:
            pdf = sph_uniform_pdf()
        S = calc_S_oa(T, theta0, theta, phi0, phi, pdf, n_alpha=n_alpha)
    else:
        S = calc_S(T, theta0, theta, phi0, phi, alpha, beta)
    return S

def compute_spheroid_Z(S):
    """从 S 矩阵计算 Z 矩阵"""
    return calc_Z(S)