"""Verify the Afore aportacion → Inversiones/Afore voluntary contribution link."""
import asyncio
import sys
sys.path.insert(0, "/home/ubuntu/Finalat")

from backend.models.database import async_session
from backend.routers.finanzas import _load_afore

UID = "TMti8ciOrQbO2n3soWErc1dILTo1"

async def main():
    async with async_session() as db:
        afore_data = await _load_afore(db, UID)
    
    print("=== Inversiones → Afore data ===")
    for k, v in afore_data.items():
        print(f"  {k}: {v}")
    
    print(f"\n  voluntaryContribution = {afore_data.get('voluntaryContribution', 'NOT SET')}")
    print(f"  (This should match the weekly amount configured in Configuración → Aportaciones → Afore)")

asyncio.run(main())
