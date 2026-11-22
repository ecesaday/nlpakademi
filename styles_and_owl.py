"""Canlı renk teması, animasyonlu Piku baykuşu ve yardımcı HTML bileşenleri."""
import html
import random

import streamlit as st

POS_COLORS = {
    "İsim": "#8B5CF6", "Fiil": "#10B981", "Sıfat": "#F59E0B", "Zarf": "#06B6D4",
    "Zamir": "#EC4899", "Bağlaç": "#6366F1", "Edat": "#14B8A6", "Ünlem": "#EF4444",
    "Sayı": "#84CC16", "Noktalama": "#94A3B8", "Diğer": "#64748B",
}
ENTITY_COLORS = {"Kişi": "#8B5CF6", "Yer": "#10B981", "Kurum": "#F59E0B", "Tarih": "#06B6D4"}
SENTIMENT_STYLE = {
    "Pozitif": ("😄", "#10B981"), "Negatif": ("😠", "#EF4444"),
    "Nötr": ("😐", "#06B6D4"), "Karma": ("🤔", "#F59E0B"),
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
html, body, .stApp, .stApp button, .stApp input, .stApp textarea { font-family: 'Nunito', sans-serif !important; }
.stApp { background: linear-gradient(160deg,#F5F3FF 0%,#ECFEFF 50%,#FFFBEB 100%); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown { color: #1F2937; }
#MainMenu, footer { visibility: hidden; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#FFFFFF,#F5F3FF); border-right: 3px solid #DDD6FE; }
.stButton > button { border-radius: 16px; font-weight: 800; font-size: 1rem; padding: .55rem 1.1rem; border: 2px solid #C4B5FD; border-bottom: 5px solid #A78BFA; background: #FFFFFF; color: #6D28D9; transition: transform .08s, border-bottom-width .08s, background .15s; }
.stButton > button p { color: inherit; font-weight: 800; }
.stButton > button:hover { transform: translateY(-2px); background: #F5F3FF; border-color: #8B5CF6; color: #6D28D9; }
.stButton > button:active { transform: translateY(3px); border-bottom-width: 2px; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] { background: #10B981; color: #FFFFFF; border: 2px solid #059669; border-bottom: 5px solid #047857; }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #34D399; color: #FFFFFF; }
.stTextArea textarea { border-radius: 16px; border: 2px solid #C4B5FD; background: #FFFFFF; color: #1F2937; font-size: 1.05rem; }
.stTextArea textarea:focus { border-color: #8B5CF6; box-shadow: 0 0 0 3px #DDD6FE; }
.card { background: #FFFFFF; border-radius: 22px; padding: 18px 22px; border: 2px solid #EDE9FE; box-shadow: 0 6px 0 #DDD6FE; margin: 10px 0; }
.card h4 { margin: 0 0 8px 0; color: #6D28D9; }
.textbox { background: #FFFFFF; border-radius: 18px; padding: 16px; border: 2px dashed #C4B5FD; line-height: 2.3; font-size: 1.1rem; color: #1F2937; }
.module-header { border-radius: 24px; padding: 18px 26px; margin-bottom: 8px; box-shadow: 0 6px 0 rgba(0,0,0,.15); }
.module-header, .module-header * { color: #FFFFFF !important; }
.module-header h2 { margin: 0; font-weight: 900; font-size: 1.8rem; }
.module-header p { margin: 2px 0 0 0; font-weight: 700; opacity: .95; }
.owl-row { display: flex; align-items: center; gap: 16px; margin: 8px 0; }
.owl { flex-shrink: 0; overflow: visible; }
.bubble { position: relative; background: #FFFFFF; border: 3px solid #8B5CF6; border-radius: 22px; padding: 14px 18px; font-weight: 700; font-size: 1.02rem; color: #1F2937; box-shadow: 0 5px 0 #C4B5FD; max-width: 760px; animation: pop .5s ease-out; }
.bubble:before { content: ""; position: absolute; left: -15px; top: 26px; border-style: solid; border-width: 10px 15px 10px 0; border-color: transparent #8B5CF6 transparent transparent; }
.bubble:after { content: ""; position: absolute; left: -9px; top: 29px; border-style: solid; border-width: 7px 11px 7px 0; border-color: transparent #FFFFFF transparent transparent; }
.chip { display: inline-block; padding: 6px 13px; margin: 4px; border-radius: 14px; color: #FFFFFF; font-weight: 800; box-shadow: 0 3px 0 rgba(0,0,0,.2); line-height: 1.3; }
.chip small { display: block; font-size: .66rem; font-weight: 700; opacity: .92; }
.ent { padding: 2px 9px; border-radius: 10px; color: #FFFFFF; font-weight: 800; margin: 0 1px; box-shadow: 0 2px 0 rgba(0,0,0,.2); }
.ent small { font-size: .6rem; margin-left: 5px; background: rgba(0,0,0,.2); padding: 1px 6px; border-radius: 8px; }
.xp-badge { background: linear-gradient(135deg,#F59E0B,#FBBF24); border-radius: 20px; padding: 12px 16px; box-shadow: 0 5px 0 #D97706; margin: 8px 0 14px 0; }
.xp-badge, .xp-badge * { color: #FFFFFF !important; }
.xp-top { display: flex; justify-content: space-between; font-weight: 900; font-size: 1.05rem; }
.xp-sub { font-size: .8rem; font-weight: 700; margin-bottom: 6px; }
.xp-bar { height: 14px; background: rgba(255,255,255,.4); border-radius: 10px; overflow: hidden; }
.xp-fill { height: 100%; background: #FFFFFF; border-radius: 10px; transition: width .6s ease; }
.big-emoji { font-size: 4rem; line-height: 1; animation: pop .6s ease-out; }
.stat { text-align: center; background: #FFFFFF; border-radius: 18px; padding: 12px; border: 2px solid #EDE9FE; box-shadow: 0 4px 0 #DDD6FE; }
.stat b { font-size: 1.8rem; color: #8B5CF6; display: block; }
.good { background: #D1FAE5; border: 2px solid #10B981; border-radius: 14px; padding: 8px 14px; margin: 6px 0; color: #065F46; font-weight: 700; }
.bad { background: #FEE2E2; border: 2px solid #EF4444; border-radius: 14px; padding: 8px 14px; margin: 6px 0; color: #991B1B; font-weight: 700; }
.confetti-piece { position: fixed; top: -24px; width: 10px; height: 16px; z-index: 9999; pointer-events: none; animation-name: fall; animation-timing-function: linear; animation-fill-mode: forwards; }
@keyframes fall { to { transform: translateY(115vh) rotate(720deg); } }
@keyframes pop { 0% { transform: scale(.85); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
@keyframes blink { 0%,90%,100% { transform: scaleY(0); } 93%,97% { transform: scaleY(1); } }
@keyframes flapL { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(-20deg); } }
@keyframes flapR { 0%,100% { transform: rotate(0deg); } 50% { transform: rotate(20deg); } }
@keyframes shadowPulse { 0%,100% { transform: scale(1); opacity: .25; } 50% { transform: scale(.8); opacity: .12; } }
.owl-float { animation: float 3s ease-in-out infinite; }
.owl-shadow { transform-box: fill-box; transform-origin: center; animation: shadowPulse 3s ease-in-out infinite; }
.lid { transform-box: fill-box; transform-origin: center top; transform: scaleY(0); animation: blink 4s infinite; }
.wing { transform-box: fill-box; animation-duration: 1.6s; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }
.wing-l { transform-origin: 90% 15%; animation-name: flapL; }
.wing-r { transform-origin: 10% 15%; animation-name: flapR; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #E0E7FF; padding-bottom: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 14px 14px 0 0; font-weight: 800; font-size: 0.95rem; padding: 10px 18px; background: #FFFFFF; border: 2px solid #EDE9FE; border-bottom: none; color: #6D28D9; transition: all .15s ease; }
.stTabs [data-baseweb="tab"]:hover { background: #F5F3FF; color: #5B21B6; }
.stTabs [aria-selected="true"] { background: #8B5CF6 !important; color: #FFFFFF !important; border-color: #7C3AED !important; }
.stTabs [aria-selected="true"] p { color: #FFFFFF !important; }
.xai-stepper { margin: 14px 0; display: flex; flex-direction: column; gap: 4px; }
.step-card { background: #FFFFFF; border-radius: 20px; padding: 16px 20px; border: 2px solid #EDE9FE; box-shadow: 0 5px 0 #DDD6FE; transition: transform .12s ease, border-color .15s; }
.step-card:hover { transform: translateY(-2px); border-color: #C4B5FD; }
.step-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.step-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: 12px; color: #FFFFFF; font-weight: 900; font-size: 0.88rem; box-shadow: 0 3px 0 rgba(0,0,0,0.15); }
.step-title-text { font-size: 1.05rem; font-weight: 800; color: #4338CA; }
.step-action-box { background: #F8FAFC; border-radius: 14px; padding: 10px 14px; border-left: 4px solid #8B5CF6; font-size: 0.95rem; line-height: 1.5; color: #334155; margin: 8px 0; }
.step-evidence-box { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 0.92rem; color: #475569; margin-top: 6px; }
.evidence-badge { background: #FEF3C7; border: 1.5px solid #FCD34D; color: #92400E; font-weight: 800; padding: 3px 10px; border-radius: 10px; font-size: 0.88rem; }
.step-arrow-row { display: flex; justify-content: center; align-items: center; padding: 2px 0; }
.step-arrow-pill { background: #EDE9FE; color: #6D28D9; font-weight: 800; font-size: 0.82rem; padding: 3px 14px; border-radius: 12px; border: 1px dashed #A78BFA; }
.prompt-card { background: #1E1B4B; border-radius: 18px; padding: 16px 20px; color: #E0E7FF; border: 2px solid #4338CA; margin: 10px 0; }
.prompt-head { font-weight: 800; font-size: 0.95rem; color: #A5B4FC; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; }
.prompt-body { font-family: 'Consolas', 'Courier New', monospace; font-size: 0.88rem; line-height: 1.6; background: #0F172A; padding: 12px 16px; border-radius: 12px; border: 1px solid #334155; color: #F1F5F9; white-space: pre-wrap; word-break: break-word; max-height: 280px; overflow-y: auto; }
.anatomy-callout { background: #EEF2FF; border: 2px solid #C7D2FE; border-radius: 16px; padding: 12px 18px; margin: 10px 0; font-size: 0.93rem; color: #3730A3; line-height: 1.5; }
.diff-container { background: #FFFFFF; border-radius: 22px; border: 2px solid #EDE9FE; box-shadow: 0 6px 0 #DDD6FE; padding: 20px 22px; margin: 16px 0; }
.diff-title { font-size: 1.22rem; font-weight: 900; color: #5B21B6; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.diff-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px; }
@media (max-width: 768px) { .diff-grid { grid-template-columns: 1fr; } }
.diff-box-classic { background: #FFF1F2; border: 2px solid #FECDD3; border-radius: 18px; padding: 16px; box-shadow: 0 4px 0 #FDA4AF; }
.diff-box-llm { background: #F0FDF4; border: 2px solid #BBF7D0; border-radius: 18px; padding: 16px; box-shadow: 0 4px 0 #86EFAC; }
.diff-box-head { font-weight: 900; font-size: 1.02rem; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
.diff-takeaway { background: linear-gradient(135deg, #FEF3C7, #FFFBEB); border: 2px solid #FCD34D; border-radius: 16px; padding: 12px 18px; font-weight: 700; font-size: 0.94rem; color: #92400E; display: flex; align-items: center; gap: 10px; }
"""


def esc(text) -> str:
    """HTML kaçışı; Streamlit'in $...$ LaTeX yorumunu da engeller."""
    return html.escape(str(text)).replace("$", "&#36;")


def flat(markup: str) -> str:
    """Markdown'ın HTML'i kod bloğu sanmaması için satırları birleştirir."""
    return "".join(line.strip() for line in markup.splitlines())


def inject_css() -> None:
    st.markdown("<style>" + CSS.replace("\n", " ") + "</style>", unsafe_allow_html=True)


def owl_svg(size: int = 150) -> str:
    return flat(f"""
<svg class="owl" width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
<ellipse class="owl-shadow" cx="100" cy="192" rx="46" ry="6" fill="#1F2937"/>
<g class="owl-float">
<g class="wing wing-l"><ellipse cx="40" cy="118" rx="20" ry="44" fill="#7C3AED" transform="rotate(12 40 118)"/></g>
<g class="wing wing-r"><ellipse cx="160" cy="118" rx="20" ry="44" fill="#7C3AED" transform="rotate(-12 160 118)"/></g>
<path d="M62 60 L52 16 L92 44 Z" fill="#6D28D9"/>
<path d="M138 60 L148 16 L108 44 Z" fill="#6D28D9"/>
<ellipse cx="100" cy="115" rx="62" ry="68" fill="#8B5CF6"/>
<ellipse cx="100" cy="135" rx="40" ry="44" fill="#EDE9FE"/>
<path d="M80 128 q6 8 12 0 M100 128 q6 8 12 0 M70 146 q6 8 12 0 M90 146 q6 8 12 0 M110 146 q6 8 12 0 M80 164 q6 8 12 0 M100 164 q6 8 12 0" stroke="#C4B5FD" stroke-width="3" fill="none" stroke-linecap="round"/>
<circle cx="74" cy="82" r="25" fill="#FFFFFF" stroke="#F59E0B" stroke-width="5"/>
<circle cx="126" cy="82" r="25" fill="#FFFFFF" stroke="#F59E0B" stroke-width="5"/>
<circle cx="77" cy="84" r="12" fill="#1F2937"/>
<circle cx="123" cy="84" r="12" fill="#1F2937"/>
<circle cx="81" cy="79" r="4.5" fill="#FFFFFF"/>
<circle cx="127" cy="79" r="4.5" fill="#FFFFFF"/>
<circle class="lid" cx="74" cy="82" r="24" fill="#8B5CF6"/>
<circle class="lid" cx="126" cy="82" r="24" fill="#8B5CF6"/>
<path d="M90 100 L110 100 L100 120 Z" fill="#F59E0B"/>
<path d="M80 188 l-6 8 M80 188 l0 9 M80 188 l6 8 M120 188 l-6 8 M120 188 l0 9 M120 188 l6 8" stroke="#F59E0B" stroke-width="4" stroke-linecap="round"/>
<rect x="64" y="30" width="72" height="9" rx="3" fill="#1F2937" transform="rotate(-4 100 34)"/>
<path d="M82 34 L100 22 L118 34 Z" fill="#1F2937"/>
<line x1="136" y1="34" x2="140" y2="52" stroke="#F59E0B" stroke-width="3"/>
<circle cx="140" cy="54" r="4" fill="#F59E0B"/>
</g>
</svg>""")


def owl_bubble(text: str, size: int = 110) -> str:
    """Baykuş + konuşma balonu. Metin güvenli şekilde kaçışlanır."""
    return flat(f'<div class="owl-row">{owl_svg(size)}<div class="bubble">{esc(text)}</div></div>')


def xp_badge(xp: int, level: int, title: str) -> str:
    pct = int((xp % 100))
    return flat(f"""
<div class="xp-badge">
<div class="xp-top"><span>⭐ Seviye {level}</span><span>{xp} XP</span></div>
<div class="xp-sub">{esc(title)}</div>
<div class="xp-bar"><div class="xp-fill" style="width:{pct}%"></div></div>
<div class="xp-sub" style="margin-top:4px">Sonraki seviyeye {100 - pct} XP</div>
</div>""")


def module_header(icon: str, title: str, subtitle: str, c1: str, c2: str) -> str:
    return flat(f"""
<div class="module-header" style="background:linear-gradient(135deg,{c1},{c2})">
<h2>{icon} {esc(title)}</h2><p>{esc(subtitle)}</p></div>""")


def chip(text: str, color: str, sub: str = "") -> str:
    small = f"<small>{esc(sub)}</small>" if sub else ""
    return f'<span class="chip" style="background:{color}">{esc(text)}{small}</span>'


def confetti_html(n: int = 45) -> str:
    colors = ["#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899", "#EF4444"]
    pieces = []
    for _ in range(n):
        pieces.append(
            f'<div class="confetti-piece" style="left:{random.randint(0, 100)}%;'
            f'background:{random.choice(colors)};animation-duration:{random.uniform(2.5, 4.5):.2f}s;'
            f'animation-delay:{random.uniform(0, 1.2):.2f}s"></div>'
        )
    return "<div>" + "".join(pieces) + "</div>"


# ---------------------------------------------------------------- XAI Görselleştirme Bileşenleri
STEP_GRADIENTS = [
    ("linear-gradient(135deg,#6366F1,#8B5CF6)", "#6366F1"),
    ("linear-gradient(135deg,#06B6D4,#0EA5E9)", "#06B6D4"),
    ("linear-gradient(135deg,#F59E0B,#EA580C)", "#F59E0B"),
    ("linear-gradient(135deg,#10B981,#059669)", "#10B981"),
]


def render_decision_pipeline(steps) -> str:
    """LLM reasoning_steps listesini Stepper UI şeklinde HTML olarak çizer."""
    if not steps:
        return '<div class="card">Karar adımları henüz mevcut değil.</div>'
    items_html = []
    total = len(steps)
    for i, s in enumerate(steps):
        num = getattr(s, "step_number", i + 1)
        title = getattr(s, "step_title", f"Adım {num}")
        action = getattr(s, "technical_action", "")
        evidence = getattr(s, "evidence_in_text", "")
        grad, border_col = STEP_GRADIENTS[(num - 1) % len(STEP_GRADIENTS)]
        
        card = (
            f'<div class="step-card" style="border-left: 5px solid {border_col}">'
            f'<div class="step-head">'
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<span class="step-badge" style="background:{grad}">Adım {num}</span>'
            f'<span class="step-title-text">{esc(title)}</span>'
            f'</div>'
            f'<span style="font-size:0.8rem;color:#64748B;font-weight:700">Karar Aşaması {num}/{total}</span>'
            f'</div>'
            f'<div class="step-action-box" style="border-left-color:{border_col}">'
            f'<b>⚙️ Teknik İşlem:</b> {esc(action)}'
            f'</div>'
            f'<div class="step-evidence-box">'
            f'<b>🔎 Metindeki Kanıt / İpucu:</b> <span class="evidence-badge">🏷️ {esc(evidence)}</span>'
            f'</div>'
            f'</div>'
        )
        items_html.append(card)
        if i < total - 1:
            arrow = (
                f'<div class="step-arrow-row">'
                f'<span class="step-arrow-pill">⬇️ Sonraki Muhakeme Adımına Aktarılıyor ⬇️</span>'
                f'</div>'
            )
            items_html.append(arrow)
    return flat(f'<div class="xai-stepper">{"".join(items_html)}</div>')


def render_token_stats(p_tokens: int, c_tokens: int, t_tokens: int, model_name: str, temp: float) -> str:
    """Prompt ve token anatomisi için 4 kolonluk şık istatistik paneli."""
    m_display = esc(model_name or "gemini-3.8-flash")
    return flat(f"""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:12px 0">
  <div class="stat"><b>~{p_tokens}</b>Girdi (Prompt) Token</div>
  <div class="stat"><b>~{c_tokens}</b>Üretilen (Output) Token</div>
  <div class="stat"><b>~{t_tokens}</b>Toplam Token Yükü</div>
  <div class="stat"><b style="font-size:1.25rem">{m_display}</b>Model & Sıcaklık (T={temp})</div>
</div>
""")


def render_prompt_card(title: str, badge_label: str, content: str, explanation: str) -> str:
    """Prompt mühendisliği inceleme kartı."""
    return flat(f"""
<div class="prompt-card">
  <div class="prompt-head">
    <span>{esc(title)}</span>
    <span style="background:rgba(255,255,255,0.15);padding:2px 10px;border-radius:10px;font-size:0.8rem">{esc(badge_label)}</span>
  </div>
  <div class="prompt-body">{esc(content)}</div>
  <div style="margin-top:8px;font-size:0.84rem;color:#C7D2FE;opacity:0.9">💡 {esc(explanation)}</div>
</div>
""")


def render_decision_diff_card(title: str, classic_title: str, classic_text: str, classic_drawback: str,
                              llm_title: str, llm_text: str, llm_step_highlight: str, takeaway: str) -> str:
    """Klasik NLP ile LLM karar mekanizması farkını gösteren karşılaştırma kartı."""
    return flat(f"""
<div class="diff-container">
  <div class="diff-title">⚡ {esc(title)}</div>
  <div class="diff-grid">
    <div class="diff-box-classic">
      <div class="diff-box-head" style="color:#BE123C">⚙️ {esc(classic_title)}</div>
      <p style="margin:4px 0 8px 0;font-size:0.93rem;color:#334155">{esc(classic_text)}</p>
      <div style="background:#FFE4E6;border-radius:10px;padding:8px 10px;font-size:0.86rem;color:#9F1239;font-weight:700">
        ⚠️ <b>Sınır / Eksiklik:</b> {esc(classic_drawback)}
      </div>
    </div>
    <div class="diff-box-llm">
      <div class="diff-box-head" style="color:#047857">🧠 {esc(llm_title)}</div>
      <p style="margin:4px 0 8px 0;font-size:0.93rem;color:#334155">{esc(llm_text)}</p>
      <div style="background:#DCFCE7;border-radius:10px;padding:8px 10px;font-size:0.86rem;color:#166534;font-weight:700">
        ✨ <b>Fark Yaratan Adım:</b> {esc(llm_step_highlight)}
      </div>
    </div>
  </div>
  <div class="diff-takeaway">
    <span style="font-size:1.4rem">🦉</span>
    <div><b>Piku'nun Çıkarımı:</b> {esc(takeaway)}</div>
  </div>
</div>
""")
