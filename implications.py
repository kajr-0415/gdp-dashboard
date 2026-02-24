"""
Clinical implications, class names, and codes for PAN-MED.
Matches the exact 13-class dataset used during training.
"""

# ─── Class Definitions ─────────────────────────────────────────────────────
# Order MUST match your model's output indices (0–12)
# Update the order below to match your model's label encoding exactly.

CLASS_NAMES = [
    "Actinic Keratosis & Intraepithelial Carcinoma",  # 0 - akiec
    "Basal Cell Carcinoma",                            # 1 - bcc
    "Benign Keratosis-like Lesions",                   # 2 - bkl
    "Dermatofibroma",                                  # 3 - df
    "Melanoma",                                        # 4 - mel
    "Melanocytic Nevi",                                # 5 - nv
    "Vascular Lesions",                                # 6 - vasc
    "Psoriasis / Lichen Planus",                       # 7 - psoriasis
    "Eczema",                                          # 8 - eczema
    "Tinea / Ringworm / Candidiasis",                  # 9 - fungal
    "Atopic Dermatitis",                               # 10 - dermatitis
    "Warts / Molluscum / Viral Infections",            # 11 - warts
    "Seborrheic Keratoses & Benign Tumors",            # 12 - seborrheic
]

CLASS_CODES = [
    "akiec",       # 0
    "bcc",         # 1
    "bkl",         # 2
    "df",          # 3
    "mel",         # 4
    "nv",          # 5
    "vasc",        # 6
    "psoriasis",   # 7
    "eczema",      # 8
    "fungal",      # 9
    "dermatitis",  # 10
    "warts",       # 11
    "seborrheic",  # 12
]

# ─── Risk tier color mapping ────────────────────────────────────────────────
RISK_TIER = {
    "akiec":      "orange",   # pre-malignant
    "bcc":        "red",      # malignant
    "bkl":        "green",    # benign
    "df":         "green",    # benign
    "mel":        "red",      # malignant
    "nv":         "green",    # benign
    "vasc":       "yellow",   # monitor
    "psoriasis":  "yellow",   # chronic
    "eczema":     "yellow",   # chronic
    "fungal":     "yellow",   # treatable
    "dermatitis": "yellow",   # chronic
    "warts":      "yellow",   # viral / treatable
    "seborrheic": "green",    # benign
}

