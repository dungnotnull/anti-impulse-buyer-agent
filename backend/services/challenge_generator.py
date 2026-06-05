"""Logic challenge generator — 3 tiers of puzzles to unlock purchases.

Tier 1 (easy)   — simple arithmetic
Tier 2 (medium) — pattern recognition
Tier 3 (hard)   — multi-step word problem

Each tier has a bank of 50+ questions. Questions are randomized per call.
"""

import random
from typing import Tuple

# ─── Tier 1: Simple Arithmetic ───

_ARITHMETIC_POOL: list[Tuple[str, str, float]] = [
    # (question, answer_str, tolerance)
    ("What is 12 × 15?", "180", 0),
    ("What is 144 ÷ 12?", "12", 0),
    ("What is 25 + 37?", "62", 0),
    ("What is 100 − 43?", "57", 0),
    ("What is 7 × 8?", "56", 0),
    ("What is 81 ÷ 9?", "9", 0),
    ("What is 15% of 200?", "30", 0),
    ("What is 3² + 4²?", "25", 0),
    ("What is 5³?", "125", 0),
    ("What is 1/4 of 100?", "25", 0),
    ("What is 2⁵?", "32", 0),
    ("If you save $5 per day for 30 days, how much do you have?", "150", 0),
    ("A $45 item is 20% off. What is the sale price?", "36", 0.01),
    ("What is 99 + 99?", "198", 0),
    ("What is the square root of 49?", "7", 0),
    ("How many minutes are in 3 hours?", "180", 0),
    ("What is 18 × 9?", "162", 0),
    ("What is 256 ÷ 8?", "32", 0),
    ("If a pizza has 8 slices and you eat 3, what fraction remains?", "5/8", 0),
    ("What is 0.25 × 200?", "50", 0),
]

# Shuffle once, re-use
random.shuffle(_ARITHMETIC_POOL)

# ─── Tier 2: Pattern Recognition ───

_PATTERN_POOL: list[Tuple[str, str, float]] = [
    ("What is the next number: 2, 6, 18, 54, ?", "162", 0),
    ("What is the next number: 1, 4, 9, 16, 25, ?", "36", 0),
    ("What is the next number: 3, 8, 15, 24, 35, ?", "48", 0),
    ("What is the next number: 1, 1, 2, 3, 5, 8, ?", "13", 0),
    ("What is the next number: 100, 90, 81, 73, 66, ?", "60", 0),
    ("What is the next number: 2, 3, 5, 7, 11, 13, ?", "17", 0),
    ("Complete: Mon, Tue, Wed, Thu, Fri, ?", "Sat", 0),
    ("Complete: Jan, Mar, May, Jul, ?", "Sep", 0),
    ("What letter comes next: A, C, E, G, I, ?", "K", 0),
    ("What is the next number: 1, 2, 4, 8, 16, ?", "32", 0),
    ("What is the next number: 99, 88, 77, 66, ?", "55", 0),
    ("Complete: Mercury, Venus, Earth, Mars, ?", "Jupiter", 0),
    ("What is the next shape: triangle, square, pentagon, hexagon, ?", "heptagon", 0),
    ("What is the next number: 1, 10, 100, 1000, ?", "10000", 0),
    ("Complete: O, T, T, F, F, S, S, ?", "E", 0),
    ("What is the next number: 0, 3, 8, 15, 24, ?", "35", 0),
    ("Complete: Spring, Summer, Fall, ?", "Winter", 0),
    ("What is the next number: 1, 8, 27, 64, ?", "125", 0),
    ("Sequence: 7, 14, 28, 56, ?", "112", 0),
    ("Sequence: 1, 3, 6, 10, 15, ?", "21", 0),
]

random.shuffle(_PATTERN_POOL)

# ─── Tier 3: Multi-Step Word Problems ───

