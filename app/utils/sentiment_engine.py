"""
app/utils/sentiment_engine.py  —  SentimentPro ABSA Engine v3
─────────────────────────────────────────────────────────────
Fixes in this version:
  • Neutral markers (ok/okay/fine/average/alright/decent) detected by lexicon
    → short clauses with only neutral markers → forced neutral
  • Bare aspect-keyword clauses (no opinion word) → skipped / neutral
  • ML low-confidence (<38%) → default neutral instead of weak negative
  • 'light' aspect fully covered
  • sanitize_aspects() for all JSON / DB calls
  • Storage contract: multi-aspect → store per aspect, no false overall
"""
import re, os, csv, pickle
import numpy as np

# ══════════════════════════════════════════════════════════════
#  NEUTRAL MARKERS  (separate from pos/neg)
# ══════════════════════════════════════════════════════════════
NEU_WORDS = {
    'ok','okay','alright','fine','average','decent','moderate','mediocre',
    'acceptable','adequate','ordinary','standard','normal','regular','typical',
    'passable','tolerable','sufficient','fair','middle','so-so','neutral',
    'medium','midrange','basic','plain','simple','not bad','not good',
}

# ══════════════════════════════════════════════════════════════
#  POSITIVE LEXICON  (340+ words)
# ══════════════════════════════════════════════════════════════
POS_WORDS = {
    # Core
    'good','great','excellent','amazing','fantastic','wonderful','superb','outstanding',
    'brilliant','perfect','beautiful','crisp','vibrant','smooth','fast','quick',
    'responsive','reliable','durable','comfortable','stylish','premium','clear',
    'powerful','efficient','impressive','solid','sturdy','bright','sharp','accurate',
    'effective','awesome','incredible','exceptional','nice','strong','rich','vivid',
    'sleek','terrific','splendid','phenomenal','remarkable','cool','useful','handy',
    'convenient','easy','simple','elegant','refined','polished','flawless','worthy',
    'clean','fresh','spotless','long','full','ample','generous','plentiful',
    # Verbs / states
    'love','loved','like','liked','enjoy','enjoyed','adore','satisfied','happy',
    'pleased','glad','impressed','delighted','thrilled','excited','works','lasts',
    'recommend','recommended',
    # Service / hospitality
    'helpful','friendly','polite','attentive','kind','caring','professional','prompt',
    'warm','welcoming','courteous','gracious','hospitable','swift','timely',
    # Food specific
    'tasty','delicious','yummy','flavorful','savory','nutritious','appetizing',
    'juicy','tender','succulent','aromatic','moist','fresh','crispy',
    # Display / camera / light / sound
    'radiant','stunning','gorgeous','luminous','dazzling','glowing','shining',
    'booming','resonant','melodious','crystal','immersive','lossless',
    'blazing','snappy','zippy','seamless','fluid','buttery','lasting','enduring',
    'sustained','prolonged','extended','capacious','lightweight','thin',
    'colorful','saturated','lifelike','natural','realistic','vivid','illuminated',
    # Price
    'affordable','valuable','reasonable','competitive','worth','cost-effective',
    # Build / design
    'robust','tough','resilient','flexible','modern','innovative','trendy',
    'sophisticated','luxurious','immaculate','spacious','roomy','organized',
    'cozy','inviting','lively','harmonious','balanced','stable','consistent',
    'secure','safe',
    # Opinion
    'enjoyable','pleasant','pleasing','gratifying','satisfying','rewarding',
    'finest','superior','prime','elite',
}