# ─── Clinical Implications ─────────────────────────────────────────────────
IMPLICATIONS = {

    "akiec": {
        "category": "🟠 Pre-Malignant — Requires Prompt Treatment",
        "description": (
            "Actinic Keratosis (AK) and Intraepithelial Carcinoma (IEC / Bowen's Disease) are caused "
            "by cumulative UV radiation damage. AK is a pre-cancerous lesion that can progress to "
            "Squamous Cell Carcinoma if left untreated. IEC (Bowen's Disease) represents carcinoma "
            "in situ — full-thickness keratinocyte dysplasia confined to the epidermis. "
            "Dermatological evaluation and treatment are strongly recommended without delay."
        ),
        "actions": [
            "Dermatology evaluation",
            "Biopsy if IEC suspected",
            "Cryotherapy / 5-FU cream",
            "Photodynamic therapy",
            "Strict UV protection",
            "6-month follow-up",
        ],
    },

    "bcc": {
        "category": "🔴 Malignant — Locally Invasive",
        "description": (
            "Basal Cell Carcinoma (BCC) is the most common form of skin cancer, arising from basal "
            "cells in the epidermis. While it rarely metastasizes, it can cause significant local "
            "tissue destruction and disfigurement if untreated. It commonly presents as a pearly, "
            "translucent bump or flat scar-like lesion on sun-exposed areas. "
            "Surgical treatment is highly effective when caught early — seek prompt care."
        ),
        "actions": [
            "Urgent dermatologist referral",
            "Surgical excision",
            "Mohs surgery evaluation",
            "Sun protection protocol",
            "Regular skin surveillance",
        ],
    },

    "bkl": {
        "category": "🟢 Benign — Low Risk",
        "description": (
            "Benign Keratosis-like Lesions (BKL) include seborrheic keratoses, solar lentigines, "
            "and lichen-planus like keratoses. These are non-cancerous growths that commonly appear "
            "with age and sun exposure. They are generally harmless and require no treatment unless "
            "they become symptomatic, irritated, or are difficult to distinguish from malignant lesions. "
            "A confirmatory dermoscopic exam is advisable."
        ),
        "actions": [
            "Dermoscopy confirmation",
            "Monitor for any changes",
            "Cosmetic removal optional",
            "Annual skin check-up",
        ],
    },

    "df": {
        "category": "🟢 Benign — Fibrous Nodule",
        "description": (
            "Dermatofibroma (DF) is a common, benign fibrous skin nodule most often found on the "
            "lower extremities. It typically presents as a firm, slightly raised, hyperpigmented papule "
            "that dimples inward when pinched (Fitzpatrick sign). It is harmless and rarely requires "
            "treatment. Surgical excision may be considered if symptomatic or cosmetically undesirable."
        ),
        "actions": [
            "No urgent action required",
            "Monitor for size changes",
            "Excision if symptomatic",
            "Confirm with dermoscopy",
        ],
    },

    "mel": {
        "category": "🔴 High Risk — Malignant",
        "description": (
            "Melanoma is the most dangerous form of skin cancer, originating from melanocytes. "
            "It has high metastatic potential and can spread rapidly to lymph nodes and internal organs. "
            "Early-stage melanoma is highly curable, but prognosis worsens significantly with delayed "
            "detection. Warning signs include asymmetry, irregular borders, multiple colors, diameter "
            "over 6mm, and evolving appearance (ABCDE rule). "
            "Immediate specialist referral is critical — do not delay."
        ),
        "actions": [
            "URGENT dermatologist referral",
            "Excisional biopsy",
            "Sentinel lymph node eval",
            "Full-body skin examination",
            "Avoid all UV exposure",
            "Oncology consult if confirmed",
        ],
    },

    "nv": {
        "category": "🟢 Benign — Common Mole",
        "description": (
            "Melanocytic Nevi (NV) are common benign moles formed from clusters of melanocytes. "
            "The vast majority are completely harmless. However, atypical or dysplastic nevi with "
            "irregular features carry a slightly elevated risk of transformation into melanoma. "
            "Apply the ABCDE rule (Asymmetry, Border, Color, Diameter, Evolution) for self-monitoring. "
            "Annual dermatological check-ups are recommended, especially for individuals with many moles."
        ),
        "actions": [
            "Annual skin surveillance",
            "ABCDE self-monitoring",
            "UV protection daily",
            "Photo-document changes",
            "Biopsy if atypical features",
        ],
    },

    "vasc": {
        "category": "🟡 Benign Vascular — Monitor",
        "description": (
            "Vascular Lesions (VASC) encompass a broad group including angiomas, angiokeratomas, "
            "pyogenic granulomas, and hemorrhagic lesions. Most are benign and result from "
            "abnormal blood vessel proliferation. Pyogenic granulomas may bleed easily and recur "
            "after removal. Any rapidly growing or bleeding vascular lesion should be evaluated "
            "promptly to rule out malignant vascular tumors such as Kaposi sarcoma or angiosarcoma."
        ),
        "actions": [
            "Dermatology evaluation",
            "Dermoscopy assessment",
            "Biopsy if rapidly growing",
            "Monitor for bleeding",
            "Laser or surgical removal if needed",
        ],
    },

    "psoriasis": {
        "category": "🟡 Chronic Inflammatory — Manage Long-Term",
        "description": (
            "Psoriasis is a chronic autoimmune skin condition characterized by rapidly proliferating "
            "keratinocytes, resulting in thick, silvery-scaled plaques on erythematous skin. "
            "Lichen Planus, often grouped with psoriasis, presents as itchy, flat-topped purple papules. "
            "Both are non-contagious chronic conditions requiring long-term management. "
            "Treatment includes topical corticosteroids, phototherapy, and systemic biologics for severe cases."
        ),
        "actions": [
            "Dermatology / rheumatology consult",
            "Topical corticosteroids",
            "Phototherapy evaluation",
            "Biologics for severe cases",
            "Identify & avoid triggers",
            "Moisturize regularly",
        ],
    },

    "eczema": {
        "category": "🟡 Chronic Inflammatory — Manage & Monitor",
        "description": (
            "Eczema (Atopic Dermatitis in its most common form) is a chronic, relapsing inflammatory "
            "skin disorder causing intense itching, redness, and skin barrier dysfunction. "
            "It is closely linked to allergic conditions such as asthma and hay fever. "
            "Management focuses on skin hydration, avoidance of triggers, and anti-inflammatory therapy. "
            "Secondary bacterial infections (Staphylococcus aureus) are a common complication."
        ),
        "actions": [
            "Allergist / dermatologist referral",
            "Emollient therapy daily",
            "Topical corticosteroids",
            "Avoid known triggers",
            "Antihistamines for itch",
            "Monitor for infection signs",
        ],
    },

    "fungal": {
        "category": "🟡 Fungal Infection — Treatable",
        "description": (
            "This category includes Tinea infections (ringworm, athlete's foot, jock itch), "
            "Candidiasis (yeast infection), and other dermatophyte or fungal conditions. "
            "These are contagious infections caused by fungi that thrive in warm, moist environments. "
            "They are highly treatable with antifungal medications. Hygiene and dryness are "
            "essential for prevention and recurrence control."
        ),
        "actions": [
            "Topical antifungal therapy",
            "Oral antifungals if severe",
            "Keep affected area dry",
            "Avoid sharing personal items",
            "Complete full treatment course",
            "Follow-up if no improvement in 2 weeks",
        ],
    },

    "dermatitis": {
        "category": "🟡 Inflammatory — Chronic Management",
        "description": (
            "Atopic Dermatitis is a chronic inflammatory skin disease associated with immune "
            "dysregulation and skin barrier defects. It manifests as pruritic, eczematous lesions "
            "typically affecting flexural areas in children and adults. It is part of the atopic "
            "triad (with asthma and allergic rhinitis). Long-term management is essential to "
            "prevent flares and secondary infections. Newer biologic therapies (dupilumab) are "
            "available for moderate-to-severe cases."
        ),
        "actions": [
            "Dermatology referral",
            "Daily emollient use",
            "Topical calcineurin inhibitors",
            "Biologic therapy evaluation",
            "Avoid allergens & irritants",
            "Monitor for superinfection",
        ],
    },

    "warts": {
        "category": "🟡 Viral Infection — Treatable",
        "description": (
            "Warts are caused by Human Papillomavirus (HPV) and are highly contagious through "
            "direct contact. Molluscum Contagiosum is a related viral skin infection common in "
            "children. Most warts resolve spontaneously but can persist for years and spread. "
            "Treatment options include cryotherapy, salicylic acid, laser therapy, and "
            "immunotherapy. HPV vaccination can prevent certain high-risk strains."
        ),
        "actions": [
            "Dermatology evaluation",
            "Cryotherapy",
            "Salicylic acid treatment",
            "Avoid direct contact / sharing",
            "HPV vaccination if applicable",
            "Monitor for spread",
        ],
    },

    "seborrheic": {
        "category": "🟢 Benign — No Immediate Risk",
        "description": (
            "Seborrheic Keratoses are extremely common, benign skin growths that appear as waxy, "
            "warty, 'stuck-on' lesions. They are not contagious or pre-cancerous. This category "
            "also includes other benign tumors such as epidermal cysts and lipomas. "
            "No treatment is medically necessary, though removal is possible for cosmetic or "
            "symptomatic reasons. Distinguish from malignant lesions when uncertain."
        ),
        "actions": [
            "No urgent action needed",
            "Dermoscopy if uncertain",
            "Cosmetic removal available",
            "Cryotherapy / curettage options",
            "Annual skin check-up",
        ],
    },

    # ─── Fallback ───────────────────────────────────────────────────────────
    "DEFAULT": {
        "category": "⚪ Unclassified — Seek Evaluation",
        "description": (
            "The model was unable to confidently classify this lesion. This may be due to image "
            "quality, lighting, or an uncommon presentation. A professional dermatological "
            "examination is recommended for accurate diagnosis."
        ),
        "actions": [
            "Dermatologist consultation",
            "Retake image (better lighting)",
            "Clinical dermoscopy exam",
        ],
    },
}