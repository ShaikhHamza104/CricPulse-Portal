"""
Cricket Player Name Harmonizer & Canonical Mapping.
Translates Cricsheet initial-based abbreviations (e.g., 'v kohli', 'jj bumrah', 'cv varun')
into proper, official cricket broadcast names.
"""

# Comprehensive canonical mapping of IPL cricketers across 2008–2024
CANONICAL_PLAYER_NAMES: dict[str, str] = {
    # 2024 Top Run Scorers / Orange Cap Contenders
    "v kohli": "Virat Kohli",
    "rd gaikwad": "Ruturaj Gaikwad",
    "r parag": "Riyan Parag",
    "tm head": "Travis Head",
    "sv samson": "Sanju Samson",
    "b sai sudharsan": "B. Sai Sudharsan",
    "sai sudharsan": "B. Sai Sudharsan",
    "kl rahul": "KL Rahul",
    "n pooran": "Nicholas Pooran",
    "sp narine": "Sunil Narine",
    "abhishek sharma": "Abhishek Sharma",
    "f du plessis": "Faf du Plessis",
    "s dube": "Shivam Dube",
    "ss iyer": "Shreyas Iyer",
    "rr pant": "Rishabh Pant",
    "yb jaiswal": "Yashasvi Jaiswal",
    "y jaiswal": "Yashasvi Jaiswal",
    "sa yadav": "Suryakumar Yadav",
    "rg sharma": "Rohit Sharma",
    "h klaasen": "Heinrich Klaasen",
    "shubman gill": "Shubman Gill",
    "mp stoinis": "Marcus Stoinis",
    "da miller": "David Miller",
    "rinku singh": "Rinku Singh",
    "tilak varma": "Tilak Varma",
    "nt tilak varma": "Tilak Varma",
    "ra tripathi": "Rahul Tripathi",
    "jm bairstow": "Jonny Bairstow",
    "pd salt": "Phil Salt",
    "vr iyer": "Venkatesh Iyer",
    "ra patidar": "Rajat Patidar",
    "ak markram": "Aiden Markram",
    "so hetmyer": "Shimron Hetmyer",
    "dp padikkal": "Devdutt Padikkal",
    "dk": "Dinesh Karthik",
    "d karthik": "Dinesh Karthik",
    "ms dhoni": "MS Dhoni",
    "as rawat": "Anuj Rawat",
    "shahrukh khan": "M. Shahrukh Khan",
    "m shahrukh khan": "M. Shahrukh Khan",
    "ashutosh sharma": "Ashutosh Sharma",
    "shashank singh": "Shashank Singh",

    # 2024 Top Wicket Takers / Purple Cap Contenders
    "hv patel": "Harshal Patel",
    "cv varun": "Varun Chakravarthy",
    "varun chakravarthy": "Varun Chakravarthy",
    "jj bumrah": "Jasprit Bumrah",
    "t natarajan": "T. Natarajan",
    "harshit rana": "Harshit Rana",
    "avesh khan": "Avesh Khan",
    "arshdeep singh": "Arshdeep Singh",
    "ad russell": "Andre Russell",
    "pj cummins": "Pat Cummins",
    "ys chahal": "Yuzvendra Chahal",
    "kuldeep yadav": "Kuldeep Yadav",
    "m siraj": "Mohammed Siraj",
    "mohammed siraj": "Mohammed Siraj",
    "m shami": "Mohammed Shami",
    "mohammed shami": "Mohammed Shami",
    "m theekshana": "Maheesh Theekshana",
    "m pathirana": "Matheesha Pathirana",
    "noor ahmad": "Noor Ahmad",
    "rashid khan": "Rashid Khan",
    "ta boult": "Trent Boult",
    "sandeeep sharma": "Sandeep Sharma",
    "sandeep sharma": "Sandeep Sharma",
    "b kumar": "Bhuvneshwar Kumar",
    "sn thakur": "Shardul Thakur",
    "k rabada": "Kagiso Rabada",
    "kg rabada": "Kagiso Rabada",
    "kh pandya": "Krunal Pandya",
    "hh pandya": "Hardik Pandya",
    "ra jadeja": "Ravindra Jadeja",
    "ar patel": "Axar Patel",
    "r ashwin": "Ravichandran Ashwin",
    "ravi bishnoi": "Ravi Bishnoi",
    "va arora": "Vaibhav Arora",
    "mayank yadav": "Mayank Yadav",
    "khaleel ahmed": "Khaleel Ahmed",
    "kk ahmed": "Khaleel Ahmed",
    "m mohsin khan": "Mohsin Khan",
    "yash dayal": "Yash Dayal",
    "swapnil singh": "Swapnil Singh",
    "lh ferguson": "Lockie Ferguson",
    "g coetzee": "Gerald Coetzee",
    "mustafizur rahman": "Mustafizur Rahman",
    "sm curran": "Sam Curran",
    "c green": "Cameron Green",

    # All-Time Legends & Historic Players
    "ch gayle": "Chris Gayle",
    "ab de villiers": "AB de Villiers",
    "da warner": "David Warner",
    "s dhawan": "Shikhar Dhawan",
    "sk raina": "Suresh Raina",
    "g gambhir": "Gautam Gambhir",
    "sr watson": "Shane Watson",
    "sl malinga": "Lasith Malinga",
    "dj bravo": "Dwayne Bravo",
    "ka pollard": "Kieron Pollard",
    "v sehwag": "Virender Sehwag",
    "sr tendulkar": "Sachin Tendulkar",
    "sc ganguly": "Sourav Ganguly",
    "r dravid": "Rahul Dravid",
    "yuvraj singh": "Yuvraj Singh",
    "harbhajan singh": "Harbhajan Singh",
    "a kumble": "Anil Kumble",
    "z khan": "Zaheer Khan",
    "a nehra": "Ashish Nehra",
    "rp singh": "RP Singh",
    "pp ojha": "Pragyan Ojha",
    "ik pathan": "Irfan Pathan",
    "yk pathan": "Yusuf Pathan",
    "am rahane": "Ajinkya Rahane",
    "mk pandey": "Manish Pandey",
    "pa patel": "Parthiv Patel",
    "wp saha": "Wriddhiman Saha",
    "mandeep singh": "Mandeep Singh",
    "km jadhav": "Kedar Jadhav",
    "s badree": "Samuel Badree",
    "sp smith": "Steve Smith",
    "gj maxwell": "Glenn Maxwell",
    "g maxwell": "Glenn Maxwell",
    "jc buttler": "Jos Buttler",
    "q de kock": "Quinton de Kock",
    "mm ali": "Moeen Ali",
    "ba stokes": "Ben Stokes",
    "jofra archer": "Jofra Archer",
    "dl chahar": "Deepak Chahar",
    "rd chahar": "Rahul Chahar",
    "m sharma": "Mohit Sharma",
    "i sharma": "Ishant Sharma",
    "ut yadav": "Umesh Yadav",
}