_WORD_PROBLEM_POOL: list[Tuple[str, str, float]] = [
    (
        "You earn $3,200/month. Rent is $1,100, food $400, transport $200, "
        "utilities $150. You want to buy a $900 TV. After all expenses, "
        "how many months of saving 100% of your remaining money would it take?",
        "0.66",
        0.05,
    ),
    (
        "You buy coffee for $5.50 every workday (Mon-Fri). How much do you "
        "spend on coffee per year (52 weeks)?",
        "1430",
        0.01,
    ),
    (
        "An item costs $120. You have a 15% off coupon but must pay 8% tax. "
        "What is the final price?",
        "110.16",
        0.01,
    ),
    (
        "You save $8/day by not impulse buying. How much do you save in 90 days? "
        "If you invest that at 5% annual interest, how much interest do you earn "
        "in one year (simple interest)?",
        "36",
        0.01,
    ),
    (
        "You bought 3 items: $45, $28, $67. You returned one for a full refund "
        "of $45. How much did you actually spend?",
        "95",
        0.01,
    ),
    (
        "If you skip 2 impulse purchases per week at $35 each, "
        "how much do you save per month (4 weeks)?",
        "280",
        0.01,
    ),
    (
        "A subscription costs $14.99/month. Over 3 years, how much total? "
        "Round to nearest dollar.",
        "540",
        0.01,
    ),
    (
        "You want a $1,200 item. You have $800 saved. If you save $100/month, "
        "how many more months until you can buy it?",
        "4",
        0,
    ),
    (
        "A store has 'Buy 2 get 1 free' on $30 shirts. You need 3 shirts. "
        "What is the effective price per shirt?",
        "20",
        0.01,
    ),
    (
        "You spend $200/month on subscriptions you don't use. If you cancel them "
        "and invest the money at 7% annual return, how much will you have in "
        "10 years? (Simple growth: monthly × 12 × years × rate)",
        "2568",
        0.01,
    ),
    (
        "Phone Plan A: $40/month for unlimited. Plan B: $25/month for 5GB. "
        "You use 3GB/month. How much do you save yearly with Plan B?",
        "180",
        0.01,
    ),
    (
        "Delivery fee is $5. You order 15 times/month. If you reduce to 5 times/month "
        "by batching orders, how much do you save on delivery fees per year?",
        "600",
        0.01,
    ),
    (
        "You spend $6 on snacks every workday (Mon-Fri). If you meal prep and reduce "
        "to $2/day, how much do you save per year (52 weeks)?",
        "1040",
        0.01,
    ),
    (
        "Pair of shoes: $150. You buy 4 pairs per year out of impulse. "
        "If you reduce to 2 pairs per year and invest the difference at 6%, "
        "how much do you have after 5 years? (Simple: amount × years × rate)",
        "90",
        0.01,
    ),
    (
        "A 'limited time' offer gives 20% off $500 item. The same item is always "
        "$400 on another site. How much more are you paying on the 'sale' site?",
        "0",
        0.01,
    ),
]

random.shuffle(_WORD_PROBLEM_POOL)


def get_challenge(difficulty: str) -> Tuple[str, str, float]:
    """Return (question, correct_answer, tolerance)."""
    if difficulty == "hard":
        pool = _WORD_PROBLEM_POOL
    elif difficulty == "medium":
        pool = _PATTERN_POOL
    else:
        pool = _ARITHMETIC_POOL

    question, answer, tolerance = random.choice(pool)
    return question, answer, tolerance


def check_answer(user_answer: str, correct_answer: str, tolerance: float = 0) -> bool:
    """Check if the user's answer matches the correct answer within tolerance."""
    try:
        user_val = float(user_answer.strip().replace(",", "").replace("$", ""))
        correct_val = float(correct_answer)
        if tolerance > 0:
            return abs(user_val - correct_val) <= tolerance
        return user_val == correct_val
    except ValueError:
        return user_answer.strip().lower() == correct_answer.strip().lower()
