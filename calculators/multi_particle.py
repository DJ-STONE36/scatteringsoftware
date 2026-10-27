import numpy as np
from scipy.special import gamma, polygamma
from scipy.optimize import fsolve
from PyMieScatt import MieQ
#from pyindexrepo import RefractiveIndexLibrary

# 初始化库
#_LIB = RefractiveIndexLibrary()
#_WATER = _LIB.get_material('main', 'H2O', 'Segelstein')  # 液态水
#_ICE   = _LIB.get_material('main', 'H2O', 'Warren-1984')   # 固态冰

# 粒子模型基类及子类（RainModel, FogModel, HazeModel, SnowModel）保持原样，
# 但这里将代码整理在同一个模块中，并提供一个计算函数。

class ParticleModel:
    """所有粒子模型的基类，只保留波长和可选 DD"""
    def __init__(self, wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk):
        self.wavelength = wavelength_um * 1e-6   # 米
        self.wavelength_um = wavelength_um     # 微米
        self.DD = DD_um * 1e-6                   # 几何平均直径 (m)
        self.DD_um = DD_um
        self.N0_m3 = N0_cm3 * 1e6              # 总粒子数浓度 (m⁻³)
        self.N0_cm3 = N0_cm3
        self.sigma_g = sigma_g                # 几何标准偏差
        self.n = nn                            # 折射率实部
        self.k = kk                            # 折射率虚部 (非负)
    
    def size_distribution(self, radius):
        raise NotImplementedError

    def scattering_coefficients(self):
        """
        计算并返回消光系数、散射系数、吸收系数、不对称因子
        参数:
            DD : 粒子直径 (m)
            nn : 复折射率实部
            kk : 复折射率虚部（非负值）
        返回:
            dict: 'extinction', 'scattering', 'absorption', 'asymmetry' (m⁻¹)
        """
            # ---------- 粒径网格（对数均匀，覆盖大部分粒子）----------
        rg = self.DD / 2.0
        r_min = rg * 0.1           # 覆盖0.1倍到10倍几何平均半径
        r_max = rg * 10.0
        radius_grid = np.logspace(np.log10(r_min), np.log10(r_max), 600)

        # 直接使用 nn, kk 构造复折射率
        m = complex(self.n, self.k)

        # 数组存储微分贡献
        ext_arr = np.zeros_like(radius_grid)
        sca_arr = np.zeros_like(radius_grid)
        asym_num_arr = np.zeros_like(radius_grid)

        for i, r in enumerate(radius_grid):
            nr = self.size_distribution(r)
            if nr <= 0:
                continue
            D = 2.0 * r
            cext, csca, _, g, *_ = MieQ(
                m, self.wavelength, D,
                nMedium=1.0, asDict=False, asCrossSection=True
            )
            ext_arr[i] = nr * cext
            sca_arr[i] = nr * csca
            asym_num_arr[i] = nr * csca * g

        # 数值积分
        dr = np.gradient(radius_grid)
        ext_coeff = np.sum(ext_arr * dr)
        sca_coeff = np.sum(sca_arr * dr)
        asym = (np.sum(asym_num_arr * dr) / sca_coeff) if sca_coeff > 0 else 0.0

        return {
            'extinction': ext_coeff,
            'scattering': sca_coeff,
            'absorption': ext_coeff - sca_coeff,
            'asymmetry': asym
        }


class RainModel(ParticleModel):
    def __init__(self, wavelength_um, DD_um, N0_cm3, sigma_g=None, nn=1.33, kk=0.01):
        super().__init__(wavelength_um, DD_um, N0_cm3,
                         sigma_g if sigma_g is not None else 1.4, nn, kk)
        # DD 已经存为 self.DD (米)，转为毫米
        D_mm = self.DD * 1000.0          # m → mm
        self.Lambda = np.log(2) / D_mm   # mm⁻¹
        # 截距参数，单位 m⁻³·mm⁻¹
        self.N0_exp = self.N0_m3 * self.Lambda

    def size_distribution(self, radius):
        D_mm = radius * 2000.0           # m → mm
        if D_mm <= 0 or self.Lambda <= 0:
            return 0.0
        # N0_exp * exp(-Λ D) * dD/dr，dD/dr = 2000 mm/m
        return self.N0_exp * np.exp(-self.Lambda * D_mm) * 2000.0

