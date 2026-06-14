from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def extract_texts(path):
    doc = Document(path)
    texts = {}
    current_num = None
    for para in doc.paragraphs:
        if para.style.name == 'Heading 1':
            m = re.match(r'Text (\d+)', para.text)
            if m:
                current_num = int(m.group(1))
        if para.style.name == 'Quote' and current_num:
            texts[current_num] = para.text.strip().strip('"')
    return texts

human = extract_texts('/Users/kerempeker/Desktop/Thesis/Human_Authored_Stimuli.docx')
ai    = extract_texts('/Users/kerempeker/Desktop/Thesis/AI_Generated_Stimuli.docx')

topics = {
    1:  "Iran JCPOA Negotiations",
    2:  "Russia Invasion of Ukraine",
    3:  "Belarus Migrant Crisis",
    4:  "Afghanistan Withdrawal",
    5:  "COP26 Climate Finance",
    6:  "Myanmar Military Coup",
    7:  "Ethiopia / Tigray Conflict",
    8:  "COVID-19 / COVAX",
    9:  "UK-EU Northern Ireland Protocol",
    10: "Mali / Sahel Security",
    11: "Sudan Coup",
    12: "Israel-Palestine / Gaza",
    13: "NATO Collective Defence",
    14: "UK Energy Security",
    15: "Global Food Security",
    16: "China Trade / WTO",
    17: "Finland/Sweden NATO Bid",
    18: "ICC / International Justice",
    19: "Syria Humanitarian Crisis",
    20: "North Korea ICBM Tests",
}

print("=" * 70)
print(f"{'#':<4} {'Topic':<30} {'Cosine Sim':>10} {'Bigram Overlap':>15}")
print("=" * 70)

similarities = []
all_human = []
all_ai = []

for i in range(1, 21):
    h = human[i]
    a = ai[i]

    # Cosine similarity via TF-IDF
    vec = TfidfVectorizer(ngram_range=(1,1)).fit_transform([h, a])
    cos_sim = cosine_similarity(vec[0], vec[1])[0][0]

    # Bigram overlap
    def bigrams(text):
        words = re.findall(r'\w+', text.lower())
        return set(zip(words, words[1:]))

    h_bi = bigrams(h)
    a_bi = bigrams(a)
    if h_bi | a_bi:
        overlap = len(h_bi & a_bi) / len(h_bi | a_bi)
    else:
        overlap = 0.0

    similarities.append((i, cos_sim, overlap))
    all_human.append(h)
    all_ai.append(a)

    flag = " ⚠️ HIGH" if cos_sim > 0.5 else ""
    print(f"{i:<4} {topics[i]:<30} {cos_sim:>10.3f} {overlap:>14.3f}{flag}")

print("=" * 70)
avg_cos = sum(s[1] for s in similarities) / len(similarities)
avg_big = sum(s[2] for s in similarities) / len(similarities)
max_cos = max(s[1] for s in similarities)
print(f"{'AVERAGE':<35} {avg_cos:>10.3f} {avg_big:>15.3f}")
print(f"{'MAX':<35} {max_cos:>10.3f}")
print()
print("Interpretation:")
print(f"  Mean cosine similarity: {avg_cos:.3f} — {'LOW ✓ (< 0.3 = distinct)' if avg_cos < 0.3 else 'MODERATE — check flagged texts'}")
print(f"  Mean bigram overlap:    {avg_big:.3f} — {'LOW ✓ (< 0.1 = no verbatim copying)' if avg_big < 0.1 else 'CHECK FLAGGED'}")
print()
if max_cos < 0.5:
    print("CONCLUSION: No high-similarity pairs detected.")
    print("AI-generated texts are lexically distinct from human-authored texts.")
    print("Bias from AI training data reproducing source texts is unlikely.")
else:
    high = [s for s in similarities if s[1] > 0.5]
    print(f"WARNING: {len(high)} pair(s) with cosine similarity > 0.5 — review manually.")
