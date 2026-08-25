"""Pakistan salaried-income tax computation (FY 2025-26 slabs).

Annual taxable salary slabs for salaried individuals:

    up to   600,000            0%
    600,001 – 1,200,000       5% of excess over 600,000
    1,200,001 – 2,200,000    30,000 + 15% of excess over 1,200,000
    2,200,001 – 3,200,000   180,000 + 25% of excess over 2,200,000
    3,200,001 – 4,100,000   430,000 + 30% of excess over 3,200,000
    above    4,100,000      700,000 + 35% of excess over 4,100,000

Monthly withholding = annual tax / 12.
"""

from decimal import Decimal, ROUND_HALF_UP

SLABS = [
    (Decimal("600000"), Decimal("0"), Decimal("0")),
    (Decimal("1200000"), Decimal("0.05"), Decimal("0")),
    (Decimal("2200000"), Decimal("0.15"), Decimal("30000")),
    (Decimal("3200000"), Decimal("0.25"), Decimal("180000")),
    (Decimal("4100000"), Decimal("0.30"), Decimal("430000")),
]


def annual_tax(annual_taxable):
    """Return the annual income tax for a salaried amount."""
    amount = max(Decimal(str(annual_taxable)), Decimal("0"))

    if amount <= SLABS[0][0]:
        return Decimal("0")

    previous_cap, _, _ = SLABS[0]

    for cap, rate, base in SLABS[1:]:
        if amount <= cap:
            tax = base + (amount - previous_cap) * rate
            return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        previous_cap = cap

    top_cap, top_rate, top_base = SLABS[-1]
    tax = top_base + (amount - top_cap) * Decimal("0.35")

    return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def monthly_withholding(monthly_gross):
    annual = Decimal(str(monthly_gross)) * 12

    return (
        annual_tax(annual) / 12
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