# ══════════════════════════════════════════════════════════════
#  NEGATIVE LEXICON  (340+ words)
# ══════════════════════════════════════════════════════════════
NEG_WORDS = {
    # Core
    'bad','terrible','horrible','awful','dreadful','worst','poor','useless',
    'broken','defective','disappointing','disappointed','slow','laggy','blurry',
    'dim','weak','unreliable','uncomfortable','cheap','flimsy','ugly',
    'inefficient','frustrating','unhappy','dissatisfied','disgusting','dirty',
    'rude','unfriendly','impolite','expensive','overpriced','rubbish','garbage',
    'hate','hated','dislike','mediocre','limited','inadequate','insufficient',
    'heavy','bulky','stale','bland','noisy','confusing','complicated','difficult',
    'pathetic','flawed','fail','failed','wrong','unresponsive','grainy',
    'fuzzy','choppy','sluggish','hopeless','lousy','shoddy','inferior',
    'substandard','faulty','crashing','unstable','inconsistent','malfunctioning',
    'pointless','waste','scam','fragile','brittle',
    # Display / camera / light / sound
    'dull','dark','faded','washed','muddy','cloudy','scratchy','flickering',
    'muffled','distorted','crackling','buzzing','static','tinny','hollow',
    'pixelated','smudged','smeared','hazy','glare',
    # Build / design
    'clunky','cumbersome','unwieldy','awkward','outdated','obsolete',
    'peeling','cracking','wobbling','rattling','screeching','grinding',
    'torn','worn','damaged','scratched','chipped','cracked',
    # Battery / performance
    'overheating','swollen','leaking','dead','short','tiny','narrow','drain',
    # Service / place
    'cold','tasteless','undercooked','overcooked','oily','soggy','watery',
    'diluted','runny','congealed','rancid','smelly','musty','moldy','grimy',
    'filthy','unkempt','cluttered','cramped','depressing','chaotic',
    # General
    'low','lacking','missing','absent','deceptive','misleading','overrated',
    'unimpressive','toxic','harmful','dangerous','unsafe','hazardous',
    'incomplete','unreliable','buggy','glitchy','broken','error',
}

NEGATORS = {
    'not','no','never','hardly','barely','scarcely','neither','nor',
    'cannot','cant',"can't",'dont',"don't",'doesnt',"doesn't",
    'didnt',"didn't",'isnt',"isn't",'wasnt',"wasn't",'wont',"won't",
    'without','lack','lacks','lacking',
}

STOPS = {
    'a','an','the','and','or','in','on','at','to','for','of','with','by','from',
    'is','was','are','were','be','been','have','has','had','do','does','did',
    'will','would','could','should','may','might','must','can','so','this','that',
    'i','me','my','we','you','he','she','it','they','them','its','as','if','then',
    'than','when','where','while','each','both','into','through','during','before',
    'after','above','below','between','again','once','here','there','just','about',
    'since','until','very','really','quite','rather','get','got','also','up','out',
    'all','am','us','our','your','their','these','those','such','even',
}

# ══════════════════════════════════════════════════════════════
#  ASPECT PATTERNS  (23 categories)
# ══════════════════════════════════════════════════════════════
ASPECT_PATTERNS = [
    ('battery life',    r'\bbattery\s+(?:life|drain|backup|lasts?)\b'),
    ('battery',         r'\bbattery\b|\bcharging\b|\bcharger\b'),
    ('camera',          r'\bcamera\b|\bphoto\b|\bpicture\b|\bselfie\b|\blens\b|\bzoom\b|\bphotography\b|\bpics?\b|\bimage\b'),
    ('display',         r'\bdisplay\b|\bscreen\b|\bresolution\b|\bbrightness\b|\bpanel\b'),
    ('lighting',        r'\blighting\b|\blight\b|\billumination\b|\bbacklight\b|\blights\b'),
    ('performance',     r'\bperformance\b|\bprocessor\b|\bcpu\b|\bgpu\b|\blag\b|\bhanging\b|\bfreezes?\b|\bbenchmark\b|\bram\b|\bspeed\b'),
    ('storage',         r'\bstorage\b|\binternal\s+memory\b|\bstorage\s+space\b|\bdisk\b|\bmemory\b'),
    ('sound',           r'\bsound\b|\baudio\b|\bspeaker\b|\bvolume\b|\bbass\b|\bmicrophone\b|\bearphone\b|\bheadphone\b|\bmic\b'),
    ('design',          r'\bdesign\b|\bbuild\s+quality\b|\bbuild\b|\bappearance\b|\bfinish\b|\baesthetics?\b|\blooks?\b|\bbody\b'),
    ('connectivity',    r'\bwifi\b|\bwi-fi\b|\bbluetooth\b|\bnetwork\b|\bsignal\b|\binternet\b|\b5g\b|\b4g\b|\bhotspot\b'),
    ('quality',         r'\bquality\b|\bdurability\b|\bsturdiness\b|\bconstruction\b|\bcraftsmanship\b|\bmaterial\b'),
    ('price',           r'\bprice\b|\bcost\b|\bvalue\b|\bworth\b|\bexpensive\b|\baffordable\b|\bbudget\b|\boverpriced\b|\brate\b'),
    ('delivery',        r'\bdelivery\b|\bshipping\b|\bpackaging\b|\bdispatch\b|\bcourier\b|\btracking\b|\barrival\b'),
    ('customer service',r'\bcustomer\s+service\b|\bafter\s+sales\b|\bwarranty\b|\brefund\b|\breturn\s+policy\b|\bsupport\s+team\b'),
    ('service',         r'\bservice\b|\bstaff\b|\bwaiter\b|\bwaitress\b|\breceptionist\b|\bhospitality\b|\bserver\b'),
    ('food',            r'\bfood\b|\btaste\b|\bflavor\b|\bflavour\b|\bmeal\b|\bdish\b|\bcuisine\b|\bmenu\b|\byummy\b|\btasty\b|\bdelicious\b|\brecipe\b'),
    ('ambiance',        r'\bambiance\b|\batmosphere\b|\bdecor\b|\bambience\b|\bvibe\b|\bsetting\b|\binterior\b|\benvironment\b'),
    ('cleanliness',     r'\bclean\b|\bhygiene\b|\bdirty\b|\bneat\b|\btidy\b|\bfilthy\b|\bsanitary\b|\bmessy\b'),
    ('room',            r'\broom\b|\bsuite\b|\bbedroom\b|\baccommodation\b|\bbathroom\b|\btoilet\b|\bbed\b'),
    ('location',        r'\blocation\b|\bnearby\b|\bcentral\b|\baccessible\b|\bproximity\b|\bdistance\b|\barea\b'),
    ('features',        r'\bfeatures?\b|\bfunctionality\b|\bcapability\b|\boptions?\b|\bmode\b|\bfunction\b'),
    ('interface',       r'\binterface\b|\bui\b|\bux\b|\bnavigation\b|\busability\b|\blayout\b|\bapp\b'),
]

