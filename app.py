"""NLP Akademisi: Bilge Baykuş ile Doğal Dil İşleme (Streamlit ana uygulaması)."""
import html
import re

import streamlit as st

import classic_nlp as cnlp
import llm_service as llm
from modules_content import LEVEL_TITLES, MODULES, QUIZ_TOPICS, WARMUP_QUESTIONS
from styles_and_owl import (ENTITY_COLORS, POS_COLORS, SENTIMENT_STYLE, chip, confetti_html, esc, flat,
                            inject_css, module_header, owl_bubble, owl_svg, xp_badge,
                            render_decision_diff_card, render_decision_pipeline, render_prompt_card, render_token_stats)

st.set_page_config(page_title="NLP Akademisi · Piku", page_icon="🦉", layout="wide")
inject_css()

MOD = {m["id"]: m for m in MODULES}
NAV = [f"{m['icon']} {m['title']}" for m in MODULES] + ["🏆 Baykuş'un Meydan Okuması"]


# ------------------------------------------------------------------ Durum
def init_state():
    defaults = {
        "xp": 0, "intro_done": False, "intro_step": 0, "profile": [], "awarded": set(), "results": {},
        "tip_counter": 0, "quiz": None, "quiz_submitted": False, "quiz_id": 0, "confetti_shown": set(),
        "nav": NAV[0],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def award_xp(key: str, amount: int) -> bool:
    if key in st.session_state.awarded:
        return False
    st.session_state.awarded.add(key)
    st.session_state.xp += amount
    st.toast(f"+{amount} XP kazandın! ⭐", icon="🎉")
    return True


def level_info():
    xp = st.session_state.xp
    level = xp // 100 + 1
    return level, LEVEL_TITLES[min(level - 1, len(LEVEL_TITLES) - 1)]


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def run_llm(fn, *args, msg="Piku düşünüyor... 🦉"):
    try:
        with st.spinner(msg):
            return fn(*args)
    except llm.LLMError as e:
        st.markdown(owl_bubble("Hay aksi, kanatlarım karıştı! Bir sorun çıktı ama pes etmek yok.", 90), unsafe_allow_html=True)
        st.error(str(e))
    except Exception as e:  # noqa: BLE001
        st.error(f"Beklenmeyen bir hata oluştu: {e}")
    return None


def highlight_html(text: str, items, ignore_case=False) -> str:
    """items: [(ifade, renk, etiket)]. Orijinal metni bozmadan eşleşmeleri rozetle vurgular."""
    flags = re.IGNORECASE if ignore_case else 0
    spans = []
    for phrase, color, tag in sorted(items, key=lambda x: -len(x[0] or "")):
        if not phrase:
            continue
        for m in re.finditer(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, flags=flags):
            s, e = m.span()
            if all(e <= a or s >= b for a, b, _, _ in spans):
                spans.append((s, e, color, tag))
    spans.sort()
    out, pos = [], 0
    for s, e, color, tag in spans:
        out.append(esc(text[pos:s]))
        out.append(f'<span class="ent" style="background:{color}">{esc(text[s:e])}<small>{esc(tag)}</small></span>')
        pos = e
    out.append(esc(text[pos:]))
    return "".join(out).replace("\n", "<br>")


def textbox(inner: str):
    st.markdown(f'<div class="textbox">{inner}</div>', unsafe_allow_html=True)


def render_xai_panel(res, text: str, mod_title: str):
    """Her analiz modülü için 3 sekmeli Açıklanabilir Yapay Zeka (XAI) Paneli."""
    st.markdown('<div style="margin-top:24px"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="border-left:6px solid #8B5CF6;background:linear-gradient(135deg,#FFFFFF,#F5F3FF);padding:16px 22px;margin-bottom:12px">'
        f'<h3 style="margin:0;color:#6D28D9;display:flex;align-items:center;gap:10px">'
        f'<span>🦉</span> Açıklanabilir Yapay Zeka (XAI): LLM Karar Adımları & Arka Plan'
        f'</h3>'
        f'<p style="margin:6px 0 0 0;font-size:0.94rem;color:#4B5563">'
        f'Yapay zekanın kara kutusunu açıyoruz! Aşağıdaki 3 sekmeden modelin adım adım muhakeme zincirini (Chain-of-Thought), '
        f'arka plandaki prompt & token anatomisini ve dönen yapılandırılmış ham JSON çıktısını inceleyebilirsin.'
        f'</p></div>',
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs([
        "🧠 1. Adım Adım Karar Akışı (Görsel Pipeline)",
        "🎛️ 2. Mutfağın Arkası (Prompt & Token Anatomisi)",
        "📦 3. Ham JSON Veri Çıktısı (Structured Output)"
    ])

    with tab1:
        st.markdown(
            '<div style="font-size:0.95rem;color:#4B5563;margin-bottom:10px">'
            '🚀 <b>Düşünce Zinciri (Chain-of-Thought Karar Boru Hattı):</b> '
            'Büyük Dil Modeli son cevaba ulaşmadan önce metin üzerinde sırasıyla şu 4 kritik işlemi gerçekleştirdi:'
            '</div>',
            unsafe_allow_html=True
        )
        steps = getattr(res, "reasoning_steps", [])
        if steps:
            st.markdown(render_decision_pipeline(steps), unsafe_allow_html=True)
        else:
            st.info("Bu analiz çıktısında karar adımları bulunamadı.")

    with tab2:
        meta = getattr(res, "_meta", None) or llm.get_last_metadata()
        p_tok = meta.get("prompt_tokens", 0)
        c_tok = meta.get("candidate_tokens", 0)
        t_tok = meta.get("total_tokens", 0)
        m_name = meta.get("model") or (llm.LAST_MODEL.get("name") or "gemini-3.8-flash")
        temp = meta.get("temperature", 0.3)
        sys_p = meta.get("system_prompt") or llm.SYSTEM_PROMPT
        u_p = meta.get("prompt") or f"METİN:\n{text}"

        st.markdown(
            '<div class="anatomy-callout">'
            '💡 <b>Prompt Mühendisliği & Token Nedir?</b> '
            'Büyük Dil Modelleri (LLM) metinleri tek tek harf ya da kelime olarak değil, ortalama 3-4 karakterlik <b>Token</b> parçaları halinde işler. '
            'Türkçe gibi sondan eklemeli dillerde ekler genellikle ayrı tokenlar olarak temsil edilir (Örn: <i>"gel-ecek-ler-di"</i>). '
            'Modele gönderilen <b>System Prompt</b> baykuş Piku rolünü ve JSON kuralını dikte ederken, '
            '<b>User Prompt</b> metin ve analiz yönergesini taşır.'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(render_token_stats(p_tok, c_tok, t_tok, m_name, temp), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(render_prompt_card(
                "🤖 Arka Plandaki System Prompt",
                "Sabit Sistem Direktifi",
                sys_p,
                "Modelin kişiliğini (Piku), JSON format kuralını ve XAI karar adımları zorunluluğunu belirleyen üst direktif."
            ), unsafe_allow_html=True)
        with c2:
            st.markdown(render_prompt_card(
                "💬 Gönderilen User Prompt (İstek)",
                f"{mod_title} Görevi",
                u_p,
                "Kullanıcının girdiği metin ve LLM'den istenen spesifik 4 adımlı analiz yönergesi."
            ), unsafe_allow_html=True)

    with tab3:
        st.markdown(
            '<div class="card" style="margin-bottom:12px">'
            '<h4>📦 Pydantic ile Doğrulanmış Yapılandırılmış Çıktı (Structured Output)</h4>'
            '<p style="margin:0;font-size:0.92rem;color:#4B5563">'
            'Günümüz modern yapay zeka uygulamalarında modeller sadece serbest metin üretmez; '
            'doğrudan API ve arayüzlere bağlanabilen sıkı <b>JSON şemalarıyla</b> haberleşir. '
            'Aşağıdaki ham JSON verisi modelden gelen orijinal yanıttır; arayüz bu veriyi okuyup görselleştirir.'
            '</p></div>',
            unsafe_allow_html=True
        )
        if hasattr(res, "model_dump"):
            st.json(res.model_dump())
        elif hasattr(res, "dict"):
            st.json(res.dict())
        else:
            st.write(res)


# ------------------------------------------------------------------ Tanışma
def _next():
    st.session_state.intro_step += 1


def _choose(answer, reaction):
    st.session_state.profile.append((answer, reaction))
    st.session_state.intro_step += 1


def _finish():
    st.session_state.intro_done = True
    award_xp("intro", 20)


def _skip():
    st.session_state.intro_done = True


def intro_screen():
    step = st.session_state.intro_step
    n = len(WARMUP_QUESTIONS)
    st.markdown("<div></div>", unsafe_allow_html=True)
    st.progress(min(step / (n + 1), 1.0))

    if step == 0:
        st.markdown(owl_bubble("Merhaba! Ben Piku 🦉 Kelimelerin gizli dünyasını çözmeye hazır mısın?", 190), unsafe_allow_html=True)
        st.markdown(
            '<div class="card"><h4>🎓 NLP Akademisi\'ne hoş geldin!</h4>'
            "Burada <b>5 eğlenceli görevle</b> doğal dil işlemeyi öğrenecek, XP toplayacak ve seviye atlayacaksın. "
            "Önce seni tanımam için 3 minik ısınma sorum var!</div>", unsafe_allow_html=True)
        c1, c2, _ = st.columns([1, 1, 3])
        c1.button("Hazırım! 🚀", type="primary", on_click=_next, key="intro_start")
        c2.button("Tanışmayı atla ⏭️", on_click=_skip, key="intro_skip")
    elif step <= n:
        q = WARMUP_QUESTIONS[step - 1]
        prefix = (st.session_state.profile[-1][1] + " ") if st.session_state.profile else ""
        st.markdown(owl_bubble(prefix + q["q"], 150), unsafe_allow_html=True)
        cols = st.columns(len(q["options"]))
        for i, (col, opt) in enumerate(zip(cols, q["options"])):
            col.button(opt, key=f"warm_{step}_{i}", on_click=_choose, args=(opt, q["reactions"][i]))
        st.caption(f"Soru {step} / {n}")
    else:
        answers = " · ".join(a for a, _ in st.session_state.profile)
        st.markdown(owl_bubble("Harika, seni tanıdım! " + st.session_state.profile[-1][1] + " Hazırsan eğitime başlayalım!", 190), unsafe_allow_html=True)
        st.markdown(f'<div class="card"><h4>📝 Notlarım</h4>{esc(answers)}<br><br>🎁 Tanışma tamamlandı: <b>+20 XP</b> seni bekliyor!</div>', unsafe_allow_html=True)
        st.button("Eğitime Başla 🚀", type="primary", on_click=_finish, key="intro_finish")


# ------------------------------------------------------------------ Ortak bileşenler
def sidebar():
    with st.sidebar:
        st.markdown(f'<div style="text-align:center">{owl_svg(120)}</div>', unsafe_allow_html=True)
        st.markdown("<div style=\"text-align:center;font-weight:900;font-size:1.3rem;color:#6D28D9\">NLP Akademisi</div>", unsafe_allow_html=True)
        level, title = level_info()
        st.markdown(xp_badge(st.session_state.xp, level, title), unsafe_allow_html=True)
        st.radio("🗺️ Görev Haritası", NAV, key="nav")
        if llm.LAST_MODEL["name"]:
            st.caption(f"⚡ Son yanıtlayan model: {llm.LAST_MODEL['name']}")
        st.button("🔄 Baştan başla", on_click=reset_all, key="reset")


def module_top(mod):
    st.markdown(module_header(mod["icon"], mod["title"], mod["subtitle"], mod["c1"], mod["c2"]), unsafe_allow_html=True)
    tips = mod["owl_tips"]
    st.markdown(owl_bubble(tips[st.session_state.tip_counter % len(tips)], 95), unsafe_allow_html=True)
    with st.expander("📖 Mini Ders: Teori"):
        st.markdown(mod["theory"])


def set_text(key, value):
    st.session_state[key] = value


def text_input_block(mod, label, height=120):
    key = f"text_{mod['id']}"
    if key not in st.session_state:
        st.session_state[key] = mod["examples"][0]
    st.caption("⚡ Tek tıkla hazır örnek doldur:")
    cols = st.columns(len(mod["examples"]))
    for i, col in enumerate(cols):
        col.button(f"✨ Örnek {i + 1}", key=f"ex_{mod['id']}_{i}", on_click=set_text, args=(key, mod["examples"][i]),
                   help=mod["examples"][i][:120])
    return st.text_area(label, key=key, height=height)


def store(mod_id, text, result):
    st.session_state.results[mod_id] = (text, result)
    st.session_state.tip_counter += 1
    award_xp(f"mod_{mod_id}", 15)


# ------------------------------------------------------------------ Modül 1
def page_tokenization():
    mod = MOD["tok"]
    module_top(mod)
    text = text_input_block(mod, "✍️ Ameliyat edilecek metin:")
    if st.button("🔬 Ameliyatı Başlat", type="primary", key="go_tok"):
        if not text.strip():
            st.warning("Önce bir metin yaz ya da örnek seç!")
        else:
            res = run_llm(llm.analyze_tokens, text)
            if res:
                store("tok", text, res)
    saved = st.session_state.results.get("tok")
    if not saved:
        return
    text, res = saved
    st.markdown(owl_bubble(res.owl_comment, 90), unsafe_allow_html=True)
    st.subheader("🧬 LLM'in morfolojik ameliyatı")
    chips = ""
    for t in res.tokens:
        color = POS_COLORS.get(t.pos, POS_COLORS["Diğer"])
        parts = t.root + (" + " + " + ".join(t.suffixes) if t.suffixes else "")
        chips += chip(t.token, color, f"{t.pos} · {parts}")
    textbox(chips)
    legend = "".join(chip(k, v) for k, v in POS_COLORS.items() if k != "Diğer")
    st.markdown(f'<div>{legend}</div>', unsafe_allow_html=True)
    st.dataframe([{"Kelime": t.token, "Kök": t.root, "Ekler": " + ".join(t.suffixes) or "-", "Tür": t.pos, "Not": t.note}
                  for t in res.tokens], hide_index=True)

    render_xai_panel(res, text, "Tokenization & Morfoloji")

    st.subheader("⚔️ Klasik yöntemle kıyaslama")
    ws, rx = cnlp.whitespace_tokenize(text), cnlp.regex_tokenize(text)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat"><b>{len(ws)}</b>Boşluk ayırma</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat"><b>{len(rx)}</b>Regex tokenizer</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat"><b>{len(res.tokens)}</b>LLM (morfolojik)</div>', unsafe_allow_html=True)
    st.markdown("**Boşluk ayırma sonucu** (noktalama yapışık kalır, ekler görünmez):")
    textbox("".join(chip(w, "#94A3B8") for w in ws))
    rows = []
    for w in ws:
        root, suf = cnlp.simple_stem(w)
        rows.append({"Kelime": w, "Klasik kök tahmini": root, "Klasik ekler": " + ".join(suf) or "-"})
    with st.expander("🔎 Klasik sonek kırpma (stemmer) sonucu"):
        st.dataframe(rows, hide_index=True)
        st.caption("Klasik stemmer bağlamı bilmediği için kökü fazla ya da eksik kırpabilir. LLM sonuçlarıyla karşılaştır!")

    st.markdown(render_decision_diff_card(
        title="Karar Mekanizması Farkı: Kural Tabanlı Kırpma vs. LLM Morfolojisi",
        classic_title="Klasik Kural Tabanlı Stemmer (Sonek Kırpıcı)",
        classic_text="Kelimelerin sonundan sabit bir ek listesindeki harf dizilerini (örn. -ler, -den, -dir) mekanik olarak budar. Kelimenin cümledeki görevini (isim mi fiil mi olduğunu) ve bağlamını bilmez.",
        classic_drawback="Aşırı kırpma (over-stemming) veya yetersiz kırpma yapar. Noktalama işaretini kelimeye yapışık sanabilir, kökün anlamını bozar.",
        llm_title="LLM Bilişsel Morfolojik Çözümleme",
        llm_text="Transformer dikkat (attention) mekanizmasıyla cümlenin tamamını tarar. Cümledeki özne-yüklem ilişkisini, zaman eklerini ve kelime türünü (POS) bir arada muhakeme eder.",
        llm_step_highlight="2. Morfem & Kök Sınırı Ayrıştırma ve 3. Ek Sıralaması Denetimi adımlarında dilbilgisel bağlamı kavrayarak kök ve ekleri hatasız ayırdı.",
        takeaway="Klasik yöntem kelimeyi mekanik bir makasla keser; LLM ise kelimenin cümledeki rolünü ve anlamını anlayarak morfolojik ameliyat yapar!"
    ), unsafe_allow_html=True)


# ------------------------------------------------------------------ Modül 2
def page_sentiment():
    mod = MOD["sent"]
    module_top(mod)
    text = text_input_block(mod, "✍️ Yorum ya da cümle:", 100)
    if st.button("🕵️ Duyguyu Çöz", type="primary", key="go_sent"):
        if not text.strip():
            st.warning("Önce bir metin yaz ya da örnek seç!")
        else:
            res = run_llm(llm.analyze_sentiment, text)
            if res:
                store("sent", text, res)
    saved = st.session_state.results.get("sent")
    if not saved:
        return
    text, res = saved
    default_emoji, color = SENTIMENT_STYLE.get(res.sentiment, ("🤔", "#8B5CF6"))
    conf = res.confidence / 100 if res.confidence > 1 else res.confidence
    conf = max(0.0, min(1.0, conf))
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(flat(f'<div class="card" style="text-align:center;border-color:{color};box-shadow:0 6px 0 {color}55">'
                         f'<div class="big-emoji">{esc(res.emoji or default_emoji)}</div>'
                         f'<h3 style="color:{color};margin:6px 0">{esc(res.sentiment)}</h3>'
                         f'Güven skoru: <b>%{int(conf * 100)}</b></div>'), unsafe_allow_html=True)
        st.progress(conf)
    with c2:
        items = [(w, "#F59E0B", "zıtlık") for w in res.contrast_words]
        items += [(p, "#10B981", "+") for p in res.positive_phrases]
        items += [(p, "#EF4444", "−") for p in res.negative_phrases]
        st.markdown("**🔦 Dedektifin işaretlediği ipuçları:**")
        textbox(highlight_html(text, items, ignore_case=True))
    st.markdown("**🦉 Neden bu duygu çıktı?**")
    st.markdown(owl_bubble(res.explanation, 110), unsafe_allow_html=True)

    render_xai_panel(res, text, "Duygu Analizi")

    st.subheader("⚔️ Klasik kural tabanlı yöntemle kıyaslama")
    cl = cnlp.rule_based_sentiment(text)
    cemoji, ccolor = SENTIMENT_STYLE.get(cl["label"], ("🤔", "#8B5CF6"))
    agree = cl["label"] == res.sentiment
    st.markdown(flat(f'<div class="card"><h4>📚 Sözlük tabanlı sonuç: <span style="color:{ccolor}">{cemoji} {cl["label"]}</span></h4>'
                     f'Olumlu puan: <b>{cl["pos"]}</b> · Olumsuz puan: <b>{cl["neg"]}</b> · '
                     f'Yakalanan zıtlık bağlacı: <b>{esc(", ".join(cl["contrast"]) or "yok")}</b></div>'), unsafe_allow_html=True)
    if agree:
        st.success("İki yöntem aynı sonucu verdi. Daha karmaşık, ironik bir cümle deneyip farkı görmek ister misin?")
    else:
        st.info("Yöntemler farklı sonuç verdi! Klasik yöntem kelime sayar, LLM ise cümlenin bütününü okur.")

    st.markdown(render_decision_diff_card(
        title="Karar Mekanizması Farkı: Sözlük Tabanlı Sayım vs. LLM Anlamsal Muhakeme",
        classic_title="Klasik Sözlük Tabanlı Yöntem (Bag-of-Words)",
        classic_text="Metindeki olumlu ve olumsuz kelimeleri statik sözlük listesinden eşleştirip sayar (+1 / -1). 'Film harikaydı ama senaryo çok sıktı' cümlesinde 'harika' (+1) ve 'sıktı' (-1) kelimelerini basitçe toplayıp sıfırlayabilir.",
        classic_drawback="Zıtlık bağlaçlarındaki (ama, fakat, ancak) vurgu kaymasını ve ironiyi ('Harika, yine geç kaldın') yüzeysel ağırlıklarla veya hatalı etiketle çözer.",
        llm_title="LLM Bilişsel Duygu Çıkarımı",
        llm_text="Tüm cümlenin bağlam haritasını çıkarır. Zıtlık bağlacının oluşturduğu anlamsal eksen kaymasını ve ana cümlenin (main clause) taşıdığı asıl niyeti kavrar.",
        llm_step_highlight="2. Anlamsal İlişki ve Bağlaç Tespiti ile 3. Güven Ağırlıklandırması adımlarında bağlacın ardından gelen asıl yargıya odaklanarak doğru etiketi belirledi.",
        takeaway="Klasik yöntem kelimeleri torbaya atıp sayar; LLM ise cümlenin vurgusunu, bağlaçların yarattığı zıtlığı ve asıl hissiyatı bütünsel olarak anlar!"
    ), unsafe_allow_html=True)


# ------------------------------------------------------------------ Modül 3
def page_ner():
    mod = MOD["ner"]
    module_top(mod)
    text = text_input_block(mod, "✍️ İsim avlanacak metin:", 100)
    if st.button("🏷️ İsimleri Avla", type="primary", key="go_ner"):
        if not text.strip():
            st.warning("Önce bir metin yaz ya da örnek seç!")
        else:
            res = run_llm(llm.analyze_ner, text)
            if res:
                store("ner", text, res)
    saved = st.session_state.results.get("ner")
    if not saved:
        return
    text, res = saved
    st.markdown(owl_bubble(res.owl_comment, 90), unsafe_allow_html=True)
    legend = "".join(chip(k, v) for k, v in ENTITY_COLORS.items())
    st.markdown(f"<div>{legend}</div>", unsafe_allow_html=True)
    st.subheader("🤖 LLM'in avı")
    items = [(e.text, ENTITY_COLORS.get(e.label, "#94A3B8"), e.label) for e in res.entities]
    textbox(highlight_html(text, items))
    st.dataframe([{"Varlık": e.text, "Tür": e.label} for e in res.entities], hide_index=True)

    render_xai_panel(res, text, "Varlık İsmi Tanıma (NER)")

    st.subheader("⚔️ Klasik kural tabanlı yöntem")
    classic = cnlp.rule_based_ner(text)
    textbox(highlight_html(text, [(d["text"], ENTITY_COLORS.get(d["label"], "#94A3B8"), d["label"]) for d in classic]))
    llm_set = {e.text.lower() for e in res.entities}
    classic_set = {d["text"].lower() for d in classic}
    missed = sorted(llm_set - classic_set)
    extra = sorted(classic_set - llm_set)
    c1, c2 = st.columns(2)
    c1.markdown(f'<div class="stat"><b>{len(missed)}</b>Sadece LLM\'in bulduğu</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat"><b>{len(extra)}</b>Sadece klasiğin bulduğu</div>', unsafe_allow_html=True)
    if missed:
        st.caption("LLM'in yakaladığı ama klasik yöntemin kaçırdığı: " + ", ".join(missed))
    if extra:
        st.caption("Klasik yöntemin işaretlediği ama LLM'in saymadığı (muhtemel yanlış alarm): " + ", ".join(extra))

    st.markdown(render_decision_diff_card(
        title="Karar Mekanizması Farkı: Regex & Gazeteer Sözlüğü vs. LLM Varlık Çıkarımı",
        classic_title="Klasik Regex & Sabit Sözlük (Gazetteer)",
        classic_text="Önceden tanımlı sabit şehir listeleriyle ve 'Büyük Harfle Başlayan Kelimeler' kuralıyla arama yapar. Cümle başındaki sıradan kelimeleri büyük harf yüzünden kişi veya yer sanabilir.",
        classic_drawback="Listede yer almayan yeni kişi ve kurumları kaçırır. 'Gül' gibi hem çiçek hem kişi adı olan kelimeleri veya 'Can' gibi hem isim hem fiil olan kelimeleri ayırt edemez.",
        llm_title="LLM Bilişsel Varlık Ayrımı (Contextual NER)",
        llm_text="Kelimenin cümledeki eylemini (katıldı, yönetti, gitti), kesme işaretli eklerini ve sözdizimsel rolünü inceleyerek varlık türünü bağlamdan çıkarır.",
        llm_step_highlight="2. Sözdizimsel Rol & Ek Ayrımı ve 3. Varlık Türü Eşleme adımlarında özel ismin bağlamdaki işlevini doğrulamayı başardı.",
        takeaway="Klasik yöntem sabit bir ezber sözlüğüdür; LLM ise daha önce hiç görmediği bir özel ismi bile cümledeki rolünden tanıyan bir dedektiftir!"
    ), unsafe_allow_html=True)


# ------------------------------------------------------------------ Modül 4
def page_summary():
    mod = MOD["sum"]
    module_top(mod)
    text = text_input_block(mod, "✍️ Özetlenecek uzun metin:", 220)
    if st.button("✂️ Özetle", type="primary", key="go_sum"):
        if len(text.strip()) < 40:
            st.warning("Özetlemek için biraz daha uzun bir metin lazım!")
        else:
            res = run_llm(llm.summarize_text, text)
            if res:
                store("sum", text, res)
    saved = st.session_state.results.get("sum")
    if not saved:
        return
    text, res = saved
    st.markdown(owl_bubble(res.owl_comment, 90), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        bullets = "".join(f"<li>{esc(s)}</li>" for s in res.extractive_sentences)
        st.markdown(f'<div class="card" style="border-color:#06B6D4"><h4>🖍️ Çıkarımsal Özet</h4><ul>{bullets}</ul></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card" style="border-color:#8B5CF6"><h4>🪄 Soyutlayıcı Özet</h4>{esc(res.abstractive_summary)}</div>', unsafe_allow_html=True)
    st.markdown("**🔑 En önemli 5 anahtar kavram:**")
    palette = list(ENTITY_COLORS.values()) + ["#EC4899"]
    st.markdown("<div>" + "".join(chip(k, palette[i % len(palette)]) for i, k in enumerate(res.keywords[:5])) + "</div>", unsafe_allow_html=True)

    render_xai_panel(res, text, "Metin Özetleme")

    st.subheader("⚔️ Klasik (kelime sıklığı) yöntemle kıyaslama")
    ex = cnlp.extractive_summary(text, 2)
    kw = cnlp.keywords(text, 5)
    st.markdown(f'<div class="card"><h4>📊 Frekans tabanlı çıkarımsal özet</h4>{esc(" ".join(ex))}'
                f'<br><br><b>Sık geçen kelimeler:</b> {esc(", ".join(kw))}</div>', unsafe_allow_html=True)
    st.caption("Klasik yöntem sık geçen kelimelere bakar; LLM ise konunun anlamına. Anahtar kelimeleri karşılaştır!")

    st.markdown(render_decision_diff_card(
        title="Karar Mekanizması Farkı: Kelime Frekansı (TF) vs. LLM Anlamsal Yoğunluk & Sentez",
        classic_title="Klasik Frekans Tabanlı Özetleme (TF / Kelime Sayımı)",
        classic_text="Metinde en çok tekrarlanan kelimeleri sayar ve bu kelimeleri en çok içeren cümleleri metinden cımbızlayarak yan yana koyar (çıkarımsal).",
        classic_drawback="Asla yeni bir cümle kuramaz (soyutlayıcı özet yapamaz). Eşanlamlı kelimeleri birleştiremez ve metnin akış bütünlüğünü kuramaz.",
        llm_title="LLM Bilişsel Özetleme & Soyutlama (Abstractive)",
        llm_text="Tüm metnin semantik temsilini kavrar; ana fikirleri, neden-sonuç ilişkilerini ve çekirdek kavramları sentezleyip insan gibi akıcı yeni cümlelerle özetler.",
        llm_step_highlight="2. Bilgi Yoğunluğu Haritalama ve 3. Soyut Sentez adımlarında hem en önemli orijinal cümleleri süzdü hem de yepyeni bir soyutlayıcı özet üretti.",
        takeaway="Klasik yöntem metnin üzerine fosforlu kalemle rastgele çizik atar; LLM ise metni okuyup anlar ve kendi cümleleriyle bir hikaye gibi özetler!"
    ), unsafe_allow_html=True)


# ------------------------------------------------------------------ Modül 5
def _new_quiz(topic_text):
    quiz = run_llm(llm.generate_quiz, topic_text, msg="Piku sorularını hazırlıyor... 🦉")
    if quiz:
        st.session_state.quiz_id += 1
        st.session_state.quiz = quiz
        st.session_state.quiz_submitted = False


def page_quiz():
    st.markdown(module_header("🏆", "Baykuş'un Meydan Okuması", "AI Mini Quiz · Doğru cevap = +20 XP", "#EF4444", "#F59E0B"), unsafe_allow_html=True)
    st.markdown(owl_bubble("Bilgini test etme vakti! Bir konu seç, sorularımı o an yapay zekayla üreteyim. Hazır mısın? 🧠", 95), unsafe_allow_html=True)
    topic = st.selectbox("📚 Konu seç:", list(QUIZ_TOPICS.keys()))
    if st.button("🎲 Yeni Test Üret", type="primary", key="gen_quiz"):
        _new_quiz(QUIZ_TOPICS[topic])
    quiz = st.session_state.quiz
    if not quiz:
        return
    qid, submitted = st.session_state.quiz_id, st.session_state.quiz_submitted
    answers = []
    for i, q in enumerate(quiz.questions):
        st.markdown(f'<div class="card"><h4>Soru {i + 1}</h4>{esc(q.question)}</div>', unsafe_allow_html=True)
        ans = st.radio("Cevabın", list(range(len(q.options))), format_func=lambda j, q=q: q.options[j], index=None,
                       key=f"quiz_{qid}_{i}", disabled=submitted, label_visibility="collapsed")
        answers.append(ans)
        if submitted:
            correct = min(max(q.correct_index, 0), len(q.options) - 1)
            if ans == correct:
                st.markdown(f'<div class="good">✅ Doğru! {esc(q.explanation)}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bad">❌ Doğru cevap: {esc(q.options[correct])}. {esc(q.explanation)}</div>', unsafe_allow_html=True)
    if not submitted:
        if st.button("✅ Cevapları Kontrol Et", type="primary", key="check_quiz"):
            if any(a is None for a in answers):
                st.warning("Önce tüm soruları cevapla!")
            else:
                st.session_state.quiz_submitted = True
                for i, (a, q) in enumerate(zip(answers, quiz.questions)):
                    if a == min(max(q.correct_index, 0), len(q.options) - 1):
                        award_xp(f"quiz{qid}_{i}", 20)
                st.rerun()
        return
    score = sum(1 for i, q in enumerate(quiz.questions)
                if st.session_state.get(f"quiz_{qid}_{i}") == min(max(q.correct_index, 0), len(q.options) - 1))
    total = len(quiz.questions)
    if score == total:
        msg = f"MÜKEMMEL! {score}/{total} 🎉 Sen bir NLP dehasısın, kanatlarım çırpınıyor!"
    elif score > 0:
        msg = f"Güzel iş! {score}/{total} doğru. Biraz daha pratikle zirvedesin! 💪"
    else:
        msg = f"{score}/{total}... Olsun, baykuşlar da gece öğrenir! Modülleri gezip tekrar dene. 🌙"
    st.markdown(owl_bubble(msg, 120), unsafe_allow_html=True)
    if score >= 1 and qid not in st.session_state.confetti_shown:
        st.session_state.confetti_shown.add(qid)
        st.markdown(confetti_html(), unsafe_allow_html=True)
        if score >= 2:
            st.balloons()
    st.button("🔁 Yeni test üret", on_click=_new_quiz, args=(QUIZ_TOPICS[topic],), key="again_quiz")


# ------------------------------------------------------------------ Ana akış
init_state()
if not st.session_state.intro_done:
    intro_screen()
else:
    sidebar()
    pages = {NAV[0]: page_tokenization, NAV[1]: page_sentiment, NAV[2]: page_ner, NAV[3]: page_summary,
             NAV[4]: page_quiz}
    pages[st.session_state.nav]()
