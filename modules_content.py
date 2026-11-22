"""Modüllerin teorik anlatımları, Piku ipuçları ve tek tıkla doldurulan örnek metinler."""

LEVEL_TITLES = ["Çaylak Civciv 🐣", "Meraklı Yavru 🐥", "Kelime Avcısı 🏹", "Dil Ustası 🎓", "NLP Büyücüsü 🧙", "Bilge Baykuş 🦉"]

WARMUP_QUESTIONS = [
    {
        "q": "Bir yapay zeka olsaydın ilk hangi cümleyi analiz ederdin?",
        "options": ["🎬 Bir film yorumu", "📰 Bir haber başlığı", "💬 Arkadaşımın mesajı", "🎶 Bir şarkı sözü"],
        "reactions": [
            "Film yorumları duygu analizi için bir hazine!",
            "Haber başlıkları varlık isimleriyle dolu, tam bir isim avcısı rotası!",
            "Mesajlardaki ince ironiyi çözmek ayrı bir sanat!",
            "Sözlerdeki duygu katmanları çok eğlenceli!",
        ],
    },
    {
        "q": "NLP dünyasına ne kadar aşinasın?",
        "options": ["🐣 Yeni başlıyorum", "🐥 Biraz biliyorum", "🦅 Epey tecrübeliyim"],
        "reactions": [
            "Sorun yok, kanatlarının altına alıyorum seni!",
            "Süper, temelin varmış. Üstüne eğlenceyi ben eklerim!",
            "Vay canına, o zaman klasik yöntemle LLM'i kıyaslamak hoşuna gidecek!",
        ],
    },
    {
        "q": "Hangi süper güç seni daha çok heyecanlandırıyor?",
        "options": ["🔍 Duyguyu okumak", "🏷️ İsimleri avlamak", "✂️ Metni özetlemek", "🧩 Kelimeleri parçalamak"],
        "reactions": [
            "Bağlam dedektifliği tam sana göre!",
            "İsim avcısı modülünde renkli rozetler seni bekliyor!",
            "Özetleme modülünde iki farklı yöntemi göreceksin!",
            "Kelime ameliyatı modülünde türkçenin ekleri bile saklanamaz!",
        ],
    },
]