# Opinion boundary words used to split aspect clauses
_OPN = (
    'good|bad|great|terrible|excellent|awful|horrible|amazing|poor|fantastic|'
    'worst|best|nice|beautiful|ugly|fast|slow|strong|weak|clear|blurry|loud|quiet|'
    'smooth|laggy|fine|decent|outstanding|superb|dreadful|wonderful|disappointing|'
    'impressive|brilliant|perfect|flawed|reliable|broken|comfortable|stylish|'
    'premium|responsive|crisp|vibrant|dim|fresh|stale|bland|helpful|rude|friendly|'
    'polite|accurate|love|hate|like|dislike|enjoy|satisfied|happy|unhappy|pleased|'
    'disappointed|impressed|frustrated|confusing|heavy|sharp|dull|rich|vivid|'
    'sluggish|snappy|clean|dirty|tasty|delicious|warm|cold|muffled|bright|dark|'
    'grainy|muddy|washed|scratchy|affordable|overpriced|damaged|modern|outdated|'
    'elegant|clunky|spacious|cramped|cozy|lively|reasonable|ok|okay|alright|average'
)
SENT_BOUNDARY_RE = re.compile(r'\b(?:' + _OPN + r')\b', re.IGNORECASE)

CONJ_RE = re.compile(
    r'(?:,?\s*(?:but|however|although|though|yet|while|whereas|nevertheless|'
    r'despite|even\s+though|on\s+the\s+other\s+hand|still)\s+)'
    r'|(?:[;.!?]\s+)',
    re.IGNORECASE
)

# ══════════════════════════════════════════════════════════════
#  MODEL MANAGEMENT
# ══════════════════════════════════════════════════════════════
_model = None
_BASE  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_MODEL_PATH = os.path.join(_BASE, 'trained_models', 'sentiment_model.pkl')
_DATA_PATH  = os.path.join(_BASE, 'dataset', 'reviews.csv')


def _clean(text: str) -> str:
    text = re.sub(r'http\S+', '', text.lower())
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = [w for w in text.split() if w not in STOPS and len(w) > 1]
    return ' '.join(tokens) or text.lower()


def _train():
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    texts, labels = [], []
    try:
        with open(_DATA_PATH, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                t = row.get('review_text', '').strip()
                l = row.get('sentiment', '').strip()
                if t and l in ('positive', 'negative', 'neutral'):
                    texts.append(_clean(t)); labels.append(l)
    except Exception as e:
        print(f'[ENGINE] dataset error: {e}'); return None
    if len(texts) < 10:
        return None
    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=20000, ngram_range=(1, 3),
                                  min_df=1, sublinear_tf=True)),
        ('clf',   LogisticRegression(max_iter=5000, C=2.0, solver='lbfgs',
                                     class_weight='balanced', random_state=42)),
    ])
    pipe.fit(texts, labels)
    os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
    with open(_MODEL_PATH, 'wb') as f:
        pickle.dump(pipe, f)
    print(f'[ENGINE] Trained on {len(texts)} samples.')
    return pipe


