"""Hızlı yanıtlı, otomatik model geçişli (fallback) Gemini servisi.

- google-genai SDK
- thinking_budget=0 ile düşünme süresi kapatılır (desteklemeyen modelde güvenli geri dönüş)
- 404 / 503 / 429 vb. hatalarda ~0.5 sn içinde listedeki sıradaki modele geçilir
- Tüm çıktılar Pydantic şemalarıyla kesin JSON olarak alınır
"""
import os
import time
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

MODEL_CHAIN = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]
RETRY_DELAY = 0.5  # saniye (404'te beklemeden geçilir)
LAST_MODEL = {"name": None}
LAST_METADATA = {
    "model": None,
    "system_prompt": "",
    "prompt": "",
    "raw_json": "",
    "prompt_tokens": 0,
    "candidate_tokens": 0,
    "total_tokens": 0,
    "temperature": 0.3,
}

SYSTEM_PROMPT = (
    "Sen 'Piku' adında sevimli, neşeli ve bilgili bir baykuşsun ve Doğal Dil İşleme (NLP) öğretiyorsun. "
    "Yalnızca istenen JSON şemasına uygun yanıt ver. Metinler Türkçe, kısa, net ve eğlenceli olsun; "
    "emojiyi ölçülü kullan. Analizlerde metindeki orijinal yazımı bozma. "
    "Açıklanabilir Yapay Zeka (XAI) gereği istenen 4 adımlı reasoning_steps karar adımlarını eksiksiz doldur."
)


class LLMError(Exception):
    """Tüm modeller başarısız olduğunda ya da API anahtarı yokken fırlatılır."""


# ---------------------------------------------------------------- Şemalar
class ReasoningStep(BaseModel):
    step_number: int = Field(description="Adım sıra numarası (1, 2, 3 veya 4)")
    step_title: str = Field(description="Adım başlığı (örn: '1. Ön İşleme & Bağlam Tarama', '2. Anlamsal İlişki Tespiti')")
    technical_action: str = Field(description="LLM'in bu adımda metin üzerinde tam olarak hangi dilsel/istatistiksel işlemi yaptığının teknik özeti")
    evidence_in_text: str = Field(description="Metinden hangi kelime veya ifadeyi kanıt olarak yakaladığı")


class TokenItem(BaseModel):
    token: str = Field(description="Metindeki kelime ya da noktalama işareti (orijinal yazımıyla)")
    root: str = Field(description="Kelimenin kökü / lemması")
    suffixes: List[str] = Field(description="Köke eklenen ekler sırayla; ek yoksa boş liste")
    pos: str = Field(description="İsim, Fiil, Sıfat, Zarf, Zamir, Bağlaç, Edat, Ünlem, Sayı, Noktalama veya Diğer")
    note: str = Field(description="Ekin ya da kelimenin işlevini anlatan çok kısa not")


class TokenizationResult(BaseModel):
    reasoning_steps: List[ReasoningStep] = Field(description="Morfolojik analize adım adım nasıl ulaşıldığını gösteren 4 adımlı karar süreci")
    tokens: List[TokenItem]
    owl_comment: str = Field(description="Piku'nun bu metin hakkındaki kısa, eğlenceli yorumu")


class SentimentResult(BaseModel):
    reasoning_steps: List[ReasoningStep] = Field(description="Duygu etiketine adım adım nasıl ulaşıldığını gösteren 4 adımlı karar süreci")
    sentiment: str = Field(description="Tam olarak: Pozitif, Negatif, Nötr veya Karma")
    confidence: float = Field(description="0 ile 1 arasında güven skoru")
    emoji: str = Field(description="Duyguyu yansıtan tek emoji")
    contrast_words: List[str] = Field(description="Metindeki zıtlık bağlaçları (ama, fakat, ancak...) birebir yazımıyla")
    positive_phrases: List[str] = Field(description="Metinde birebir geçen pozitif ifadeler")
    negative_phrases: List[str] = Field(description="Metinde birebir geçen negatif ifadeler")
    explanation: str = Field(description="Piku ağzından 'Neden bu duygu çıktı?' açıklaması, 2-3 cümle")


class Entity(BaseModel):
    text: str = Field(description="Metinde birebir geçen varlık ifadesi (ek almadan, yalın hali)")
    label: str = Field(description="Tam olarak: Kişi, Yer, Kurum veya Tarih")


class NERResult(BaseModel):
    reasoning_steps: List[ReasoningStep] = Field(description="Varlıkları tespit ederken izlenen 4 adımlı karar süreci")
    entities: List[Entity]
    owl_comment: str