MODULES = [
    {
        "id": "tok", "icon": "🔬", "title": "Kelime Ameliyatı", "subtitle": "Tokenization & Morfoloji",
        "c1": "#10B981", "c2": "#06B6D4",
        "theory": """
**Tokenization**, metni modelin işleyebileceği küçük parçalara (token) bölme işlemidir.
Boşluğa göre bölmek İngilizce için bir noktaya kadar işe yarar; ama Türkçe gibi **sondan eklemeli** dillerde
tek bir kelime koca bir cümle kadar anlam taşıyabilir: *ev → evler → evlerimizden → evlerimizdendi*.

**Morfoloji** ise kelimenin iç yapısını inceler: **kök** + **yapım ekleri** + **çekim ekleri**.
Sözcük türü (POS) etiketleme de kelimenin cümledeki görevini (isim, fiil, sıfat...) belirler.

- Boşluk ayırma: hızlı ama noktalama yapışık kalır, ekleri göremez.
- Regex tokenizer: noktalamayı ayırır, ama yine kök/ek bilmez.
- Kural tabanlı stemmer: ek listesiyle kırpar, hata yapabilir.
- LLM: bağlama bakarak kök, ek ve türü birlikte çözer.
""",
        "owl_tips": [
            "İpucu: Türkçede ekler kökün sağına dizilir. Kelime bir tren, ekler vagon! 🚂",
            "Hu hu! Noktalama işaretleri de birer token olabilir, onları unutma!",
            "Klasik yöntem 'geldiler!' kelimesini noktalamasıyla yapıştırık bırakır, LLM ise ayırır.",
        ],
        "examples": [
            "Öğrencilerimizle birlikte kütüphanelerden kitapları okuyacaktık.",
            "Gelemeyeceklerini sandığımız arkadaşlarım sonunda geldiler!",
            "Evlerimizdeki çocukların oyuncaklarını topladık, çok yoruldum.",
        ],
    },
    {
        "id": "sent", "icon": "🕵️", "title": "Bağlam Dedektifi", "subtitle": "Duygu Analizi",
        "c1": "#8B5CF6", "c2": "#EC4899",
        "theory": """
**Duygu analizi**, bir metnin olumlu, olumsuz, nötr ya da karma bir duygu taşıdığını belirler.

Klasik yaklaşım bir **sözlük** kullanır: olumlu kelimeleri say, olumsuzları say, karşılaştır.
Ama dil bu kadar basit değildir:

- **Zıtlık bağlaçları** (*ama, fakat, ancak*): vurgu genellikle bağlaçtan **sonraki** kısımdadır.
- **Olumsuzluk**: *"güzel değil"* olumlu kelime içerir ama olumsuz anlam taşır.
- **İroni**: *"Harika, yine geç kaldı."* kelime olarak olumlu, anlam olarak olumsuzdur.

LLM'ler bağlamı bütün olarak okuyabildiği için bu tuzakları çok daha iyi çözer.
""",
        "owl_tips": [
            "Dedektif notu: 'ama' kelimesini gördüğünde sağ tarafa kulak kabart! 🔎",
            "Karma duygu: aynı cümlede hem alkış hem şikayet olabilir!",
            "Kural tabanlı yöntemle LLM'in sonucunu karşılaştır, farkı bulmak oyunun yarısı!",
        ],
        "examples": [
            "Film görsel olarak harikaydı ama senaryo beni çok sıktı.",
            "Bu telefon fiyatına göre mükemmel, kesinlikle tavsiye ederim!",
            "Kargo çok geç geldi, üstelik ürün de bozuktu.",
        ],
    },
    {
        "id": "ner", "icon": "🏷️", "title": "İsim Avcısı", "subtitle": "Varlık İsmi Tanıma (NER)",
        "c1": "#F59E0B", "c2": "#EF4444",
        "theory": """
**NER (Named Entity Recognition)**, metindeki özel varlıkları bulup türünü etiketler:

- 👤 **Kişi** (Ayşe Demir)
- 📍 **Yer** (Ankara)
- 🏢 **Kurum** (TÜBİTAK, Ankara Üniversitesi)
- 📅 **Tarih** (15 Mart 2024)

Kural tabanlı sistemler **büyük harf**, **düzenli ifade** ve **sözlük** (gazetteer) kullanır.
Sorunları: cümle başındaki büyük harf, bilinmeyen isimler, *"Can"* gibi hem isim hem sıradan kelime olanlar.
LLM'ler ise bağlamdan varlığın türünü çıkarır.
""",
        "owl_tips": [
            "Türkçede ekler özel isimlere kesme işaretiyle gelir: Ankara'da, Ayşe'nin. Köke odaklan! 🎯",
            "Büyük harf her zaman isim demek değildir, cümle başını unutma!",
            "Rozetler orijinal cümleyi bozmaz, sadece renkli işaretler ekler. ✨",
        ],
        "examples": [
            "Ayşe Demir, 15 Mart 2024 tarihinde Ankara Üniversitesi'nde düzenlenen TÜBİTAK çalıştayına katıldı.",
            "Mustafa Kemal Atatürk 19 Mayıs 1919'da Samsun'a çıktı.",
            "Google'ın CEO'su Sundar Pichai, Kasım 2023'te İstanbul'u ziyaret etti.",
        ],
    },
    {
        "id": "sum", "icon": "✂️", "title": "Özet Atölyesi", "subtitle": "Metin Özetleme & Anahtar Kavramlar",
        "c1": "#06B6D4", "c2": "#8B5CF6",
        "theory": """
İki temel özetleme yaklaşımı vardır:

- **Çıkarımsal (Extractive):** Metindeki en önemli cümleleri **olduğu gibi** seçer. Güvenilirdir ama akıcılığı sınırlıdır.
- **Soyutlayıcı (Abstractive):** Metni anlayıp **yeni cümlelerle** yeniden yazar. İnsan özetine yakındır; LLM'lerin güçlü olduğu alandır.

**Anahtar kavram çıkarımı** klasik yöntemde kelime sıklığına (TF) dayanır; LLM ise konunun asıl kavramlarını anlamdan seçer.
""",
        "owl_tips": [
            "Çıkarımsal özet = fosforlu kalemle işaretlemek, soyutlayıcı = kendi cümlelerinle anlatmak! 🖍️",
            "Anahtar kelimeler metnin röntgeni gibidir. 🩻",
            "Klasik yöntem sık geçen kelimelere bakar, LLM anlama bakar. Farka dikkat!",
        ],
        "examples": [
            "Doğal dil işleme, bilgisayarların insan dilini anlamasını ve üretmesini sağlayan yapay zeka alanıdır. İlk sistemler elle yazılmış kurallara dayanıyordu. Daha sonra istatistiksel yöntemler büyük metin koleksiyonlarından örüntüleri öğrenmeye başladı. Günümüzde ise büyük dil modelleri milyarlarca parametreyle metinleri anlayabiliyor ve yeni metinler üretebiliyor. Bu modeller çeviri, özetleme ve soru yanıtlama gibi birçok görevi tek bir yapıda çözebiliyor. Ancak yanlış bilgi üretme ve önyargı gibi sorunlar hâlâ aktif araştırma konusudur.",
            "Baykuşlar gece avlanan yırtıcı kuşlardır. Geniş gözleri az ışıkta bile keskin görmelerini sağlar. Kafalarını yaklaşık iki yüz yetmiş derece çevirebilirler. Tüyleri sayesinde neredeyse hiç ses çıkarmadan uçarlar. Bu özellikler baykuşları kemirgenlerin doğal düşmanı yapar. Birçok kültürde baykuş bilgeliğin simgesi sayılır.",
            "Mersin, Akdeniz kıyısında yer alan önemli bir liman kentidir. Limanı Türkiye'nin dış ticaretinde büyük rol oynar. Şehir aynı zamanda narenciye üretimiyle tanınır. Yazları sıcak ve nemli geçen iklimi turizmi destekler. Tarihi Tarsus ve Silifke ilçeleri kültür turizmine katkı sağlar. Son yıllarda enerji yatırımlarıyla da öne çıkmaktadır.",
        ],
    },
]

QUIZ_TOPICS = {
    "🔬 Tokenization & Morfoloji": "Tokenization, morfoloji, kök-ek ayrımı ve sözcük türleri (özellikle Türkçe)",
    "🕵️ Duygu Analizi": "Duygu analizi, zıtlık bağlaçları, olumsuzluk ve ironi",
    "🏷️ Varlık İsmi Tanıma (NER)": "Varlık ismi tanıma (NER): kişi, yer, kurum, tarih",
    "✂️ Özetleme & Anahtar Kavramlar": "Çıkarımsal ve soyutlayıcı özetleme, anahtar kelime çıkarımı",
    "🎲 Karışık NLP": "Doğal dil işlemenin genel kavramları: tokenization, embedding, dil modelleri, duygu analizi, NER, özetleme",
}