def load_model():
    global _model
    if os.path.exists(_MODEL_PATH):
        try:
            with open(_MODEL_PATH, 'rb') as f:
                m = pickle.load(f)
            m.predict_proba(['test'])
            _model = m; return _model
        except Exception:
            pass
    _model = _train(); return _model


# ══════════════════════════════════════════════════════════════
#  PREDICTION  (lexicon + ML hybrid)
# ══════════════════════════════════════════════════════════════
def _has_opinion(text: str) -> bool:
    """Return True if text contains at least one positive, negative, or neutral marker."""
    words = re.sub(r'[^a-z\s]', '', text.lower()).split()
    return any(w in POS_WORDS or w in NEG_WORDS or w in NEU_WORDS for w in words)


def _lexicon(text: str):
    """
    Score text with the lexicon.
    Returns (label|None, confidence).
    Priority: negators flip polarity; neutral markers → neutral.
    """
    words = re.sub(r'[^a-z\s]', '', text.lower()).split()
    p = n = neu = 0; neg = False
    for w in words:
        if w in NEGATORS:
            neg = True; continue
        if w in NEU_WORDS:
            neu += 1
        elif w in POS_WORDS:
            if neg: n += 1
            else:   p += 1
        elif w in NEG_WORDS:
            if neg: p += 1
            else:   n += 1
        neg = False

    if p == 0 and n == 0 and neu > 0:
        return 'neutral', float(min(80, 50 + neu * 12))
    if p > n and p >= 1:
        return 'positive', float(min(88, 52 + p * 15))
    if n > p and n >= 1:
        return 'negative', float(min(88, 52 + n * 15))
    if p == n and (p > 0 or neu > 0):
        return 'neutral', 55.0
    return None, 50.0


def _ml(text: str):
    """ML prediction. Returns (label, confidence, is_mixed, distribution)."""
    global _model
    if _model is None: _model = load_model()
    if _model is None: return None, 50.0, False, {}
    cleaned = _clean(text)
    if not cleaned: return None, 50.0, False, {}
    try:
        proba   = _model.predict_proba([cleaned])[0]
        classes = list(_model.classes_)
        idx     = int(np.argmax(proba))
        sp      = sorted(proba, reverse=True)
        is_mix  = bool((float(sp[0]) - float(sp[1])) < 0.18 and float(sp[0]) < 0.60)
        dist    = {str(classes[i]): round(float(p) * 100, 1) for i, p in enumerate(proba)}
        return str(classes[idx]), round(float(proba[idx]) * 100, 1), is_mix, dist
    except Exception as e:
        print(f'[ML] error: {e}')
        return None, 50.0, False, {}


def _predict(clause: str):
    """
    Hybrid predict for a single clause.
    Rules:
      1. If clause has NO opinion words → return neutral (bare aspect keyword)
      2. ≤6 words: lexicon first (precise for short phrases)
      3. >6 words: ML first, lexicon fallback on low confidence (<40%)
      4. ML confidence <38% → default neutral
    """
    # Rule 1: no opinion word at all → neutral (bare keyword like "quality", "delivery")
    if not _has_opinion(clause):
        return 'neutral', 55.0, False, {'neutral': 55.0}

    words = clause.split()

    # Rule 2: short clause → lexicon first
    if len(words) <= 6:
        lex_lbl, lex_conf = _lexicon(clause)
        if lex_lbl:
            return lex_lbl, lex_conf, False, {lex_lbl: lex_conf}

    # Rule 3: ML
    lbl, conf, is_mix, dist = _ml(clause)
    if lbl and conf >= 40:
        return lbl, conf, is_mix, dist

    # Rule 4: ML low confidence → try lexicon
    lex_lbl, lex_conf = _lexicon(clause)
    if lex_lbl:
        return lex_lbl, lex_conf, False, {lex_lbl: lex_conf}

    # Rule 5: ML low confidence, no lexicon signal → neutral
    return 'neutral', 55.0, False, {'neutral': 55.0}


# ══════════════════════════════════════════════════════════════
#  ASPECT DETECTION
# ══════════════════════════════════════════════════════════════
def _find_aspects(text: str):
    """Return sorted non-overlapping (start, end, name) hits."""
    tl = text.lower()
    hits = []
    for name, pat in ASPECT_PATTERNS:
        for m in re.finditer(pat, tl):
            hits.append((m.start(), m.end(), name))
    hits.sort()
    deduped, last = [], -1
    for s, e, n in hits:
        if s >= last:
            deduped.append((s, e, n)); last = e
    return deduped