class SummaryResult(BaseModel):
    reasoning_steps: List[ReasoningStep] = Field(description="Özeti çıkarırken ve soyutlarken izlenen 4 adımlı karar süreci")
    extractive_sentences: List[str] = Field(description="Metinden birebir seçilmiş en önemli 2-3 cümle")
    abstractive_summary: str = Field(description="Metnin kendi cümlelerinle yazılmış 2-3 cümlelik özeti")
    keywords: List[str] = Field(description="En önemli 5 anahtar kelime/kavram")
    owl_comment: str


class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(description="Tam 4 seçenek")
    correct_index: int = Field(description="Doğru seçeneğin 0 tabanlı indeksi")
    explanation: str = Field(description="Doğru cevabın kısa ve eğlenceli açıklaması")


class QuizResult(BaseModel):
    questions: List[QuizQuestion] = Field(description="Tam 3 soru")
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list, description="Soru üretim karar adımları (opsiyonel)")


# ---------------------------------------------------------------- Çekirdek
_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise LLMError("API anahtarı bulunamadı. Proje klasörüne .env dosyası açıp GEMINI_API_KEY=... yaz.")
        _client = genai.Client(api_key=key)
    return _client


def _make_config(schema, temperature: float, use_thinking: bool):
    kwargs = dict(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        max_output_tokens=4096,
    )
    if use_thinking:
        kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    return types.GenerateContentConfig(**kwargs)


def _status(err: Exception):
    return getattr(err, "code", None) or getattr(err, "status_code", None)


def get_last_metadata() -> dict:
    return dict(LAST_METADATA)


def call_structured(prompt: str, schema, temperature: float = 0.3):
    """Modelleri sırayla dener; ilk başarılı yanıtı Pydantic nesnesi olarak döndürür."""
    client = _get_client()
    errors = []
    for model in MODEL_CHAIN:
        for use_thinking in (True, False):
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt, config=_make_config(schema, temperature, use_thinking)
                )
                parsed = getattr(resp, "parsed", None)
                result = parsed if isinstance(parsed, schema) else schema.model_validate_json(resp.text)
                LAST_MODEL["name"] = model

                # Token ve çalışma metriklerini kaydet (XAI Mutfağın Arkası)
                usage = getattr(resp, "usage_metadata", None)
                p_tokens = getattr(usage, "prompt_token_count", None) if usage else None
                c_tokens = getattr(usage, "candidates_token_count", None) if usage else None
                t_tokens = getattr(usage, "total_token_count", None) if usage else None

                raw_text_resp = getattr(resp, "text", "") or ""
                approx_input = p_tokens or max(1, int(len((SYSTEM_PROMPT + " " + prompt).split()) * 1.4))
                approx_output = c_tokens or max(1, int(len(raw_text_resp.split()) * 1.3))
                total_tok = t_tokens or (approx_input + approx_output)

                meta = {
                    "model": model,
                    "system_prompt": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "raw_json": raw_text_resp,
                    "prompt_tokens": approx_input,
                    "candidate_tokens": approx_output,
                    "total_tokens": total_tok,
                    "temperature": temperature,
                }
                LAST_METADATA.update(meta)
                try:
                    result._meta = meta
                except Exception:
                    pass
                return result
            except Exception as e:  # noqa: BLE001 - her hatada yedek modele geçilir
                errors.append(f"{model}: {type(e).__name__} {_status(e) or ''}")
                if use_thinking and "thinking" in str(e).lower():
                    continue  # aynı modeli düşünme ayarı olmadan dene
                if _status(e) != 404:
                    time.sleep(RETRY_DELAY)
                break
    raise LLMError("Şu an hiçbir model yanıt veremedi (" + " | ".join(errors[-3:]) + "). Biraz sonra tekrar dene.")


# ---------------------------------------------------------------- Modüller
def analyze_tokens(text: str) -> TokenizationResult:
    prompt = (
        "Aşağıdaki metni morfolojik olarak tokenlarına ayır (kelimeler ve noktalama ayrı token). "
        "Her token için kök, ekler (sırayla), sözcük türü ve kısa not ver. Metnin dili neyse o dilin kurallarını uygula.\n\n"
        "AÇIKLANABİLİR YAPAY ZEKA (XAI) KARAR BORU HATTI:\n"
        "Yapay zekanın bu morfolojik sonuca adım adım nasıl ulaştığını gösteren tam 4 adet açıklayıcı 'reasoning_steps' üret:\n"
        "1. Ön İşleme & Karakter/Boşluk Tespiti (step_number=1, technical_action='...', evidence_in_text='...')\n"
        "2. Morfem & Kök Sınırı Ayrıştırma (step_number=2, technical_action='...', evidence_in_text='...')\n"
        "3. Ek Sıralaması & Biçimbirim Denetimi (step_number=3, technical_action='...', evidence_in_text='...')\n"
        "4. Sözcük Türü (POS) ve Nihai Doğrulama (step_number=4, technical_action='...', evidence_in_text='...')\n"
        "Her adım kısa, teknik ve eğitici olsun.\n\n"
        f"METİN:\n{text}"
    )
    return call_structured(prompt, TokenizationResult)


