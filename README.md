# 碳益评：农业碳资产可信度评估与绿色授信辅助决策系统

## 项目定位

本项目是一个 Streamlit 原型系统，用于中国研究生“双碳”创新与创意大赛展示。

系统定位为农业合作社碳资产可信度评估与绿色授信辅助决策工具。它基于模拟合作社数据、公开 GIS/遥感代理指标思路和模板化解释报告，对农业碳资产可信度进行评估，并输出绿色授信辅助建议。

边界声明：本系统为贷前辅助筛查工具，不是真实 MRV，不替代银行审批，不直接发放贷款，不承诺 CCER 一定开发成功。

## 项目文件结构

```text
.
├── app.py
├── mock_coops.csv
├── requirements.txt
└── README.md
```

文件说明：

- `app.py`：Streamlit 应用主程序。
- `mock_coops.csv`：模拟农业合作社数据，应用通过 `pd.read_csv("mock_coops.csv")` 读取。
- `requirements.txt`：Streamlit Community Cloud 部署依赖。
- `README.md`：项目说明、本地运行方式和部署步骤。

## 本地运行方式

先进入项目文件夹，然后安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
streamlit run app.py
```

启动后，终端会显示类似下面的地址：

```text
Local URL: http://localhost:8501
```

在浏览器打开该地址即可使用系统。

## 输入说明

左侧 sidebar 支持选择合作社，并可调整以下参数：

- 选择合作社
- 种植面积 `area_mu`
- 作物类型 `crop_type`
- 低碳措施 `low_carbon_measure`
- 碳价情景：保守 60 元/吨、基准 80 元/吨、乐观 100 元/吨
- `G` 空间生态潜力，0 到 1
- `B` 低碳措施适配度，0 到 1
- `V` 核证可行性，0 到 1
- `R` 收益稳定性，0 到 1
- `C` 主体履约能力，0 到 1
- `A` 政策适配度，0 或 1
- 政府风险分担比例 `alpha`，0 到 0.8
- 资金需求 `funding_need_wan`，单位万元

## 输出说明

页面输出包括：

- 碳资产可信度评分，按百分制展示
- 可信碳收益，单位万元
- 建议授信上限，单位万元
- 风险等级
- 三种碳价情景下的建议授信上限压力测试图表
- 当前合作社计算结果表
- 银行版、政府版、合作社版三方模板化解释报告

AI/模板化解释层只负责解释模型结果，不参与风险计算，不参与授信审批。

## 部署到 Streamlit Community Cloud

1. 准备一个 GitHub 仓库。
2. 将本项目的 `app.py`、`mock_coops.csv`、`requirements.txt`、`README.md` 上传到仓库根目录。
3. 打开 [Streamlit Community Cloud](https://streamlit.io/cloud)。
4. 使用 GitHub 账号登录。
5. 点击 `New app`。
6. 选择刚才上传项目的 GitHub 仓库、分支和主文件。
7. 主文件路径填写：

```text
app.py
```

8. 点击 `Deploy`。

部署时，Streamlit Community Cloud 会自动读取 `requirements.txt` 安装依赖，并运行 `app.py`。由于数据文件 `mock_coops.csv` 与 `app.py` 位于同一目录，应用会通过相对路径 `pd.read_csv("mock_coops.csv")` 正确读取数据。

## 部署注意事项

- 不要在 `app.py` 中使用 `C:/Users/...`、`/mnt/data/...` 等本地绝对路径。
- 数据文件应放在仓库中，并使用相对路径读取。
- 本系统仅用于原型展示和贷前辅助筛查，不构成真实授信审批结论。