# ══════════════════════════════════════════════════════════════
#  CLAUSE SPLITTING
# ══════════════════════════════════════════════════════════════
def _split_clauses(text: str):
    """
    Split text into (aspect_name, clause_text) pairs.
    Handles all patterns:
      • "battery is good but camera is bad"   (conjunction)
      • "battery good. camera bad. light ok." (punctuation)
      • "battery good, camera bad, light ok"  (comma)
      • "battery good camera bad light ok"    (no separator)
    """
    # Stage 1 — split on conjunctions and sentence-ending punctuation
    primary = [c.strip().rstrip('.!?,;')
               for c in CONJ_RE.split(text) if c and c.strip()]

    # Stage 2 — sub-split on commas
    clauses = []
    for part in primary:
        subs = [s.strip() for s in part.split(',') if s.strip() and len(s.strip()) > 2]
        clauses.extend(subs if len(subs) > 1 else [part])

    # Stage 3 — for each clause, detect aspects and boundary-split if multiple
    pairs = []
    for clause in clauses:
        if not clause or len(clause) < 2: continue
        hits = _find_aspects(clause)

        if not hits:
            pairs.append(('overall', clause))

        elif len(hits) == 1:
            pairs.append((hits[0][2], clause))

        else:
            # Multiple aspects in same clause → split at boundary between them
            for i, (start, end, name) in enumerate(hits):
                if i + 1 < len(hits):
                    nxt    = hits[i + 1][0]
                    region = clause[end:nxt]
                    sm     = list(SENT_BOUNDARY_RE.finditer(region))
                    # Cut after last opinion word between the two aspects
                    cut    = end + sm[-1].end() if sm else (end + nxt) // 2
                    seg    = clause[start:cut].strip().strip('.,;- ')
                else:
                    seg = clause[start:].strip().strip('.,;- ')
                if seg and len(seg) > 1:
                    pairs.append((name, seg))

    return pairs or [('overall', text)]


# ══════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════
def analyze(text: str) -> dict:
    """
    Full ABSA analysis.

    Storage contract:
      • Single aspect OR all aspects same sentiment
            → overall_sentiment = that sentiment
            → is_mixed = False
      • Multiple aspects with DIFFERENT sentiments
            → overall_sentiment = 'mixed'
            → is_mixed = True
            → each aspect stored individually with its own sentiment

    Returns:
        overall_sentiment : str
        overall_confidence: float
        is_mixed          : bool
        distribution      : {label: pct}   (aspect-vote based)
        aspects           : list of dicts
        is_multi_aspect   : bool
    """
    pairs   = _split_clauses(text)
    seen    = {}
    aspects = []

    for name, clause in pairs:
        lbl, conf, _, _ = _predict(clause)
        # Deduplicate aspect names
        key = name
        if key in seen:
            seen[key] += 1; key = f'{name} ({seen[key]})'
        else:
            seen[name] = 1
        aspects.append({
            'aspect':     key,
            'sentiment':  str(lbl),
            'confidence': round(float(conf), 1),
            'clause':     str(clause),
        })

    sentiments   = [a['sentiment'] for a in aspects]
    unique_sents = set(sentiments)

    if len(aspects) == 1:
        overall_lbl  = sentiments[0]
        overall_conf = aspects[0]['confidence']
        is_mixed     = False
    elif len(unique_sents) == 1:
        # All aspects agree
        overall_lbl  = sentiments[0]
        overall_conf = round(sum(a['confidence'] for a in aspects) / len(aspects), 1)
        is_mixed     = False
    else:
        # Conflicting sentiments → mixed
        overall_lbl  = 'mixed'
        overall_conf = round(sum(a['confidence'] for a in aspects) / len(aspects), 1)
        is_mixed     = True

    from collections import Counter
    cnt      = Counter(sentiments)
    dist_out = {k: round(v / len(sentiments) * 100, 1) for k, v in cnt.items()}

    return {
        'overall_sentiment':  overall_lbl,
        'overall_confidence': overall_conf,
        'is_mixed':           is_mixed,
        'distribution':       dist_out,
        'aspects':            aspects,
        'is_multi_aspect':    len(aspects) > 1,
    }


def sanitize_aspects(aspects: list) -> list:
    """Convert all values to native Python types — safe for json.dumps() and SQLite."""
    return [
        {
            'aspect':     str(a['aspect']),
            'sentiment':  str(a['sentiment']),
            'confidence': float(a['confidence']),
            'clause':     str(a['clause']),
        }
        for a in aspects
    ]
