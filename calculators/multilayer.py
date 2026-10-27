import numpy as np
import scattnlay

def compute_multilayer_spectrum(layers_params, wavelengths, medium_n=1.0):
    """
    计算多层球的光谱效率因子
    layers_params: 列表，每个元素为 {'radius': 半径(m), 'm': 复折射率(相对环境)}
    wavelengths: 波长数组 (nm)
    返回: Qext, Qsca, Qabs 数组
    """
    Qext_list, Qsca_list, Qabs_list = [], [], []
    for wl in wavelengths:
        x_list = []
        m_list = []
        k = 2 * np.pi / (wl * 1e-9)
        for layer in layers_params:
            x = k * layer['radius']
            m_rel = layer['m'] / medium_n
            x_list.append(x)
            m_list.append(m_rel)
        x_array = np.array(x_list)
        m_array = np.array(m_list)
        terms, Qext, Qsca, Qabs, Qbk, Qpr, g, Albedo, S1, S2 = scattnlay.scattnlay(
            x_array, m_array, theta=np.array([0]), nmax=-1
        )
        Qext_list.append(Qext[0] if isinstance(Qext, np.ndarray) else Qext)
        Qsca_list.append(Qsca[0] if isinstance(Qsca, np.ndarray) else Qsca)
        Qabs_list.append(Qabs[0] if isinstance(Qabs, np.ndarray) else Qabs)
    return np.array(Qext_list), np.array(Qsca_list), np.array(Qabs_list)

def compute_multilayer_angular(layers_params, wavelength, medium_n=1.0):
    """
    计算特定波长下的散射角分布
    返回: theta_deg, I_parallel, I_perpendicular, I_unpolarized, Qext, Qsca, Qabs, g
    """
    theta_deg = np.linspace(0, 180, 181)
    theta_rad = np.radians(theta_deg)
    x_list, m_list = [], []
    k = 2 * np.pi / (wavelength * 1e-9)
    for layer in layers_params:
        x = k * layer['radius']
        m_rel = layer['m'] / medium_n
        x_list.append(x)
        m_list.append(m_rel)
    x_array = np.array(x_list)
    m_array = np.array(m_list)
    terms, Qext, Qsca, Qabs, Qbk, Qpr, g, Albedo, S1, S2 = scattnlay.scattnlay(
        x_array, m_array, theta=theta_rad, nmax=-1
    )
    I_parallel = np.abs(S1[0])**2 if S1.ndim > 1 else np.abs(S1)**2
    I_perpendicular = np.abs(S2[0])**2 if S2.ndim > 1 else np.abs(S2)**2
    I_unpolarized = (I_parallel + I_perpendicular) / 2
    Qext_val = Qext[0] if isinstance(Qext, np.ndarray) else Qext
    Qsca_val = Qsca[0] if isinstance(Qsca, np.ndarray) else Qsca
    Qabs_val = Qabs[0] if isinstance(Qabs, np.ndarray) else Qabs
    g_val = g[0] if isinstance(g, np.ndarray) else g
    return theta_deg, I_parallel, I_perpendicular, I_unpolarized, Qext_val, Qsca_val, Qabs_val, g_val