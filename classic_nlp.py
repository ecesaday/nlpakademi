"""LLM ile kıyaslama için klasik, kural tabanlı NLP fonksiyonları (API gerektirmez)."""
import re
from collections import Counter

STOPWORDS = {
    "ve", "ile", "bir", "bu", "şu", "o", "da", "de", "ki", "mi", "mı", "mu", "mü", "için", "gibi", "çok", "daha",
    "en", "ama", "fakat", "ancak", "ya", "veya", "hem", "ise", "olarak", "olan", "her", "tüm", "bunun", "ise",
    "kadar", "göre", "sonra", "önce", "ayrıca", "üzerinde", "içinde", "bile", "ne", "nasıl", "ben", "sen", "biz",
    "onlar", "var", "yok", "olan", "oldu", "olduğu", "eden", "edilir", "edilen", "the", "and", "of", "to", "in",
}

POSITIVE = ["güzel", "harika", "mükemmel", "muhteşem", "süper", "iyi", "başarılı", "mutlu", "memnun", "sev",
            "keyif", "eğlenceli", "hoş", "nefis", "tavsiye", "kaliteli", "hızlı", "etkileyici", "bayıl", "beğen"]
NEGATIVE = ["kötü", "berbat", "rezalet", "sıkıcı", "sıktı", "üzgün", "üzül", "nefret", "yavaş", "pahalı", "bozuk",
            "korkunç", "başarısız", "sorun", "yetersiz", "geç", "rezil", "kırıl", "bık", "şikayet"]
CONTRAST = ["ama", "fakat", "ancak", "lakin", "oysa", "yalnız"]
NEGATION = ["değil", "yok"]

MONTHS = "Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık"
PLACES = ["Ankara", "İstanbul", "İzmir", "Mersin", "Bursa", "Antalya", "Adana", "Konya", "Samsun", "Trabzon",
          "Türkiye", "Almanya", "Fransa", "İngiltere", "Amerika", "Japonya", "Paris", "Londra", "Berlin", "Roma"]
ORG_WORDS = "Üniversitesi|Bakanlığı|Belediyesi|A\\.Ş\\.|Holding|Bankası|Derneği|Vakfı|Kurumu|Enstitüsü"

SUFFIXES = sorted(set([
    "lerinden", "larından", "lardan", "lerden", "ların", "lerin", "larla", "lerle", "ları", "leri", "lar", "ler",
    "dan", "den", "tan", "ten", "nın", "nin", "nun", "nün", "ın", "in", "un", "ün", "da", "de", "ta", "te",
    "ya", "ye", "yı", "yi", "yu", "yü", "sı", "si", "su", "sü", "ım",
    "im", "um", "üm", "iz", "ız", "uz", "üz", "mak", "mek", "yor", "dı", "di", "du", "dü", "tı", "ti", "mış",
    "miş", "muş", "müş", "acak", "ecek", "ması", "mesi", "lı", "li", "lu", "lü", "lık", "lik", "luk", "lük",
    "cı", "ci", "cu", "cü", "sız", "siz", "suz", "süz", "ça", "ce", "la", "le",
]), key=len, reverse=True)


def tr_lower(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()


# ------------------------------------------------------------ Tokenization
def whitespace_tokenize(text: str):
    return text.split()


def regex_tokenize(text: str):
    return re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)


def simple_stem(word: str):
    """Basit sonek kırpma: (kök, [ekler]). Aşırı/yetersiz kırpma yapabilir; amaç klasik yöntemin sınırını göstermek."""
    w = tr_lower(re.sub(r"[^\w]", "", word))
    suffixes = []
    for _ in range(4):
        for s in SUFFIXES:
            min_root = 4 if len(s) == 1 else 3
            if w.endswith(s) and len(w) - len(s) >= min_root:
                suffixes.insert(0, s)
                w = w[: -len(s)]
                break
        else:
            break
    return w, suffixes


# ------------------------------------------------------------ Duygu analizi
def _count_lexicon(tokens, lexicon):
    return sum(1 for t in tokens if any(t.startswith(w) for w in lexicon))