def analyze_sentiment(text: str) -> SentimentResult:
    prompt = (
        "Metnin duygu durumunu çıkar. Zıtlık bağlaçlarına (ama, fakat, ancak, lakin...) özellikle dikkat et; "
        "hem olumlu hem olumsuz yargı varsa 'Karma' de. Açıklamayı Piku ağzından, neden bu sonucun çıktığını anlatarak yaz.\n\n"
        "AÇIKLANABİLİR YAPAY ZEKA (XAI) KARAR BORU HATTI:\n"
        "Yapay zekanın bu duygu kararına adım adım nasıl ulaştığını gösteren tam 4 adet açıklayıcı 'reasoning_steps' üret:\n"
        "1. Ön İşleme & Bağlam Tarama (step_number=1, technical_action='...', evidence_in_text='...')\n"
        "2. Anlamsal İlişki ve Bağlaç Tespiti (step_number=2, technical_action='...', evidence_in_text='...')\n"
        "3. Olasılık/Güven Ağırlıklandırması (step_number=3, technical_action='...', evidence_in_text='...')\n"
        "4. Nihai Etiketleme Kararı (step_number=4, technical_action='...', evidence_in_text='...')\n"
        "Her adım kısa, teknik ve eğitici olsun.\n\n"
        f"METİN:\n{text}"
    )
    return call_structured(prompt, SentimentResult)


def analyze_ner(text: str) -> NERResult:
    prompt = (
        "Metindeki varlık isimlerini bul: Kişi, Yer, Kurum, Tarih. 'text' alanına varlığı metinde geçtiği yazımla, "
        "ekleri (Ankara'da → Ankara) çıkararak yaz. Aynı varlığı tekrar listeleme.\n\n"
        "AÇIKLANABİLİR YAPAY ZEKA (XAI) KARAR BORU HATTI:\n"
        "Yapay zekanın varlık tespitine adım adım nasıl ulaştığını gösteren tam 4 adet açıklayıcı 'reasoning_steps' üret:\n"
        "1. Yüzey Biçim & Büyük Harf / İfade Taraması (step_number=1, technical_action='...', evidence_in_text='...')\n"
        "2. Sözdizimsel Rol & Ek Ayrımı (step_number=2, technical_action='...', evidence_in_text='...')\n"
        "3. Varlık Türü Eşleme & Anlamsal Doğrulama (step_number=3, technical_action='...', evidence_in_text='...')\n"
        "4. Nihai Varlık Filtreleme Kararı (step_number=4, technical_action='...', evidence_in_text='...')\n"
        "Her adım kısa, teknik ve eğitici olsun.\n\n"
        f"METİN:\n{text}"
    )
    return call_structured(prompt, NERResult)


def summarize_text(text: str) -> SummaryResult:
    prompt = (
        "Metni iki şekilde özetle: (1) Çıkarımsal: metinden birebir kopyalanmış en önemli 2-3 cümle. "
        "(2) Soyutlayıcı: kendi cümlelerinle 2-3 cümlelik özet. Ayrıca en önemli 5 anahtar kavramı ver.\n\n"
        "AÇIKLANABİLİR YAPAY ZEKA (XAI) KARAR BORU HATTI:\n"
        "Yapay zekanın bu özetleme kararına adım adım nasıl ulaştığını gösteren tam 4 adet açıklayıcı 'reasoning_steps' üret:\n"
        "1. Metin Segmentasyonu & Çekirdek Cümle Taraması (step_number=1, technical_action='...', evidence_in_text='...')\n"
        "2. Bilgi Yoğunluğu & Kavram Haritalama (step_number=2, technical_action='...', evidence_in_text='...')\n"
        "3. Çıkarımsal Aday Seçimi & Soyut Sentez (step_number=3, technical_action='...', evidence_in_text='...')\n"
        "4. Akıcılık & Bütünlük Kontrolü (step_number=4, technical_action='...', evidence_in_text='...')\n"
        "Her adım kısa, teknik ve eğitici olsun.\n\n"
        f"METİN:\n{text}"
    )
    return call_structured(prompt, SummaryResult)


def generate_quiz(topic: str) -> QuizResult:
    prompt = (
        f"'{topic}' konusunda üniversite öğrencileri için eğlenceli, net ve tek doğru cevaplı 3 soruluk çoktan seçmeli "
        "test üret. Her soruda tam 4 seçenek olsun, doğru cevabın yeri rastgele dağılsın, açıklamalar kısa olsun."
    )
    return call_structured(prompt, QuizResult, temperature=0.9)
