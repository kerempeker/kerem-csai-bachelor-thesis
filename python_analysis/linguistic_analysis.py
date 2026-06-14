# -*- coding: utf-8 -*-
"""
Linguistic feature analysis: AI vs Human stimulus texts.
Computes per-text features and group-level statistics with effect sizes.
Run: python linguistic_analysis.py
"""
import json, re, statistics
from math import sqrt

INPUT = '/tmp/stimuli_data.json'

with open(INPUT) as f:
    data = json.load(f)

ai_texts = [item['body'].strip().strip('"').strip("'") for item in data['AI_Generated_Stimuli.docx']]
hu_texts = [item['body'].strip().strip('"').strip("'") for item in data['Human_Authored_Stimuli.docx']]

MODALS        = {'will','would','can','could','may','might','shall','should','must'}
HEDGES        = {'perhaps','possibly','arguably','somewhat','relatively','rather','fairly','quite','seemingly','apparently'}
INTENSIFIERS  = {'strongly','deeply','gravely','seriously','firmly','unwaveringly','unequivocally','fully','wholly','entirely','utterly','vigorously'}
NOM_SUFFIXES  = ('tion','ment','ness','ity','ence','ance','ism','ship')

def linguistic_features(text):
    text = text.replace('—','-').replace('–','-')
    sents = [s.strip() for s in re.split(r'[.!?]+\s+', text.strip().rstrip('.!?')) if s.strip()]
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words: return None
    types = set(words)
    sent_lens = [len(re.findall(r"[A-Za-z']+", s)) for s in sents]
    nom_count = sum(1 for w in words if any(w.endswith(suf) for suf in NOM_SUFFIXES) and len(w) > 6)

    f = {
        'words': len(words),
        'sents': len(sents),
        'mean_sent_len': statistics.mean(sent_lens) if sent_lens else 0,
        'sent_len_sd':   statistics.stdev(sent_lens) if len(sent_lens) > 1 else 0,
        'mean_word_len': statistics.mean(len(w) for w in words),
        'TTR':           len(types)/len(words),
        'commas_per_sent': text.count(',') / len(sents) if sents else 0,
        'semicolons':    text.count(';'),
        'modals_per100w':       100*sum(words.count(m) for m in MODALS)/len(words),
        'hedges_per100w':       100*sum(words.count(h) for h in HEDGES)/len(words),
        'intensifiers_per100w': 100*sum(words.count(i) for i in INTENSIFIERS)/len(words),
        'nominalizations_per100w': 100*nom_count/len(words),
        'we_per100w':    100*words.count('we')/len(words),
        'our_per100w':   100*words.count('our')/len(words),
    }
    return f

def cohens_d(g1, g2):
    m1, m2 = statistics.mean(g1), statistics.mean(g2)
    s1 = statistics.stdev(g1) if len(g1) > 1 else 0
    s2 = statistics.stdev(g2) if len(g2) > 1 else 0
    pooled = sqrt((s1**2 + s2**2)/2) if (s1 or s2) else 0
    return (m1 - m2)/pooled if pooled else 0

ai_feats = [linguistic_features(t) for t in ai_texts]
hu_feats = [linguistic_features(t) for t in hu_texts]
keys = list(ai_feats[0].keys())

d_label = 'd'
print(f"\n{'Feature':<25} {'AI mean':>10} {'AI sd':>8} {'HU mean':>10} {'HU sd':>8} {'delta':>9} {d_label:>8}")
print('-'*82)
results = []
for k in keys:
    ai_vals = [f[k] for f in ai_feats]
    hu_vals = [f[k] for f in hu_feats]
    ai_m, hu_m = statistics.mean(ai_vals), statistics.mean(hu_vals)
    ai_s = statistics.stdev(ai_vals); hu_s = statistics.stdev(hu_vals)
    d = cohens_d(ai_vals, hu_vals)
    results.append({'feature': k, 'ai_mean': ai_m, 'ai_sd': ai_s,
                    'hu_mean': hu_m, 'hu_sd': hu_s, 'delta': ai_m-hu_m, 'd': d})
    print(f"{k:<25} {ai_m:>10.3f} {ai_s:>8.3f} {hu_m:>10.3f} {hu_s:>8.3f} {ai_m-hu_m:>+9.3f} {d:>+8.2f}")

print(f"\n=== Significant differentiators (|d| ≥ 0.5) ===")
for r in sorted(results, key=lambda x: -abs(x['d'])):
    if abs(r['d']) >= 0.5:
        direction = 'AI > Human' if r['d'] > 0 else 'Human > AI'
        magnitude = 'large' if abs(r['d']) >= 0.8 else 'medium'
        print(f"  {r['feature']:<25} d = {r['d']:+.2f}  ({direction}, {magnitude} effect)")

# Save results as JSON for downstream use
with open('/Users/kerempeker/Desktop/Thesis/linguistic_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to linguistic_results.json")
