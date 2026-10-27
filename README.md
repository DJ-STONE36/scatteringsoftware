# 大气光散射特性仿真与可视化软件

基于 **PyQt5 + Matplotlib** 的大气粒子光散射仿真与可视化工具，集成了 Mie 理论、T 矩阵方法、多层球精确解以及雨/雾/霾/雪多粒子系综模型，可在图形界面中完成参数输入、数值计算、曲线绘制与结果展示。

> 本项目为本科毕业设计《大气光散射特性仿真与可视化软件的设计与实现》的配套软件代码。

## 功能特性

| 模块 | 物理模型 | 计算方法 | 输出 |
| --- | --- | --- | --- |
| 球形单粒子 | 均匀球形粒子 | Mie 理论（`PyMieScatt`） | 效率因子 $Q_\text{ext}, Q_\text{sca}, Q_\text{abs}$、不对称因子 $g$、散射强度函数 $S_L, S_R, S_U \sim \theta$ |
| 椭球形单粒子 | 均匀椭球（可调纵横比） | T 矩阵方法（`scatterpy`） | S 矩阵、Z 矩阵、极化散射强度角分布，支持取向平均（均匀 / 高斯 PDF） |
| 多层球 | 同心多层球 | `scattnlay` 精确解 | 光谱效率因子 $Q(\lambda)$、极坐标散射强度角分布 |
| 多粒子 | 雨 / 雾 / 霾 / 雪 | 粒径分布 + Mie 单次散射 | 消光、散射、吸收系数（m⁻¹）、不对称因子、$\mathrm{d}N/\mathrm{d}r$ 谱图 |

界面采用左右分栏布局：左侧为四个参数标签页，右侧同步显示数值结果与图像，图像在 Matplotlib 画布中绘制，可随窗口缩放。

### 各标签页说明

- **球形单粒子**：输入复折射率 $m=a+b\mathrm{j}$、波长（μm）、直径（μm），可分别计算效率因子或绘制散射强度角分布。
- **椭球形单粒子**：输入直径、波长、折射率、纵横比、入射/散射方向（天顶角与方位角），可计算 S 矩阵、S+Z 矩阵或扫描 0.1°–180° 绘制平行/垂直/非极化散射强度；支持取向平均与高斯展宽、方位角离散点数、自动调优相对容差 `rtol`。
- **多层球**：可动态添加/删除同心层（半径、折射率实部与虚部），设置环境介质折射率与波长范围，同时输出光谱曲线与中间波长的极坐标角分布。
- **多粒子**：设置激光波长、有效直径、总粒子数浓度 $N_0$、形状参数 $\mu$ 与复折射率，勾选雨（mm/h）、雾（能见度 km）、霾（相对湿度 %）、雪（mm/h）后计算混合散射特性，并可叠加绘制各模型的粒径分布谱图。

## 环境要求

- Python 3.9+（开发环境为 Python 3.12）
- Windows / Linux / macOS（开发环境为 Windows）

### 依赖安装

```bash
pip install -r requirements.txt
```

| 依赖 | 用途 |
| --- | --- |
| `numpy`、`scipy` | 数值计算、特殊函数 |
| `matplotlib` | 绘图与 PyQt5 画布嵌入 |
| `PyQt5` | 图形界面 |
| `PyMieScatt` | 球形粒子 Mie 理论 |
| `scattnlay` | 多层球精确解 |
| `scatterpy` | 椭球 T 矩阵方法 |

## 运行

```bash
python main.py
```

启动后将打开主窗口，默认参数可直接点击各标签页的「计算 / 绘制」按钮查看结果。

## 目录结构

```
scatteringsoftware/
├── main.py                     # 程序入口
├── main_windows.py             # 主窗口及各标签页界面与事件响应
├── calculators/
│   ├── __init__.py
│   ├── sphere_single.py        # 球形单粒子：Mie 效率因子与散射强度函数
│   ├── spheroid_single.py      # 椭球单粒子：T 矩阵、S/Z 矩阵与角分布
│   ├── multilayer.py           # 多层球：光谱与角分布
│   └── multi_particle.py       # 雨/雾/霾/雪粒径分布与混合散射系数
├── requirements.txt
└── README.md
```

## 模型说明（简要）

### 球形单粒子（Mie 理论）

由 Mie 级数求得消光、散射、吸收效率因子与不对称因子：

$$
Q_\text{ext}=\frac{2}{x^2}\sum_{n=1}^{\infty}(2n+1)\,\mathrm{Re}(a_n+b_n),\qquad
Q_\text{sca}=\frac{2}{x^2}\sum_{n=1}^{\infty}(2n+1)\left(|a_n|^2+|b_n|^2\right)
$$

其中尺度参数 $x=\pi d/\lambda$，$a_n,b_n$ 为 Mie 系数。

### 椭球形单粒子（T 矩阵）

先由 `calc_T` 求 T 矩阵，再由 `calc_S` 求散射振幅矩阵：

$$
\begin{pmatrix} S_1 & S_3 \\ S_4 & S_2 \end{pmatrix}
= \frac{2\pi}{k}\sum_{n}\sum_{m}\alpha_{mn}\left[\cdots\right]
$$

取向平均时对取向角按给定概率密度函数（均匀或高斯）积分，得到平均 S 矩阵，进而计算 Z 矩阵（Mueller 矩阵）。

### 多层球

对每一层使用相对折射率 $m_j$ 与尺度参数 $x_j = 2\pi r_j/\lambda$，按 `scattnlay` 的递归算法求各阶散射系数，累加得到 $Q_\text{ext}, Q_\text{sca}, Q_\text{abs}$ 及角分布。

### 多粒子系综

对不同水凝物采用不同粒径分布：

- 雨、雪：指数分布 $n(D)=N_0\Lambda e^{-\Lambda D}$，$\Lambda=\ln 2 / D_0$
- 雾：Gamma 分布 $n(r)=N_0\frac{\Lambda^{\mu+1}}{\Gamma(\mu+1)}r^{\mu}e^{-\Lambda r}$
- 霾：对数正态分布，并按相对湿度进行吸湿增长修正

对各分布积分 $\int Q_\text{ext}(D)\,\frac{\pi D^2}{4}\,n(D)\,\mathrm{d}D$ 得到宏观消光、散射与吸收系数，并按散射权重合成不对称因子。

## 说明

- 界面设置中文字体为 `Times New Roman` + `SimHei`，非中文系统请自行调整 `main_windows.py` 中的 `plt.rcParams['font.family']`。
- 椭球 T 矩阵计算量较大，参数较大时需等待数秒。

## 许可

本项目采用 MIT License。