# Common fan/cricket broadcast nicknames mapped to canonical display names
CRICKET_NICKNAMES: dict[str, str] = {
    "king kohli": "v kohli",
    "chiku": "v kohli",
    "thala": "ms dhoni",
    "captain cool": "ms dhoni",
    "hitman": "rg sharma",
    "sky": "sa yadav",
    "boom boom": "jj bumrah",
    "boom boom bumrah": "jj bumrah",
    "abd": "ab de villiers",
    "mr 360": "ab de villiers",
    "universe boss": "ch gayle",
    "jaddu": "ra jadeja",
    "sir jadeja": "ra jadeja",
    "bhuvi": "b kumar",
    "lord shardul": "sn thakur",
    "lord": "sn thakur",
    "ash": "r ashwin",
    "gabbar": "s dhawan",
}


def resolve_player_search_terms(query: str | None) -> list[str]:
    """
    Translates a user's natural language or formal player search (e.g. 'Virat Kohli',
    'Rohit Sharma', 'King Kohli', 'Bumrah', 'Dhoni') into candidate search keys compatible
    with the Cricsheet/DuckDB analytical engine.
    """
    if not query:
        return []

    cleaned = str(query).strip().lower()
    if not cleaned:
        return []

    candidates: list[str] = []

    # 1. Nickname direct lookup
    if cleaned in CRICKET_NICKNAMES:
        candidates.append(CRICKET_NICKNAMES[cleaned])

    # 2. Reverse exact lookup from Canonical Display Names
    rev_canonical = {disp.lower(): cricsheet_key for cricsheet_key, disp in CANONICAL_PLAYER_NAMES.items()}
    if cleaned in rev_canonical:
        if rev_canonical[cleaned] not in candidates:
            candidates.append(rev_canonical[cleaned])

    # 3. Match substrings and words in canonical display names
    for cricsheet_key, disp in CANONICAL_PLAYER_NAMES.items():
        disp_lower = disp.lower()
        if cleaned == disp_lower or cleaned in disp_lower:
            if cricsheet_key not in candidates:
                candidates.append(cricsheet_key)

    # 4. Generate Cricsheet-style initials + surname heuristic
    # E.g. 'Virat Kohli' -> 'v kohli'
    # E.g. 'Mahendra Singh Dhoni' -> 'ms dhoni'
    words = [w for w in cleaned.split() if w]
    if len(words) >= 2:
        cand_initial = f"{words[0][0]} {words[-1]}"
        if cand_initial not in candidates:
            candidates.append(cand_initial)

        initials_prefix = "".join(w[0] for w in words[:-1])
        cand_all_initials = f"{initials_prefix} {words[-1]}"
        if cand_all_initials not in candidates:
            candidates.append(cand_all_initials)

        # Surname alone (e.g. 'Kohli', 'Bumrah', 'Sharma')
        surname = words[-1]
        if surname not in candidates:
            candidates.append(surname)

    # 5. Fallback to raw cleaned query
    if cleaned not in candidates:
        candidates.append(cleaned)

    return candidates


def humanize_player_name(raw_name: str | None) -> str:
    """
    Transforms any Cricsheet player name into a clean, human-readable name.
    1. Checks the canonical mapping for exact matches.
    2. If not found, formats initials properly (e.g. 'j j bumrah' -> 'J.J. Bumrah').
    """
    if not raw_name:
        return "Unknown Cricketer"

    cleaned = str(raw_name).strip().lower()

    # 1. Exact match in canonical dictionary
    if cleaned in CANONICAL_PLAYER_NAMES:
        return CANONICAL_PLAYER_NAMES[cleaned]

    # 2. Heuristic formatting for unmapped names:
    # E.g. "str binny" -> "S.T.R. Binny", "s aravind" -> "S. Aravind"
    parts = cleaned.split()
    if len(parts) >= 2:
        first_parts = parts[:-1]
        last_part = parts[-1].capitalize()

        # Check if first part consists of initials (each word 1-2 letters)
        formatted_initials = []
        is_initials = True
        for part in first_parts:
            if len(part) <= 2:
                formatted_initials.append(part.upper() + ".")
            else:
                is_initials = False
                break

        if is_initials:
            return f"{''.join(formatted_initials)} {last_part}"

    # Fallback to Title Case
    return " ".join(word.capitalize() for word in cleaned.split())
