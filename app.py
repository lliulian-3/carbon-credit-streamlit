import html
import textwrap

import pandas as pd
import streamlit as st


APP_TITLE = "碳益评：农业碳资产可信度评估与绿色授信辅助决策系统"
BOUNDARY_STATEMENT = (
    "温馨提示：本系统用于提供贷前参考和评估建议，不是政府或金融机构的正式认定工具，"
    "不直接审批贷款，不直接放款，最终结果以金融机构审核为准。"
)

CARBON_PRICE_SCENARIOS = {
    "保守 60 元/吨": 60,
    "基准 80 元/吨": 80,
    "乐观 100 元/吨": 100,
}

SCENARIO_NOTES = {
    "保守 60 元/吨": "按较低碳价测算，适合看底线情况",
    "基准 80 元/吨": "按常规碳价测算，适合作为主要参考",
    "乐观 100 元/吨": "按较高碳价测算，适合看上行情景",
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


st.set_page_config(page_title="碳益评", layout="wide")


def clean_html(markup: str) -> str:
    return textwrap.dedent(markup).strip()


def render_html(markup: str) -> None:
    markup = clean_html(markup)
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_css() -> None:
    with open("style.css", "r", encoding="utf-8") as file:
        render_html(f"<style>{file.read()}</style>")


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
    credit_support_wan = calculate_credit_support_wan(expected_revenue_wan, C, A, alpha)
    return min(funding_need_wan, credit_support_wan)


def calculate_credit_support_wan(
    expected_revenue_wan: float,
    C: float,
    A: int,
    alpha: float,
) -> float:
    s_credit = C
    phi_g = 1 + alpha * A
    return expected_revenue_wan * LTV * s_credit * phi_g


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
        credit_support_wan = calculate_credit_support_wan(
            expected_revenue_wan, C, A, alpha
        )
        credit_limit_wan = calculate_credit_limit_wan(
            expected_revenue_wan, funding_need_wan, C, A, alpha
        )
        rows.append(
            {
                "碳价情景": scenario,
                "碳价（元/吨）": price,
                "可信碳收益（万元）": expected_revenue_wan,
                "碳收益支撑额度（万元）": credit_support_wan,
                "建议授信上限（万元）": credit_limit_wan,
                "情景说明": SCENARIO_NOTES[scenario],
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
    indicators = [
        ("空间生态条件", G, "空间生态条件相对较弱，建议关注地块条件和种植稳定性。"),
        ("措施适配程度", B, "措施适配程度相对较弱，建议选择更适合作物的低碳做法。"),
        ("资料是否好核查", V, "资料是否好核查这一项相对较弱，建议完善作业记录、购销凭证、照片或遥感证明材料。"),
        ("收益稳定性", R, "收益稳定性相对较弱，建议关注碳价波动、气象风险和产量波动。"),
        ("持续履约能力", C, "持续履约能力相对较弱，建议完善合作社经营记录和履约记录。"),
        ("是否符合政策支持方向", float(A), "政策支持方向匹配度相对较弱，建议关注是否符合地方绿色金融试点和农业低碳政策方向。"),
    ]
    _, _, tip = min(indicators, key=lambda item: item[1])
    return [tip]


def risk_class(risk_level: str) -> str:
    if risk_level.startswith("绿色"):
        return "risk-low"
    if risk_level.startswith("红色"):
        return "risk-high"
    return "risk-mid"


def format_wan(value: float) -> str:
    return f"{value:.2f} 万元"


def format_score(value: float) -> str:
    return f"{value * 100:.2f} 分"


def wheat_svg() -> str:
    return clean_html(
        """
        <svg class="wheat-svg" viewBox="0 0 220 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M112 152 C105 116 106 80 119 34" stroke="#F4D88A" stroke-width="8" stroke-linecap="round"/>
            <path d="M118 42 C92 44 82 61 82 61 C102 69 116 59 118 42Z" fill="#F4D88A" opacity=".95"/>
            <path d="M113 66 C87 70 77 88 77 88 C99 95 112 84 113 66Z" fill="#E6BD5B" opacity=".95"/>
            <path d="M110 92 C83 98 75 117 75 117 C98 122 110 109 110 92Z" fill="#F4D88A" opacity=".95"/>
            <path d="M125 51 C148 59 154 78 154 78 C132 80 122 68 125 51Z" fill="#F4D88A" opacity=".95"/>
            <path d="M119 78 C145 86 151 106 151 106 C128 107 117 94 119 78Z" fill="#E6BD5B" opacity=".95"/>
            <path d="M116 105 C140 114 145 134 145 134 C123 133 114 120 116 105Z" fill="#F4D88A" opacity=".95"/>
            <path d="M38 150 C75 133 141 132 184 151" stroke="#B7D7A8" stroke-width="10" stroke-linecap="round" opacity=".7"/>
            <path d="M28 166 C72 150 146 150 194 166" stroke="#8FBC79" stroke-width="8" stroke-linecap="round" opacity=".55"/>
        </svg>
        """
    )


def section_html(title: str, note: str = "") -> str:
    note_html = f'<div class="section-note">{h(note)}</div>' if note else ""
    return clean_html(
        f"""
        <div class="section-heading">
            <div class="section-icon">🌾</div>
            <div>
                <div class="section-title">{h(title)}</div>
                {note_html}
            </div>
        </div>
        """
    )


def render_section(title: str, note: str = "") -> None:
    render_html(section_html(title, note))


def render_current_object_card(
    cooperative_name: str,
    crop_type: str,
    low_carbon_measure: str,
    area_mu: float,
    funding_need_wan: float,
) -> str:
    return clean_html(
        f"""
        <div class="farm-card">
            {wheat_svg()}
            <div class="farm-card-title">当前评估对象</div>
            <div class="farm-row"><span>合作社</span><strong>{h(cooperative_name)}</strong></div>
            <div class="farm-row"><span>作物</span><strong>{h(crop_type)}</strong></div>
            <div class="farm-row"><span>低碳做法</span><strong>{h(low_carbon_measure)}</strong></div>
            <div class="farm-row"><span>种植面积</span><strong>{area_mu:,.0f} 亩</strong></div>
            <div class="farm-row"><span>资金需求</span><strong>{funding_need_wan:.2f} 万元</strong></div>
        </div>
        """
    )


def hero_html(
    cooperative_name: str,
    crop_type: str,
    low_carbon_measure: str,
    area_mu: float,
    funding_need_wan: float,
) -> str:
    current_card = render_current_object_card(
        cooperative_name, crop_type, low_carbon_measure, area_mu, funding_need_wan
    )
    return clean_html(
        f"""
        <div class="hero">
            <div class="hero-copy">
                <div class="brand-line"><span class="brand-mark">碳</span><span>碳益评</span></div>
                <h1>{h(APP_TITLE)}</h1>
                <p class="hero-subtitle">帮助合作社看懂低碳价值，辅助获得绿色金融支持。选择合作社和种植情况后，系统会给出低碳价值评估和融资参考建议。</p>
                <div class="hero-tags">
                    <span>贷前参考</span>
                    <span>绿色评估</span>
                    <span>风险分层</span>
                    <span>不替代审批</span>
                </div>
            </div>
            {current_card}
        </div>
        """
    )


def result_cards_html(
    s_carbon: float,
    selected_expected_revenue_wan: float,
    selected_credit_limit_wan: float,
    risk_level: str,
) -> str:
    score_width = max(0, min(100, s_carbon * 100))
    return clean_html(
        f"""
        <div class="result-grid">
            <div class="result-card">
                <div class="result-top"><span>碳资产可信度评分</span><em>🌱</em></div>
                <div class="result-value">{s_carbon * 100:.2f}<small>分</small></div>
                <div class="score-track"><div class="score-fill" style="width:{score_width:.0f}%"></div></div>
                <p>反映当前低碳种植做法的可信程度。</p>
            </div>
            <div class="result-card">
                <div class="result-top"><span>可信碳收益</span><em>🌾</em></div>
                <div class="result-value">{selected_expected_revenue_wan:.2f}<small>万元</small></div>
                <p>按当前碳价情景估算的碳收益参考值。</p>
            </div>
            <div class="result-card">
                <div class="result-top"><span>建议授信上限（参考）</span><em>¥</em></div>
                <div class="result-value">{selected_credit_limit_wan:.2f}<small>万元</small></div>
                <p>系统给出的融资参考上限，不代表最终放款额度。</p>
            </div>
            <div class="result-card {risk_class(risk_level)}">
                <div class="result-top"><span>风险等级</span><em>●</em></div>
                <div class="result-value risk-text">{h(risk_level)}</div>
                <p>综合可信度和情景测试后的评估结果。</p>
            </div>
        </div>
        """
    )


def render_scenario_row(row: pd.Series, max_limit: float) -> str:
    support_wan = float(row["碳收益支撑额度（万元）"])
    credit_limit_wan = float(row["建议授信上限（万元）"])
    width = support_wan / max_limit * 100
    return clean_html(
        f"""
        <div class="scenario-row">
            <div class="scenario-text">
                <strong>{h(row["碳价情景"])}</strong>
                <span>{h(row["情景说明"])}</span>
            </div>
            <div class="scenario-bar-wrap" aria-hidden="true">
                <div class="scenario-bar" style="width:{width:.0f}%"></div>
            </div>
            <div class="scenario-value">
                <span>支撑额度</span><strong>{support_wan:.2f} 万元</strong>
                <span>建议上限</span><strong>{credit_limit_wan:.2f} 万元</strong>
            </div>
        </div>
        """
    )


def scenario_compare_html(scenario_df: pd.DataFrame) -> str:
    max_limit = max(float(scenario_df["碳收益支撑额度（万元）"].max()), 0.01)
    rows_html = "\n".join(
        render_scenario_row(row, max_limit) for _, row in scenario_df.iterrows()
    )
    return clean_html(
        f"""
        <div class="scenario-panel">
            <div class="scenario-explain">
                碳收益支撑额度反映不同碳价下的理论支撑能力；建议授信上限还会受到合作社资金需求约束。
            </div>
            {rows_html}
        </div>
        """
    )


def risk_factors_html(risk_factors: list[str]) -> str:
    items = "".join(f"<li>{h(factor)}</li>" for factor in risk_factors)
    return clean_html(
        f"""
        <div class="soft-card">
            <div class="soft-card-title">需要重点关注的地方</div>
            <ul class="risk-list">{items}</ul>
        </div>
        """
    )


def render_advice_card(title: str, items: list[str]) -> str:
    list_items = "".join(f"<li>{h(item)}</li>" for item in items)
    return clean_html(
        f"""
        <div class="advice-card">
            <h3>{h(title)}</h3>
            <ul>{list_items}</ul>
        </div>
        """
    )


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

    render_html(
        '<div class="plain-note">说明：解释建议只负责把评估结果说清楚，不参与风险计算，也不参与贷款审核。</div>'
    )

    bank_tab, gov_tab, coop_tab = st.tabs(["给银行的建议", "给政府的建议", "给合作社的建议"])

    with bank_tab:
        render_html(
            render_advice_card(
                "给银行的建议",
                [
                    f"是否建议纳入绿色授信备选名单：{candidate_text}。",
                    f"建议授信上限（参考）：{format_wan(selected_credit_limit_wan)}。",
                    f"主要关注点：{risk_factor_text}。",
                    "建议结合低碳行为记录、经营流水和履约情况进行动态复评。",
                    "最终结果仍由银行按内部制度、风控政策和尽调情况审核，本系统不直接放款。",
                ],
            )
        )

    with gov_tab:
        render_html(
            render_advice_card(
                "给政府的建议",
                [
                    f"是否建议纳入县域绿色金融试点：{pilot_text}。",
                    f"是否建议触发有限责任风险补偿：{compensation_text}，当前风险分担比例为 {alpha:.2f}。",
                    "政府风险补偿只能作为有限责任分担安排，不能 100% 兜底。",
                    "建议同步设置银行尽调责任、合作社真实记录义务和贷后复评机制，防止道德风险。",
                ],
            )
        )

    with coop_tab:
        render_html(
            render_advice_card(
                "给合作社的建议",
                [
                    f"{cooperative_name} 当前碳资产可信度水平为{credibility_text}，评分为 {format_score(s_carbon)}。",
                    "建议继续完善低碳做法，提高措施和作物、地块条件的匹配程度。",
                    "建议保存农资采购记录、作业台账、农机凭证、地块边界资料、照片或遥感佐证材料。",
                    "可通过连续留痕、规范财务记录、稳定订单或保险安排，提高后续融资可得性。",
                ],
            )
        )


load_css()
df = load_data()

with st.sidebar:
    st.markdown("## 合作社情况填写")
    st.caption("请按实际情况选择或调整，右侧评估结果会自动更新。")

    selected_id = st.selectbox(
        "选择合作社",
        options=df["cooperative_id"].tolist(),
        format_func=lambda coop_id: f"{df.loc[df['cooperative_id'] == coop_id, 'cooperative_name'].iloc[0]}",
        help="选择需要评估的合作社。系统会自动带入一组示例数据，您也可以继续调整。",
    )

    selected_row = df.loc[df["cooperative_id"] == selected_id].iloc[0]

    with st.expander("一、种植基本情况", expanded=True):
        area_mu = st.number_input(
            "种植面积（亩）",
            min_value=1.0,
            value=float(selected_row["area_mu"]),
            step=100.0,
            help="填写合作社本季主要种植面积。",
        )

        crop_options = sorted(df["crop_type"].unique().tolist())
        crop_type = st.selectbox(
            "作物类型",
            options=crop_options,
            index=crop_options.index(selected_row["crop_type"]),
            help="选择当前主要种植的作物。",
        )

        measure_options = list(UNIT_REDUCTION.keys())
        low_carbon_measure = st.selectbox(
            "低碳做法",
            options=measure_options,
            index=measure_options.index(selected_row["low_carbon_measure"]),
            help="选择当前主要采用的绿色种植方式。",
        )

        selected_scenario = st.selectbox(
            "碳价情景",
            options=list(CARBON_PRICE_SCENARIOS.keys()),
            index=1,
            help="选择用于估算碳收益的碳价情景。",
        )
        carbon_price = CARBON_PRICE_SCENARIOS[selected_scenario]

    with st.expander("二、低碳种植可信情况", expanded=True):
        G = st.slider("空间生态条件", 0.0, 1.0, float(selected_row["G_ecological_potential"]), 0.01, help="地块生态条件、空间位置等对低碳价值形成的支持程度。")
        B = st.slider("措施适配程度", 0.0, 1.0, float(selected_row["B_measure_fit"]), 0.01, help="低碳做法与作物、地块、生产方式的匹配程度。")
        V = st.slider("资料是否好核查", 0.0, 1.0, float(selected_row["V_verification_feasibility"]), 0.01, help="后续收集资料、核查记录、说明低碳行为是否方便。")
        R = st.slider("收益稳定性", 0.0, 1.0, float(selected_row["R_revenue_stability"]), 0.01, help="经营收益和碳收益预期是否相对稳定。")
        C = st.slider("持续履约能力", 0.0, 1.0, float(selected_row["C_performance_capacity"]), 0.01, help="合作社持续执行低碳做法、按时履约和维护记录的能力。")
        A = st.selectbox(
            "是否符合政策支持方向",
            options=[1, 0],
            index=0 if int(selected_row["A_policy_fit"]) == 1 else 1,
            format_func=lambda value: "是，符合政策支持方向" if value == 1 else "否，暂不符合政策支持方向",
            help="选择当前项目是否符合当地绿色金融和农业低碳政策支持方向。",
        )

    with st.expander("三、融资参考填写", expanded=True):
        alpha = st.slider(
            "政府风险分担比例",
            0.0,
            0.8,
            float(selected_row["alpha_government_risk_share"]),
            0.01,
            help="政府或政策工具可能承担的有限风险分担比例。",
        )
        funding_need_wan = st.number_input(
            "资金需求（万元）",
            min_value=0.0,
            value=float(selected_row["funding_need_wan"]),
            step=1.0,
            help="填写合作社希望获得的资金支持规模。",
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

render_html(
    hero_html(
        str(selected_row["cooperative_name"]),
        crop_type,
        low_carbon_measure,
        area_mu,
        funding_need_wan,
    )
)

render_html(f'<div class="notice-box">{h(BOUNDARY_STATEMENT)}</div>')

render_section(
    "评估结果一眼看懂",
    "下面四项是本次评估最重要的结果，数值会随着左侧填写内容自动变化。",
)
render_html(
    result_cards_html(
        s_carbon,
        selected_expected_revenue_wan,
        selected_credit_limit_wan,
        risk_level,
    )
)

render_section(
    "不同碳价情景下的融资参考",
    "同一合作社在不同碳价下，碳收益支撑能力和融资参考上限会有所不同。",
)
left_col, right_col = st.columns([1.45, 1])
with left_col:
    render_html(scenario_compare_html(scenario_df))
with right_col:
    render_html(risk_factors_html(risk_factors))

result_df = pd.DataFrame(
    [
        {
            "合作社名称": selected_row["cooperative_name"],
            "作物类型": crop_type,
            "低碳做法": low_carbon_measure,
            "面积（亩）": f"{area_mu:.0f}",
            "可信度评分": f"{s_carbon * 100:.2f}",
            "可信碳收益（万元）": f"{selected_expected_revenue_wan:.2f}",
            "建议授信上限（万元）": f"{selected_credit_limit_wan:.2f}",
            "风险等级": risk_level,
        }
    ]
)

with st.expander("查看当前合作社评估明细", expanded=False):
    st.dataframe(result_df, width="stretch", hide_index=True)
    display_scenario_df = scenario_df.assign(
        **{
            "可信碳收益（万元）": scenario_df["可信碳收益（万元）"].map(lambda x: f"{x:.2f}"),
            "碳收益支撑额度（万元）": scenario_df["碳收益支撑额度（万元）"].map(lambda x: f"{x:.2f}"),
            "建议授信上限（万元）": scenario_df["建议授信上限（万元）"].map(lambda x: f"{x:.2f}"),
        }
    )
    st.dataframe(display_scenario_df, width="stretch", hide_index=True)

render_section(
    "给不同对象的建议",
    "系统把同一份评估结果分别说给银行、政府和合作社看，方便沟通和后续完善。",
)
render_reports(
    str(selected_row["cooperative_name"]),
    s_carbon,
    selected_credit_limit_wan,
    risk_level,
    risk_factors,
    alpha,
    A,
)