class FogModel(ParticleModel):
    def __init__(self, wavelength_um, DD_um, N0_cm3, sigma_g=None, nn=1.33, kk=0.01):
        super().__init__(wavelength_um, DD_um, N0_cm3,
                         sigma_g if sigma_g is not None else 1.4, nn, kk)
        
        if self.sigma_g <= 1.0:
            raise ValueError("sigma_g 必须大于 1")

        # 从 sigma_g 求解形状参数 mu（不变）
        #def equation(mu):
        #    return np.exp(np.sqrt(polygamma(1, mu + 1))) - self.sigma_g
        #self.mu = fsolve(equation, 2.0)[0]
        
        self.mu = sigma_g
        # 有效半径 (m)
        self.reff = self.DD / 2.0
        # 斜率参数 (m⁻¹)
        self.Lambda = (self.mu + 3) / self.reff
        # 截距参数（由总浓度 N0_m3 归一化）
        self.N0_w = (self.N0_m3 * (self.Lambda ** (self.mu + 1))
                     / gamma(self.mu + 1))

    def size_distribution(self, radius):
        if radius <= 0:
            return 0.0
        return self.N0_w * (radius ** self.mu) * np.exp(-self.Lambda * radius)
    
class HazeModel(ParticleModel):
    def __init__(self, wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk, rh=None):
        # 吸湿增长：干直径 → 湿直径
        if rh is not None:
            if rh < 60:
                growth = 1.0
            elif rh < 80:
                growth = 1.2
            elif rh < 95:
                growth = 1.5
            else:
                growth = 2.0
            wet_DD_um = DD_um * growth
        else:
            wet_DD_um = DD_um
        super().__init__(wavelength_um, wet_DD_um, N0_cm3, sigma_g, nn, kk)
        self.rh = rh
        self.dry_DD_um = DD_um

    def size_distribution(self, radius):
        if radius <= 0:
            return 0.0
        rg = self.DD / 2.0          # 几何平均半径 (米)
        if self.sigma_g <= 0:
            raise ValueError("sigma_g must be > 0")
        ln_sigma = np.log(self.sigma_g)
        norm = self.N0_m3 / (np.sqrt(2 * np.pi) * ln_sigma)
        return (norm / radius) * np.exp(
            -0.5 * (np.log(radius / rg) / ln_sigma) ** 2
        )
    
class SnowModel(ParticleModel):
    def __init__(self, wavelength_um, DD_um, N0_cm3, sigma_g=None, nn=1.33, kk=0.01):
        super().__init__(wavelength_um, DD_um, N0_cm3,
                         sigma_g if sigma_g is not None else 1.4, nn, kk)
        D_mm = self.DD * 1000.0
        self.Lambda = np.log(2) / D_mm
        self.N0_exp = self.N0_m3 * self.Lambda

    def size_distribution(self, radius):
        D_mm = radius * 2000.0
        if D_mm <= 0 or self.Lambda <= 0:
            return 0.0
        return self.N0_exp * np.exp(-self.Lambda * D_mm) * 2000.0

def compute_multi_particle(wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk, 
                           rain_rate=None, visibility_km=None,
                           rh_percent=None, snow_rate=None):
    """
    计算多种粒子混合的散射系数
    输入:
        wavelength_um : 波长 (μm)
        DD, nn, kk    : 粒子直径 (m)、折射率实部、虚部
        rain_rate, visibility_km, rh_percent, snow_rate : 各模型强度参数
    返回:
        dict: extinction, scattering, absorption, asymmetry (m⁻¹)
    """

    models = []
    if rain_rate is not None and rain_rate > 0:
        models.append(RainModel(wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk))
    if visibility_km is not None and visibility_km > 0:
        #visibility_m = visibility_km * 1000.0
        models.append(FogModel(wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk))
    if rh_percent is not None and 0 < rh_percent <= 100:
        models.append(HazeModel(wavelength_um, DD_um, N0_cm3, sigma_g, 
                                nn, kk, rh=rh_percent,))
    if snow_rate is not None and snow_rate > 0:
        models.append(SnowModel(wavelength_um, DD_um, N0_cm3, sigma_g, nn, kk))

    total_ext = total_sca = total_abs = weighted_asym = 0.0
    for model in models:
        # 使用统一的 DD, nn, kk 调用散射系数计算
        res = model.scattering_coefficients()
        total_ext += res['extinction']
        total_sca += res['scattering']
        total_abs += res['absorption']
        weighted_asym += res['scattering'] * res['asymmetry']

    asym = weighted_asym / total_sca if total_sca > 0 else 0.0
    return {
        'extinction': total_ext,
        'scattering': total_sca,
        'absorption': total_abs,
        'asymmetry': asym
    }
