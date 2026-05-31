import pandas as pd
import streamlit as st


APP_TITLE = "碳益评：农业碳资产可信度评估与绿色授信辅助决策系统"
BOUNDARY_STATEMENT = (
    "本系统为贷前辅助筛查工具，不是真实 MRV，不替代银行审批，"
    "不直接发放贷款，不承诺 CCER 一定开发成功。"
)

CARBON_PRICE_SCENARIOS = {
    "保守 60 元/吨": 60,
    "基准 80 元/吨": 80,
    "乐观 100 元/吨": 100,
}

UNIT_REDUCTION = {
    "秸秆还田": 0.15,
    "化肥减量": 0.10,
    "保护性耕作": 0.12,
    "节能农机": 0.08,
}

T = 10
DISCOUNT_FACTOR = 0.74
LTV = 0.6


st.set_page_config(page_title="碳益评", page_icon="🌾", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv("mock_coops.csv")


def calculate_s_carbon(
    G: float,
    B: float,
    V: float,
    R: float,
    C: float,
    A: int,
) -> float:
    return 0.25 * G + 0.20 * B + 0.15 * V + 0.15 * R + 0.15 * C + 0.10 * A


def calculate_expected_revenue_wan(
    area_mu: float,
    low_carbon_measure: str,
    carbon_price: float,
    s_carbon: float,
) -> float:
    unit_reduction = UNIT_REDUCTION[low_carbon_measure]
    q = area_mu * unit_reduction
    e_r_yuan = q * carbon_price * T * DISCOUNT_FACTOR * s_carbon
    return e_r_yuan / 10000


def calculate_credit_limit_wan(
    expected_revenue_wan: float,
    funding_need_wan: float,
    C: float,
    A: int,
    alpha: float,
) -> float:
    s_credit = C
    phi_g = 1 + alpha * A
    return min(funding_need_wan, expected_revenue_wan * LTV * s_credit * phi_g)


def build_scenario_table(
    area_mu: float,
    low_carbon_measure: str,
    s_carbon: float,
    funding_need_wan: float,
    C: float,
    A: int,
    alpha: float,
) -> pd.DataFrame:
    rows = []
    for scenario, price in CARBON_PRICE_SCENARIOS.items():
        expected_revenue_wan = calculate_expected_revenue_wan(
            area_mu, low_carbon_measure, price, s_carbon
        )
        credit_limit_wan = calculate_credit_limit_wan(
            expected_revenue_wan, funding_need_wan, C, A, alpha
        )
        rows.append(
            {
                "碳价情景": scenario,
                "碳价（元/吨）": price,
                "可信碳收益（万元）": expected_revenue_wan,
                "建议授信上限（万元）": credit_limit_wan,
            }
        )
    return pd.DataFrame(rows)


def classify_risk(s_carbon: float, scenario_df: pd.DataFrame, funding_need_wan: float) -> str:
    credit_by_scenario = dict(
        zip(scenario_df["碳价情景"], scenario_df["建议授信上限（万元）"])
    )
    conservative_limit = credit_by_scenario["保守 60 元/吨"]
    base_limit = credit_by_scenario["基准 80 元/吨"]
    optimistic_limit = credit_by_scenario["乐观 100 元/吨"]

    if s_carbon >= 0.70 and conservative_limit >= funding_need_wan:
        return "绿色：低风险"
    if optimistic_limit < funding_need_wan or s_carbon < 0.40:
        return "红色：高风险"
    if base_limit >= funding_need_wan and conservative_limit < funding_need_wan:
        return "黄色：中风险"
    return "黄色：中风险"


def get_main_risk_factors(
    G: float,
    B: float,
    V: float,
    R: float,
    C: float,
    A: int,
) -> list[str]:
    factors = []
    indicators = {
        "空间生态潜力 G 偏低": G,
        "低碳措施适配度 B 偏低": B,
        "核证可行性 V 偏低": V,
        "收益稳定性 R 偏低": R,
        "主体履约能力 C 偏低": C,
    }
    for label, value in indicators.items():
        if value < 0.60:
            factors.append(label)
    if A == 0:
        factors.append("政策适配度 A 未命中")
    if not factors:
        factors.append("当前核心指标整体较均衡，仍需关注后续数据留痕和复评")
    return factors


def format_wan(value: float) -> str:
    return f"{value:.2f} 万元"


def format_score(value: float) -> str:
    return f"{value * 100:.2f} 分"


def render_reports(
    cooperative_name: str,
    s_carbon: float,
    selected_credit_limit_wan: float,
    risk_level: str,
    risk_factors: list[str],
    alpha: float,
    A: int,
) -> None:
    candidate_text = "建议纳入绿色授信备选名单" if risk_level != "红色：高风险" else "暂不建议直接纳入绿色授信备选名单"
    pilot_text = "建议纳入县域绿色金融试点观察名单" if s_carbon >= 0.60 and A == 1 else "建议暂作为县域绿色金融试点储备对象"
    compensation_text = "可考虑触发有限责任风险补偿机制" if A == 1 and alpha > 0 else "暂不建议触发有限责任风险补偿机制"
    credibility_text = (
        "较高" if s_carbon >= 0.70 else "中等" if s_carbon >= 0.40 else "较低"
    )
    risk_factor_text = "；".join(risk_factors)

    st.info("AI/模板化解释层只负责解释模型结果，不参与风险计算，不参与授信审批。")

    bank_tab, gov_tab, coop_tab = st.tabs(["银行版建议", "政府版建议", "合作社版建议"])

    with bank_tab:
        st.markdown(
            f"""
**银行版建议**

- 是否建议纳入绿色授信备选名单：{candidate_text}。
- 建议授信上限：{format_wan(selected_credit_limit_wan)}，该数值仅为贷前辅助筛查口径下的建议上限。
- 主要风险因素：{risk_factor_text}。
- 是否建议动态复评：建议结合遥感代理指标、低碳行为记录和经营履约表现进行动态复评。
- 最终审批仍由银行按内部制度、风控政策和尽调结果独立完成，本系统不批准贷款。
"""
        )

    with gov_tab:
        st.markdown(
            f"""
**政府版建议**

- 是否建议纳入县域绿色金融试点：{pilot_text}。
- 是否建议触发有限责任风险补偿：{compensation_text}，当前政府风险分担比例 alpha 为 {alpha:.2f}。
- 政府风险补偿只能作为有限责任分担安排，不能 100% 兜底。
- 应同步设置银行尽调责任、合作社真实记录义务和贷后复评机制，防止银行和合作社道德风险。
- AI/模板化解释层只负责解释模型结果，不参与风险计算，不参与授信审批。
"""
        )

    with coop_tab:
        st.markdown(
            f"""
**合作社版建议**

- 当前低碳措施下，{cooperative_name} 的碳资产可信度水平为{credibility_text}，评分为 {format_score(s_carbon)}。
- 可通过提高低碳措施与作物场景适配度、增强核证可行性、稳定经营收益和提升履约能力来提高可信度评分。
- 建议保存低碳农资采购记录、作业台账、农机作业凭证、地块边界资料、遥感佐证材料和合作社成员执行记录。
- 后续可通过连续留痕、规范财务记录、稳定订单或保险安排、参与政策试点来提高融资可得性。
- AI/模板化解释层只负责解释模型结果，不参与风险计算，不参与授信审批。
"""
        )


df = load_data()

st.title(APP_TITLE)

st.header("一、项目边界说明")
st.warning(BOUNDARY_STATEMENT)
st.caption("系统基于公开 GIS/遥感代理指标和模拟合作社数据，对农业碳资产可信度进行评估，并输出绿色授信辅助建议。")

with st.sidebar:
    st.header("参数输入")

    selected_id = st.selectbox(
        "选择合作社",
        options=df["cooperative_id"].tolist(),
        format_func=lambda coop_id: f"{coop_id} - {df.loc[df['cooperative_id'] == coop_id, 'cooperative_name'].iloc[0]}",
    )

    selected_row = df.loc[df["cooperative_id"] == selected_id].iloc[0]

    area_mu = st.number_input(
        "种植面积 area_mu",
        min_value=1.0,
        value=float(selected_row["area_mu"]),
        step=100.0,
    )

    crop_options = sorted(df["crop_type"].unique().tolist())
    crop_type = st.selectbox(
        "作物类型 crop_type",
        options=crop_options,
        index=crop_options.index(selected_row["crop_type"]),
    )

    measure_options = list(UNIT_REDUCTION.keys())
    low_carbon_measure = st.selectbox(
        "低碳措施 low_carbon_measure",
        options=measure_options,
        index=measure_options.index(selected_row["low_carbon_measure"]),
    )

    selected_scenario = st.selectbox(
        "碳价情景",
        options=list(CARBON_PRICE_SCENARIOS.keys()),
        index=1,
    )
    carbon_price = CARBON_PRICE_SCENARIOS[selected_scenario]

    G = st.slider("G 空间生态潜力", 0.0, 1.0, float(selected_row["G_ecological_potential"]), 0.01)
    B = st.slider("B 低碳措施适配度", 0.0, 1.0, float(selected_row["B_measure_fit"]), 0.01)
    V = st.slider("V 核证可行性", 0.0, 1.0, float(selected_row["V_verification_feasibility"]), 0.01)
    R = st.slider("R 收益稳定性", 0.0, 1.0, float(selected_row["R_revenue_stability"]), 0.01)
    C = st.slider("C 主体履约能力", 0.0, 1.0, float(selected_row["C_performance_capacity"]), 0.01)
    A = st.selectbox("A 政策适配度", options=[0, 1], index=int(selected_row["A_policy_fit"]))
    alpha = st.slider(
        "政府风险分担比例 alpha",
        0.0,
        0.8,
        float(selected_row["alpha_government_risk_share"]),
        0.01,
    )
    funding_need_wan = st.number_input(
        "资金需求 funding_need_wan，单位万元",
        min_value=0.0,
        value=float(selected_row["funding_need_wan"]),
        step=1.0,
    )

s_carbon = calculate_s_carbon(G, B, V, R, C, A)
selected_expected_revenue_wan = calculate_expected_revenue_wan(
    area_mu, low_carbon_measure, carbon_price, s_carbon
)
selected_credit_limit_wan = calculate_credit_limit_wan(
    selected_expected_revenue_wan, funding_need_wan, C, A, alpha
)
scenario_df = build_scenario_table(
    area_mu,
    low_carbon_measure,
    s_carbon,
    funding_need_wan,
    C,
    A,
    alpha,
)
risk_level = classify_risk(s_carbon, scenario_df, funding_need_wan)
risk_factors = get_main_risk_factors(G, B, V, R, C, A)

st.header("二、模型计算结果")
metric_cols = st.columns(4)
metric_cols[0].metric("碳资产可信度评分", format_score(s_carbon))
metric_cols[1].metric("可信碳收益", format_wan(selected_expected_revenue_wan))
metric_cols[2].metric("建议授信上限", format_wan(selected_credit_limit_wan))
metric_cols[3].metric("风险等级", risk_level)

result_df = pd.DataFrame(
    [
        {
            "合作社名称": selected_row["cooperative_name"],
            "作物类型": crop_type,
            "低碳措施": low_carbon_measure,
            "面积（亩）": area_mu,
            "可信度评分": f"{s_carbon * 100:.2f}",
            "可信碳收益（万元）": f"{selected_expected_revenue_wan:.2f}",
            "建议授信上限（万元）": f"{selected_credit_limit_wan:.2f}",
            "风险等级": risk_level,
        }
    ]
)
st.dataframe(result_df, width="stretch", hide_index=True)

st.header("三、碳价压力测试")
chart_df = scenario_df.set_index("碳价情景")[["建议授信上限（万元）"]]
st.bar_chart(chart_df, width="stretch")
st.dataframe(
    scenario_df.assign(
        **{
            "可信碳收益（万元）": scenario_df["可信碳收益（万元）"].map(lambda x: f"{x:.2f}"),
            "建议授信上限（万元）": scenario_df["建议授信上限（万元）"].map(lambda x: f"{x:.2f}"),
        }
    ),
    width="stretch",
    hide_index=True,
)

st.header("四、AI/模板化解释报告")
render_reports(
    str(selected_row["cooperative_name"]),
    s_carbon,
    selected_credit_limit_wan,
    risk_level,
    risk_factors,
    alpha,
    A,
)
