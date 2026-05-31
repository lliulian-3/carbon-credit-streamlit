# 碳益评：农业碳资产可信度评估与绿色授信辅助决策系统

## 项目说明

本项目是一个基于 Streamlit 的农业绿色融资参考服务页面。系统根据模拟合作社数据、低碳种植做法和碳价情景，评估农业碳资产可信度，并给出融资参考建议。

温馨提示：本系统用于提供贷前参考和评估建议，不是政府或金融机构的正式认定工具，不直接审批贷款，不直接放款，最终结果以金融机构审核为准。

## 文件结构

```text
.
├── app.py
├── style.css
├── mock_coops.csv
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

文件说明：

- `app.py`：Streamlit 页面和计算逻辑。
- `style.css`：页面视觉样式。
- `mock_coops.csv`：模拟合作社数据。
- `requirements.txt`：运行依赖。
- `.streamlit/config.toml`：Streamlit 主题颜色配置。
- `README.md`：运行和部署说明。

## 本地运行

安装依赖：

```bash
pip install streamlit pandas
```

启动应用：

```bash
streamlit run app.py
```

启动后浏览器打开：

```text
http://localhost:8501
```

也可以在 Windows 上双击 `run_app.bat` 启动。使用时请保持黑色命令窗口不要关闭。

## 页面功能

- 选择合作社和种植情况
- 调整低碳可信度相关指标
- 查看碳资产可信度评分
- 查看可信碳收益参考值
- 查看建议授信上限
- 查看风险等级
- 对比保守、基准、乐观三种碳价情景
- 查看给银行、政府和合作社的建议

## 部署到 Streamlit Community Cloud

1. 将以下文件上传到 GitHub 仓库根目录：

```text
app.py
style.css
mock_coops.csv
requirements.txt
README.md
.streamlit/config.toml
```

2. 打开 Streamlit Community Cloud。
3. 选择 GitHub 仓库。
4. 主文件填写：

```text
app.py
```

5. 点击部署。

部署成功后，平台会生成一个 `.streamlit.app` 结尾的网址，可直接发给别人查看。
