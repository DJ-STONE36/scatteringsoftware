import sys
import traceback
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QLineEdit, QPushButton, QTabWidget,
                             QTextEdit, QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                             QComboBox, QSplitter,QMessageBox)
from PyQt5.QtCore import Qt

# 导入计算模块
from calculators import sphere_single
from calculators import spheroid_single
from calculators import multilayer
from calculators import multi_particle

# 设置中文字体
plt.rcParams['font.family'] = ['Times New Roman', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({'font.size': 24})          # 全局字体大小
plt.rcParams.update({'legend.fontsize': 24})    # 图例字体大小


class MplCanvas(FigureCanvas):
    """用于在 PyQt 中嵌入 matplotlib 图形"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("大气光散射特性仿真与可视化软件的设计与实现")
        self.setGeometry(100, 100, 2400, 1400)

        # 主分割器：左右分栏
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # 左侧：参数输入区（带四个标签页）
        self.left_widget = QWidget()
        left_layout = QVBoxLayout(self.left_widget)
        self.tab_widget = QTabWidget()
        left_layout.addWidget(self.tab_widget)

        self.init_sphere_tab()
        self.init_spheroid_tab()
        self.init_multilayer_tab()
        self.init_multiparticle_tab()

        self.tab_widget.setStyleSheet("QTabBar::tab { font-size: 9pt; }")

        main_splitter.addWidget(self.left_widget)

        # 右侧：结果输出区（文本+图像）
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        right_layout.addWidget(self.output_text, 1)  # 文本区域占1份
        self.canvas = MplCanvas(self, width=5, height=4)
        right_layout.addWidget(self.canvas, 3)       # 图形区域占2份
        main_splitter.addWidget(self.right_widget)

        main_splitter.setSizes([500, 1500])

    # ================== 球形单粒子标签页 ==================
    def init_sphere_tab(self):
        tab = QWidget()
        tab.setStyleSheet("font-size: 12pt;")
        layout = QGridLayout(tab)
        row = 0

        # 复折射率 m
        layout.addWidget(QLabel("复折射率 m (a+bj):"), row, 0)
        self.sphere_m_edit = QLineEdit("1.5+0.01j")
        layout.addWidget(self.sphere_m_edit, row, 1)
        row += 1

        # 波长 (μm)
        layout.addWidget(QLabel("波长 λ (μm):"), row, 0)
        self.sphere_wl_edit = QLineEdit("0.532")
        layout.addWidget(self.sphere_wl_edit, row, 1)
        row += 1

        # 直径 (μm)
        layout.addWidget(QLabel("直径 d (μm):"), row, 0)
        self.sphere_d_edit = QLineEdit("2.0")
        layout.addWidget(self.sphere_d_edit, row, 1)
        row += 1

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_params = QPushButton("参数计算")
        btn_params.clicked.connect(self.on_sphere_params)
        btn_plot = QPushButton("散射强度函数绘制")
        btn_plot.clicked.connect(self.on_sphere_plot)
        btn_layout.addWidget(btn_params)
        btn_layout.addWidget(btn_plot)
        layout.addLayout(btn_layout, row, 0, 1, 2)
        row += 1

        layout.setRowStretch(row, 1)
        self.tab_widget.addTab(tab, "球形单粒子")

    def on_sphere_params(self):
        try:
            m_str = self.sphere_m_edit.text().replace('j', 'j')
            m = complex(m_str)
            wl_um = float(self.sphere_wl_edit.text())
            d_um = float(self.sphere_d_edit.text())
            wavelength = wl_um * 1e-6
            diameter = d_um * 1e-6
            Qext, Qsca, Qabs, g = sphere_single.compute_efficiency(m, wavelength, diameter)
            text = f"消光效率 Qext: {Qext:.4f}\n散射效率 Qsca: {Qsca:.4f}\n吸收效率 Qabs: {Qabs:.4f}\n不对称因子 g: {g:.4f}"
            
            font = self.output_text.font()
            font.setPointSize(12)      # 根据需要调整数值，例如 14、16 等
            self.output_text.setFont(font)

            self.output_text.setPlainText(text)
            self.canvas.fig.clear()
            self.canvas.draw()
        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

    def on_sphere_plot(self):
        try:
            m_str = self.sphere_m_edit.text().replace('j', 'j')
            m = complex(m_str)
            wl_um = float(self.sphere_wl_edit.text())
            d_um = float(self.sphere_d_edit.text())
            wavelength = wl_um * 1e-6
            diameter = d_um * 1e-6
            theta, SL, SR, SU = sphere_single.compute_scattering_function(m, wavelength, diameter)

            self.canvas.fig.clear()
            ax = self.canvas.fig.add_subplot(111)
            ax.semilogy(theta, SL, 'b', ls='dashdot', lw=1, label="平行极化")
            ax.semilogy(theta, SR, 'r', ls='dashed', lw=1, label="垂直极化")
            ax.semilogy(theta, SU, 'k', lw=1, label="非极化")
            ax.set_xlabel("散射角 θ (rad)")
            ax.set_ylabel("强度 |S|²")
            ax.set_title(f'球形粒子散射强度 (D={d_um}µm, λ={wl_um}µm, m={m})')
            ax.legend()
            ax.grid(True, alpha=0.3)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
            #self.output_text.setPlainText("散射强度函数图已绘制。")
        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

    # ================== 椭球形单粒子标签页 ==================
    def init_spheroid_tab(self):
        tab = QWidget()
        tab.setStyleSheet("font-size: 12pt;")
        layout = QGridLayout(tab)
        row = 0

        # 粒子参数组
        group_particle = QGroupBox("粒子参数")
        glayout = QGridLayout()
        glayout.addWidget(QLabel("直径 D (μm):"), 0, 0)
        self.sph_D_edit = QLineEdit("10.0")
        glayout.addWidget(self.sph_D_edit, 0, 1)
        glayout.addWidget(QLabel("波长 λ (μm):"), 1, 0)
        self.sph_wl_edit = QLineEdit("0.55")
        glayout.addWidget(self.sph_wl_edit, 1, 1)
        glayout.addWidget(QLabel("折射率实部 n:"), 2, 0)
        self.sph_n_edit = QLineEdit("1.33")
        glayout.addWidget(self.sph_n_edit, 2, 1)
        glayout.addWidget(QLabel("折射率虚部 k:"), 3, 0)
        self.sph_k_edit = QLineEdit("0.0")
        glayout.addWidget(self.sph_k_edit, 3, 1)
        glayout.addWidget(QLabel("纵横比 (a/c):"), 4, 0)
        self.sph_ar_edit = QLineEdit("1.2")
        glayout.addWidget(self.sph_ar_edit, 4, 1)
        group_particle.setLayout(glayout)
        layout.addWidget(group_particle, row, 0, 1, 2)
        row += 1

        # 散射方向组
        group_dir = QGroupBox("散射方向")
        dlayout = QGridLayout()
        dlayout.addWidget(QLabel("入射天顶角 θ₀ (°):"), 0, 0)
        self.sph_theta0_edit = QLineEdit("45")
        dlayout.addWidget(self.sph_theta0_edit, 0, 1)
        dlayout.addWidget(QLabel("入射方位角 φ₀ (°):"), 0, 2)
        self.sph_phi0_edit = QLineEdit("0")
        dlayout.addWidget(self.sph_phi0_edit, 0, 3)
        dlayout.addWidget(QLabel("散射天顶角 θ (°):"), 1, 0)
        self.sph_theta_edit = QLineEdit("60")
        dlayout.addWidget(self.sph_theta_edit, 1, 1)
        dlayout.addWidget(QLabel("散射方位角 φ (°):"), 1, 2)
        self.sph_phi_edit = QLineEdit("30")
        dlayout.addWidget(self.sph_phi_edit, 1, 3)
        group_dir.setLayout(dlayout)
        layout.addWidget(group_dir, row, 0, 1, 2)
        row += 1

        # 取向平均组
        group_orient = QGroupBox("取向平均")
        olayout = QGridLayout()
        self.sph_orient_check = QCheckBox("启用取向平均")
        olayout.addWidget(self.sph_orient_check, 0, 0, 1, 2)
        olayout.addWidget(QLabel("PDF 类型:"), 1, 0)
        self.sph_pdf_combo = QComboBox()
        self.sph_pdf_combo.addItems(["uniform", "gaussian"])
        olayout.addWidget(self.sph_pdf_combo, 1, 1)
        olayout.addWidget(QLabel("高斯标准差 (°):"), 2, 0)
        self.sph_std_edit = QLineEdit("10")
        olayout.addWidget(self.sph_std_edit, 2, 1)
        olayout.addWidget(QLabel("方位角离散点数:"), 3, 0)
        self.sph_nalpha_spin = QSpinBox()
        self.sph_nalpha_spin.setRange(1, 20)
        self.sph_nalpha_spin.setValue(5)
        olayout.addWidget(self.sph_nalpha_spin, 3, 1)
        group_orient.setLayout(olayout)
        layout.addWidget(group_orient, row, 0, 1, 2)
        row += 1

        # 自动调优组
        group_tune = QGroupBox("自动调优")
        tlayout = QGridLayout()
        self.sph_tune_check = QCheckBox("启用自动调优")
        tlayout.addWidget(self.sph_tune_check, 0, 0)
        tlayout.addWidget(QLabel("相对容差 rtol:"), 1, 0)
        self.sph_rtol_edit = QLineEdit("1e-4")
        tlayout.addWidget(self.sph_rtol_edit, 1, 1)
        group_tune.setLayout(tlayout)
        layout.addWidget(group_tune, row, 0, 1, 2)
        row += 1

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_S = QPushButton("计算 S 矩阵")
        btn_S.clicked.connect(self.on_spheroid_S)
        btn_SZ = QPushButton("计算 S+Z 矩阵")
        btn_SZ.clicked.connect(self.on_spheroid_SZ)
        btn_plot = QPushButton("绘制散射强度")
        btn_plot.clicked.connect(self.on_spheroid_plot)
        btn_layout.addWidget(btn_S)
        btn_layout.addWidget(btn_SZ)
        btn_layout.addWidget(btn_plot)
        layout.addLayout(btn_layout, row, 0, 1, 2)
        row += 1

        layout.setRowStretch(row, 1)
        self.tab_widget.addTab(tab, "椭球形单粒子")

    def _get_spheroid_params(self):
        D = float(self.sph_D_edit.text()) * 1e-6
        wl = float(self.sph_wl_edit.text()) * 1e-6
        n = float(self.sph_n_edit.text())
        k = float(self.sph_k_edit.text())
        ar = float(self.sph_ar_edit.text())
        theta0 = float(self.sph_theta0_edit.text())
        theta = float(self.sph_theta_edit.text())
        phi0 = float(self.sph_phi0_edit.text())
        phi = float(self.sph_phi_edit.text())
        orient_avg = self.sph_orient_check.isChecked()
        pdf_type = self.sph_pdf_combo.currentText()
        std_deg = float(self.sph_std_edit.text()) if pdf_type == "gaussian" else 0.0
        n_alpha = self.sph_nalpha_spin.value()
        rtol = float(self.sph_rtol_edit.text()) if self.sph_tune_check.isChecked() else 1e-4
        return D, wl, n, k, ar, theta0, theta, phi0, phi, orient_avg, pdf_type, std_deg, n_alpha, rtol

    def on_spheroid_S(self):
        try:
            params = self._get_spheroid_params()
            D, wl, n, k, ar, theta0, theta, phi0, phi, orient_avg, pdf_type, std_deg, n_alpha, rtol = params
            # 计算 T
            T = spheroid_single.compute_spheroid_T(D, wl, n, k, ar, n_maxorder=70, n_gauss=140)
            # 计算 S
            S = spheroid_single.compute_spheroid_S(T, theta0, theta, phi0, phi, 0, 0,
                                                   orient_avg, pdf_type, std_deg, n_alpha)
            
            font = self.output_text.font()
            font.setPointSize(12)      # 根据需要调整数值，例如 14、16 等
            self.output_text.setFont(font)
            
            self.output_text.setPlainText(f"S 矩阵:\n{np.array2string(S, precision=4, suppress_small=True)}")
            self.canvas.fig.clear()
            self.canvas.draw()
        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

    def on_spheroid_SZ(self):
        try:
            params = self._get_spheroid_params()
            D, wl, n, k, ar, theta0, theta, phi0, phi, orient_avg, pdf_type, std_deg, n_alpha, rtol = params
            T = spheroid_single.compute_spheroid_T(D, wl, n, k, ar, n_maxorder=70, n_gauss=140)
            S = spheroid_single.compute_spheroid_S(T, theta0, theta, phi0, phi, 0, 0,
                                                   orient_avg, pdf_type, std_deg, n_alpha)
            Z = spheroid_single.compute_spheroid_Z(S)
            
            font = self.output_text.font()
            font.setPointSize(12)      # 根据需要调整数值，例如 14、16 等
            self.output_text.setFont(font)

            self.output_text.setPlainText(f"S 矩阵:\n{np.array2string(S, precision=4)}\n\nZ 矩阵（实部）:\n{np.array2string(np.real(Z), precision=4)}")
            self.canvas.fig.clear()
            self.canvas.draw()
        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")     
        
    def on_spheroid_plot(self):
        """计算散射强度随散射角的变化并绘图"""
        try:
            # 读取参数（忽略散射天顶角输入值，使用扫描范围）
            D, wl, n, k, ar, theta0, _, phi0, phi, orient_avg, pdf_type, std_deg, n_alpha, rtol = self._get_spheroid_params()

            # 角度扫描：散射天顶角 0.1° ~ 180°，固定散射方位角
            theta_scan = np.linspace(0.1, 180.0, 360)
            phi_scan = np.full_like(theta_scan, phi)  # 使用界面中设置的散射方位角

            # 计算 T 矩阵
            T = spheroid_single.compute_spheroid_T(D, wl, n, k, ar)
            # 计算 S 矩阵（取向平均可启用）
            S = spheroid_single.compute_spheroid_S(T, theta0, theta_scan, phi0, phi_scan, 0, 0,
                                   orient_avg, pdf_type, std_deg, n_alpha)

            # 提取散射振幅元素
            S11 = S[..., 0, 0]
            S12 = S[..., 0, 1]
            S21 = S[..., 1, 0]
            S22 = S[..., 1, 1]

            # 极化散射强度（与第一个代码一致）
            I_par = np.abs(S11)**2 + np.abs(S21)**2
            I_per = np.abs(S12)**2 + np.abs(S22)**2
            I_unpol = (I_par + I_per) / 2.0

            # 绘图
            self.canvas.fig.clear()
            ax = self.canvas.fig.add_subplot(111)
            ax.plot(theta_scan, I_per, color='red', label='垂直极化')
            ax.plot(theta_scan, I_par, color='blue', label='平行极化')
            ax.plot(theta_scan, I_unpol, color='black', label='非极化')
            ax.set_xlabel('散射角 (度)')
            ax.set_ylabel('散射强度 (相对值)')
            ax.set_title(f'椭球散射强度 (D={D/1e-6}µm, λ={wl/1e-6}µm, n={n}, ar={ar})')
            ax.legend(loc='upper right')
            ax.grid(True, linestyle='--', alpha=0.5)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
        except Exception:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

            # ================== 多层球标签页 ==================
    def init_multilayer_tab(self):
        tab = QWidget()
        tab.setStyleSheet("font-size: 12pt;")
        layout = QVBoxLayout(tab)

        # 环境介质
        medium_grp = QGroupBox("环境介质")
        mlayout = QGridLayout()
        mlayout.addWidget(QLabel("折射率 (实数):"), 0, 0)
        self.ml_medium_edit = QLineEdit("1.0")
        mlayout.addWidget(self.ml_medium_edit, 0, 1)
        medium_grp.setLayout(mlayout)
        layout.addWidget(medium_grp)

        # 波长设置
        wl_grp = QGroupBox("波长设置")
        wlayout = QGridLayout()
        wlayout.addWidget(QLabel("起始波长 (nm):"), 0, 0)
        self.ml_wl_start = QLineEdit("400")
        wlayout.addWidget(self.ml_wl_start, 0, 1)
        wlayout.addWidget(QLabel("终止波长 (nm):"), 1, 0)
        self.ml_wl_end = QLineEdit("800")
        wlayout.addWidget(self.ml_wl_end, 1, 1)
        wlayout.addWidget(QLabel("点数:"), 2, 0)
        self.ml_wl_points = QLineEdit("50")
        wlayout.addWidget(self.ml_wl_points, 2, 1)
        wl_grp.setLayout(wlayout)
        layout.addWidget(wl_grp)

        # 层管理
        layer_mgr = QWidget()
        lm_layout = QHBoxLayout(layer_mgr)
        btn_add = QPushButton("添加层")
        btn_add.clicked.connect(self.add_multilayer_layer)
        btn_remove = QPushButton("删除最后一层")
        btn_remove.clicked.connect(self.remove_multilayer_layer)
        lm_layout.addWidget(btn_add)
        lm_layout.addWidget(btn_remove)
        lm_layout.addStretch()
        layout.addWidget(layer_mgr)

        # 层参数容器
        self.ml_layers_container = QWidget()
        self.ml_layers_layout = QVBoxLayout(self.ml_layers_container)
        layout.addWidget(self.ml_layers_container)

        # 存储层参数的列表
        self.ml_layers = []

        # 计算选项
        opt_grp = QGroupBox("计算选项")
        olayout = QHBoxLayout()
        self.ml_calc_spectrum = QCheckBox("光谱计算")
        self.ml_calc_spectrum.setChecked(True)
        self.ml_calc_angular = QCheckBox("角分布")
        self.ml_calc_angular.setChecked(True)
        olayout.addWidget(self.ml_calc_spectrum)
        olayout.addWidget(self.ml_calc_angular)
        opt_grp.setLayout(olayout)
        layout.addWidget(opt_grp)

        # 按钮
        btn_calc = QPushButton("开始计算")
        btn_calc.clicked.connect(self.on_multilayer_calc)
        layout.addWidget(btn_calc)

        layout.addStretch()
        self.tab_widget.addTab(tab, "多层球")

        # 默认添加一层
        self.add_multilayer_layer()

    def add_multilayer_layer(self):
        idx = len(self.ml_layers) + 1
        frame = QGroupBox(f"第 {idx} 层")
        flayout = QGridLayout()
        flayout.addWidget(QLabel("半径 (nm):"), 0, 0)
        radius_edit = QLineEdit(str(50 * idx))
        flayout.addWidget(radius_edit, 0, 1)
        flayout.addWidget(QLabel("折射率实部 n:"), 1, 0)
        n_edit = QLineEdit("1.5")
        flayout.addWidget(n_edit, 1, 1)
        flayout.addWidget(QLabel("虚部 k:"), 2, 0)
        k_edit = QLineEdit("0.01")
        flayout.addWidget(k_edit, 2, 1)
        frame.setLayout(flayout)
        self.ml_layers_layout.addWidget(frame)
        self.ml_layers.append({
            'frame': frame,
            'radius': radius_edit,
            'n': n_edit,
            'k': k_edit
        })

    def remove_multilayer_layer(self):
        if self.ml_layers:
            layer = self.ml_layers.pop()
            layer['frame'].deleteLater()

    def on_multilayer_calc(self):
        try:
            medium_n = float(self.ml_medium_edit.text())
            wl_start = float(self.ml_wl_start.text())
            wl_end = float(self.ml_wl_end.text())
            wl_points = int(self.ml_wl_points.text())
            wavelengths = np.linspace(wl_start, wl_end, wl_points)

            layers_params = []
            for layer in self.ml_layers:
                r_nm = float(layer['radius'].text())
                n_val = float(layer['n'].text())
                k_val = float(layer['k'].text())
                layers_params.append({
                    'radius': r_nm * 1e-9,
                    'm': n_val + 1j * k_val
                })

            do_spectrum = self.ml_calc_spectrum.isChecked()
            do_angular = self.ml_calc_angular.isChecked()

            output_text = ""
            self.canvas.fig.clear()

            if do_spectrum:
                Qext, Qsca, Qabs = multilayer.compute_multilayer_spectrum(layers_params, wavelengths, medium_n)
                output_text += f"光谱计算完成。\n"

                # 绘制光谱
                ax = self.canvas.fig.add_subplot(1, 1, 1) if not do_angular else self.canvas.fig.add_subplot(2, 1, 1)
                ax.plot(wavelengths, Qext, 'b-', label='消光Qext')
                ax.plot(wavelengths, Qsca, 'r-', label='散射Qsca')
                ax.plot(wavelengths, Qabs, 'g-', label='吸收Qabs')
                ax.set_xlabel("波长 (nm)")
                ax.set_ylabel("效率因子")
                ax.legend()
                ax.grid(True, alpha=0.3)

            if do_angular:
                mid_wl = wavelengths[len(wavelengths)//2]
                theta_deg, Ipar, Iper, Iunpol, Qext, Qsca, Qabs, g = multilayer.compute_multilayer_angular(
                    layers_params, mid_wl, medium_n
                )
                font = self.output_text.font()
                font.setPointSize(12)      # 根据需要调整数值，例如 14、16 等
                self.output_text.setFont(font)

                output_text += f"角分布（中间波长）{mid_wl:.1f} nm:\n"
                output_text += f"消光效率Qext={Qext:.4f}\n散射效率Qsca={Qsca:.4f}\n吸收效率Qabs={Qabs:.4f}\n不对称因子g={g:.4f}\n"
                
                plt.rcParams.update({'legend.fontsize': 16}) 
                # 绘制角分布
                if do_spectrum:
                    ax = self.canvas.fig.add_subplot(2, 1, 2, projection='polar')
                else:
                    ax = self.canvas.fig.add_subplot(1, 1, 1, projection='polar')
                
                theta_rad = np.deg2rad(theta_deg)
                ax.set_theta_zero_location("N")
                ax.set_theta_direction(-1)

                ax.plot(theta_rad, Ipar, 'b--', label='平行')
                ax.plot(theta_rad, Iper, 'r--', label='垂直')
                ax.plot(theta_rad, Iunpol, 'k-', label='非极化')
                ax.set_rscale('log')
                ax.set_xlabel("散射角 (°)")
                ax.set_ylabel("              强度")
                ax.legend(loc='best')
                ax.grid(True, alpha=0.3)

            self.canvas.fig.tight_layout()
            self.canvas.draw()
            self.output_text.setPlainText(output_text)

        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

    # ================== 多粒子标签页 ==================
    def init_multiparticle_tab(self):
        tab = QWidget()
        tab.setStyleSheet("font-size: 12pt;")
        layout = QGridLayout(tab)
        row = 0

        layout.addWidget(QLabel("激光波长 (μm):"), row, 0)
        self.mp_wl_spin = QDoubleSpinBox()
        self.mp_wl_spin.setRange(0.2, 20)
        self.mp_wl_spin.setValue(1.064)
        self.mp_wl_spin.setSuffix(" μm")
        layout.addWidget(self.mp_wl_spin, row, 1)
        row += 1

        # 粒子参数组
        group_particle = QGroupBox("粒子参数")
        glayout = QGridLayout()
        glayout.addWidget(QLabel("有效直径 D (μm):"), 0, 0)
        self.mp_D_edit = QLineEdit("15.0")
        glayout.addWidget(self.mp_D_edit, 0, 1)
        glayout.addWidget(QLabel("总粒子数浓度 N0 (cm⁻³):"), 1, 0)
        self.mp_N0_edit = QLineEdit("100")
        glayout.addWidget(self.mp_N0_edit, 1, 1)
        glayout.addWidget(QLabel("形状参数 μ:"), 2, 0)
        self.mp_sigma_edit = QLineEdit("2.0")
        glayout.addWidget(self.mp_sigma_edit, 2, 1)
        glayout.addWidget(QLabel("折射率实部 n:"), 3, 0)
        self.mp_n_edit = QLineEdit("1.33")
        glayout.addWidget(self.mp_n_edit, 3, 1)
        glayout.addWidget(QLabel("折射率虚部 k:"), 4, 0)
        self.mp_k_edit = QLineEdit("0.01")
        glayout.addWidget(self.mp_k_edit, 4, 1)
        group_particle.setLayout(glayout)
        layout.addWidget(group_particle, row, 0, 1, 2)
        row += 1

        # 雨
        self.mp_rain_check = QCheckBox("雨")
        layout.addWidget(self.mp_rain_check, row, 0)
        layout.addWidget(QLabel("强度 (mm/h):"), row, 1)
        self.mp_rain_rate = QDoubleSpinBox()
        self.mp_rain_rate.setRange(0, 200)
        self.mp_rain_rate.setValue(5)
        self.mp_rain_rate.setSuffix(" mm/h")
        layout.addWidget(self.mp_rain_rate, row, 2)
        row += 1

        # 雾
        self.mp_fog_check = QCheckBox("雾")
        layout.addWidget(self.mp_fog_check, row, 0)
        layout.addWidget(QLabel("能见度 (km):"), row, 1)
        self.mp_vis = QDoubleSpinBox()
        self.mp_vis.setRange(0.01, 50)
        self.mp_vis.setValue(1)
        self.mp_vis.setSuffix(" km")
        layout.addWidget(self.mp_vis, row, 2)
        row += 1

        # 霾
        self.mp_haze_check = QCheckBox("霾")
        layout.addWidget(self.mp_haze_check, row, 0)
        layout.addWidget(QLabel("相对湿度 (%):"), row, 1)
        self.mp_rh = QSpinBox()
        self.mp_rh.setRange(0, 100)
        self.mp_rh.setValue(80)
        self.mp_rh.setSuffix(" %")
        layout.addWidget(self.mp_rh, row, 2)
        row += 1

        # 雪
        self.mp_snow_check = QCheckBox("雪")
        layout.addWidget(self.mp_snow_check, row, 0)
        layout.addWidget(QLabel("强度 (mm/h):"), row, 1)
        self.mp_snow_rate = QDoubleSpinBox()
        self.mp_snow_rate.setRange(0, 50)
        self.mp_snow_rate.setValue(2)
        self.mp_snow_rate.setSuffix(" mm/h")
        layout.addWidget(self.mp_snow_rate, row, 2)
        row += 1
        
        # 计算 + 绘图按钮
        btn_calc = QPushButton("计算散射特性")
        btn_calc.clicked.connect(self.on_multiparticle_calc)
        btn_plot = QPushButton("绘制谱图")
        btn_plot.clicked.connect(self.on_multipart_plot)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_calc)
        btn_layout.addWidget(btn_plot)
        layout.addLayout(btn_layout, row, 0, 1, 3)
        row += 1

        layout.setRowStretch(row, 1)
        self.tab_widget.addTab(tab, "多粒子")

    def on_multiparticle_calc(self):
        try:
            wl_um = self.mp_wl_spin.value()
            dlz_D = float(self.mp_D_edit.text())
            dlz_N0 = float(self.mp_N0_edit.text())
            dlz_sigma = float(self.mp_sigma_edit.text())
            dlz_n = float(self.mp_n_edit.text())
            dlz_k = float(self.mp_k_edit.text())
            rain_rate = self.mp_rain_rate.value() if self.mp_rain_check.isChecked() else None
            vis_km = self.mp_vis.value() if self.mp_fog_check.isChecked() else None
            rh = self.mp_rh.value() if self.mp_haze_check.isChecked() else None
            snow_rate = self.mp_snow_rate.value() if self.mp_snow_check.isChecked() else None

            result = multi_particle.compute_multi_particle(wl_um, dlz_D, dlz_N0, dlz_sigma, dlz_n, dlz_k, rain_rate, vis_km, rh, snow_rate)
            text = (f"消光系数: {result['extinction']:.4e}\n"
                    f"散射系数: {result['scattering']:.4e}\n"
                    f"吸收系数: {result['absorption']:.4e}\n"
                    f"不对称因子: {result['asymmetry']:.4f}")
            
            font = self.output_text.font()
            font.setPointSize(12)      # 根据需要调整数值，例如 14、16 等
            self.output_text.setFont(font)

            self.output_text.setPlainText(text)
            self.canvas.fig.clear()
            self.canvas.draw()
        except Exception as e:
            self.output_text.setPlainText(f"错误:\n{traceback.format_exc()}")

    def on_multipart_plot(self):
        """叠加绘制所有勾选粒子的谱图（横轴半径 μm，纵轴 dN/dr cm⁻³）"""
        # 读取界面上的分布参数（直接使用原始单位）
        try:
            wl_um = self.mp_wl_spin.value()         # μm
            DD_um = float(self.mp_D_edit.text())    # μm
            N0_cm3 = float(self.mp_N0_edit.text())  # cm⁻³
            sigma_g = float(self.mp_sigma_edit.text())
            n = float(self.mp_n_edit.text())
            k = float(self.mp_k_edit.text())
            rh = self.mp_rh.value() if self.mp_haze_check.isChecked() else None
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请检查粒子参数（DD, N0, σg, n, k）是否为有效数字")
            return

        selected = []
        if self.mp_rain_check.isChecked(): selected.append('rain')
        if self.mp_snow_check.isChecked(): selected.append('snow')
        if self.mp_fog_check.isChecked():  selected.append('fog')
        if self.mp_haze_check.isChecked(): selected.append('haze')

        if not selected:
            QMessageBox.warning(self, "未选择", "请至少勾选一种粒子")
            return

        # 统一的半径网格 (μm)
        r_um = np.logspace(-2, 2, 600)     # 0.01 μm ~ 10000 μm

        self.canvas.fig.clear()
        ax = self.canvas.fig.add_subplot(111)

        # 辅助函数：从模型实例获取 dN/dr_um [cm⁻³ μm⁻¹]
        def get_dN_dr_um(model, r_um):
            r_m = r_um * 1e-6                     # μm → m
            dN_dr_m4 = np.array([model.size_distribution(r) for r in r_m])  # m⁻⁴
            # 转换：m⁻⁴ → m⁻³ μm⁻¹  (乘以 1e-6)
            # 再转换：m⁻³ → cm⁻³  (乘以 1e-6)
            dN_dr_cm3_um = dN_dr_m4 * 1e-12       # 直接连乘
            return dN_dr_cm3_um

        # 依次绘制每种粒子（使用原始单位直接构造模型）
        if 'rain' in selected:
            model = multi_particle.RainModel(wl_um, DD_um, N0_cm3, sigma_g, n, k)
            y = get_dN_dr_um(model, r_um)
            ax.loglog(r_um, y, label='雨 (指数分布)')

        if 'snow' in selected:
            model = multi_particle.SnowModel(wl_um, DD_um, N0_cm3, sigma_g, n, k)
            y = get_dN_dr_um(model, r_um)
            ax.loglog(r_um, y, label='雪 (指数分布)')

        if 'fog' in selected:
            # 临时雾滴专用网格：0.1 ~ 50 μm 线性等距
            r_um_fog = np.linspace(0.1, 50, 500)
            model = multi_particle.FogModel(wl_um, DD_um, N0_cm3, sigma_g, n, k)
            y = get_dN_dr_um(model, r_um_fog)
            ax.semilogy(r_um_fog, y, label='雾 (Gamma分布)')
            ax.set_xlim(0, 50)          # 强制横轴 0~50
            ax.set_ylim(1e-10, 1e3)     # 可选，聚焦峰值区域

        if 'haze' in selected:
            model = multi_particle.HazeModel(wl_um, DD_um, N0_cm3, sigma_g, n, k, rh=rh)
            y = get_dN_dr_um(model, r_um)
            label = f'霾 (对数正态'
            if rh is not None:
                label += f', RH={rh}%'
            label += ')'
            ax.loglog(r_um, y, label=label)

        ax.set_xlabel("粒子半径 r (μm)")
        ax.set_ylabel("dN/dr  (cm⁻³ μm⁻¹)")
        ax.grid(True, which="both", linestyle="--", alpha=0.5)
        ax.legend()
        self.canvas.fig.tight_layout()
        self.canvas.draw()