"""Test the finanzas loaders directly against the DB with the real user_id."""
import asyncio
import sys
sys.path.insert(0, "/home/ubuntu/Finalat")

from backend.models.database import async_session
from backend.routers.finanzas import (
    _load_gi_records, _load_ahorro, _load_creditos,
    _load_deudas, _load_afore, _load_gbm,
)

UID = "TMti8ciOrQbO2n3soWErc1dILTo1"


async def main():
    async with async_session() as db:
        records = await _load_gi_records(db, UID)
        print(f"GI records: {len(records)}")
        for r in records[:3]:
            print(f"   {r['date']} | {r['description']} | {r['amount']} | {r['category']}")

        ahorro = await _load_ahorro(db, UID)
        print(f"\nAhorro: {len(ahorro)}")
        for a in ahorro:
            print(f"   {a['name']} | {a['balance']}")

        cards = await _load_creditos(db, UID)
        print(f"\nCreditos: {len(cards)}")
        for c in cards:
            print(f"   {c['name']} | debt={c['debt']} limit={c['creditLimit']} usage={c['usagePercent']}%")

        deudas = await _load_deudas(db, UID)
        print(f"\nDeudas: {len(deudas)}")
        for d in deudas:
            print(f"   {d['name']} | total={d['total']} monthly={d['monthlyPayment']}")

        afore = await _load_afore(db, UID)
        print(f"\nAfore: {afore}")

        nacional, summary = await _load_gbm(db, UID)
        print(f"\nGBM positions: {len(nacional)}, summary={summary}")


asyncio.run(main())