def rule_based_sentiment(text: str) -> dict:
    """Sözlük + zıtlık bağlacı ağırlıklandırması + basit olumsuzluk ('değil') kuralı."""
    lowered = tr_lower(text)
    words = re.findall(r"\w+", lowered)
    split_at = next((i for i, w in enumerate(words) if w in CONTRAST), None)
    found_contrast = [w for w in words if w in CONTRAST]

    def score(tokens, weight):
        pos = _count_lexicon(tokens, POSITIVE)
        neg = _count_lexicon(tokens, NEGATIVE)
        if any(t in NEGATION for t in tokens):
            pos, neg = neg, pos
        return pos * weight, neg * weight

    if split_at is None:
        pos, neg = score(words, 1.0)
    else:
        p1, n1 = score(words[:split_at], 0.7)
        p2, n2 = score(words[split_at + 1:], 1.5)  # bağlaçtan sonrası genelde asıl yargıdır
        pos, neg = p1 + p2, n1 + n2

    if pos == 0 and neg == 0:
        label = "Nötr"
    elif pos > 0 and neg > 0 and min(pos, neg) / max(pos, neg) > 0.5:
        label = "Karma"
    else:
        label = "Pozitif" if pos > neg else "Negatif"
    total = pos + neg
    confidence = 0.5 if total == 0 else round(max(pos, neg) / total, 2)
    return {"label": label, "confidence": confidence, "pos": round(pos, 1), "neg": round(neg, 1),
            "contrast": found_contrast}


# ------------------------------------------------------------ NER
def rule_based_ner(text: str):
    """Düzenli ifade + yer sözlüğü + büyük harf sezgisi. Dönüş: [{'text','label','start','end'}]"""
    found, taken = [], []

    def add(start, end, label):
        if all(end <= a or start >= b for a, b in taken):
            taken.append((start, end))
            found.append({"text": text[start:end], "label": label, "start": start, "end": end})

    date_re = (rf"\b\d{{1,2}}\s+(?:{MONTHS})(?:\s+\d{{4}})?|\b(?:{MONTHS})\s+\d{{4}}|"
               r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b(?:19|20)\d{2}\b")
    for m in re.finditer(date_re, text):
        add(m.start(), m.end(), "Tarih")

    org_re = rf"(?:[A-ZÇĞİÖŞÜ][\wçğıöşü]*\s)+(?:{ORG_WORDS})"
    for m in re.finditer(org_re, text):
        add(m.start(), m.end(), "Kurum")
    for m in re.finditer(r"\b[A-ZÇĞİÖŞÜ]{3,}\b", text):
        add(m.start(), m.end(), "Kurum")

    for place in PLACES:
        for m in re.finditer(rf"(?<!\w){place}", text):
            add(m.start(), m.start() + len(place), "Yer")

    for m in re.finditer(r"[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*", text):
        before = text[: m.start()].rstrip()
        if not before or before[-1] in ".!?":
            continue  # cümle başındaki büyük harf isim olmayabilir
        add(m.start(), m.end(), "Kişi")
    return sorted(found, key=lambda d: d["start"])


# ------------------------------------------------------------ Özetleme
def split_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s.strip()]


def _key(word: str) -> str:
    return tr_lower(word)[:5]


def extractive_summary(text: str, n: int = 2):
    sentences = split_sentences(text)
    freq = Counter(_key(w) for w in re.findall(r"\w+", text) if tr_lower(w) not in STOPWORDS and len(w) > 2)
    scored = []
    for i, s in enumerate(sentences):
        words = [w for w in re.findall(r"\w+", s) if tr_lower(w) not in STOPWORDS and len(w) > 2]
        if words:
            scored.append((sum(freq[_key(w)] for w in words) / (len(words) ** 0.5), i))
    top = sorted(sorted(scored, reverse=True)[:n], key=lambda x: x[1])
    return [sentences[i] for _, i in top]


def keywords(text: str, n: int = 5):
    words = [w for w in re.findall(r"\w+", text) if tr_lower(w) not in STOPWORDS and len(w) > 3]
    freq = Counter(_key(w) for w in words)
    surface = {}
    for w in words:
        surface.setdefault(_key(w), Counter())[tr_lower(w)] += 1
    return [surface[k].most_common(1)[0][0] for k, _ in freq.most_common(n)]
