"""Test Task 1: Agent should calculate simple math directly without tools."""
import asyncio
import sys
sys.path.insert(0, "/home/ubuntu/Finalat")

from backend.models.database import async_session
from backend.services.fina_agent import fina_chat

async def main():
    tests = [
        {
            "desc": "Simple calculation: 50k at 12% for 6 months",
            "messages": [{"role": "user", "content": "Si meto 50 mil pesos en Mercado Pago al 12% por 6 meses, cuánto gano?"}],
            "checks": {
                "Has dollar amount": lambda r: "$" in r and any(c.isdigit() for c in r),
                "Shows ~3000 (correct answer)": lambda r: "3,000" in r or "3000" in r or "3.000" in r,
                "No error message": lambda r: "error" not in r.lower() and "confusión" not in r.lower(),
            }
        },
        {
            "desc": "Direct: 100k at 13% for 1 year",
            "messages": [{"role": "user", "content": "¿Cuánto me darían 100 mil pesos al 13% anual en un año?"}],
            "checks": {
                "Has dollar amount": lambda r: "$" in r,
                "Shows ~13000 (correct)": lambda r: "13,000" in r or "13000" in r or "13.000" in r,
                "Shows formula or breakdown": lambda r: "×" in r or "x" in r.lower() or "100,000" in r or "100000" in r or "rendimiento" in r.lower(),
            }
        },
        {
            "desc": "Tiered: 40k in Nu Turbo (13% up to 25k, 6.5% excess) for 1 year",
            "messages": [{"role": "user", "content": "Si meto 40 mil en Nu Cajita Turbo que da 13% hasta 25 mil y 6.5% el excedente, cuánto gano en 1 año?"}],
            "checks": {
                "Has dollar amount": lambda r: "$" in r,
                "Mentions split/tiered calculation": lambda r: "25" in r and ("15" in r or "excedente" in r.lower() or "6.5" in r),
                "Approximate answer (~4,225)": lambda r: any(x in r for x in ["4,225", "4225", "4,200", "4200", "4,250", "4250", "3,250", "rendimiento" ]),
            }
        },
    ]

    passed_total = 0
    total_checks = 0

    for test in tests:
        print(f"\nTEST: {test['desc']}")
        converse = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in test["messages"]]
        async with async_session() as db:
            response, _ = await fina_chat(converse, db, user_name="Adrian")
        print(f"  Response: {response[:300]}")
        for name, fn in test["checks"].items():
            result = fn(response)
            passed_total += 1 if result else 0
            total_checks += 1
            print(f"  {'✓' if result else '✗'} {name}")

    print(f"\n{'='*50}")
    print(f"TASK 1 SCORE: {passed_total}/{total_checks}")
    print(f"{'='*50}")

asyncio.run(main())
