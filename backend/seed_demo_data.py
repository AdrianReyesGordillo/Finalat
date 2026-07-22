"""Seed demo/fake data for user adriax45@gmail.com for visualization purposes.

Run with: python -m backend.seed_demo_data

Creates sample data across all financial modules:
- Savings accounts (ahorro)
- Credit cards (creditos)
- Debts (deudas)
- Expenses/Income (gastos_ingresos + categories)
- Contributions (aportaciones)
- Afore (retirement)
- GBM Portfolio (stocks)
"""

import asyncio
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ahorro import Ahorro
from backend.models.afore import Afore
from backend.models.aportaciones import Aportacion
from backend.models.categories import Category
from backend.models.creditos import Credito
from backend.models.deudas import Deuda
from backend.models.gastos_ingresos import GastoIngreso
from backend.models.gbm_portfolio import GbmPortfolio
from backend.models.user import User
from backend.models.database import async_session
from backend.services.encryption import encryption_service

TARGET_EMAIL = "adriax45@gmail.com"


def enc(value) -> str:
    """Encrypt a value for storage."""
    return encryption_service.encrypt(str(value))


async def seed_demo() -> None:
    """Insert demo financial data for the target user."""

    async with async_session() as db:
        # Find the user by email
        result = await db.execute(
            select(User).where(User.email == TARGET_EMAIL)
        )
        user = result.scalars().first()

        if not user:
            print(f"User {TARGET_EMAIL} not found in database. Creating placeholder...")
            user = User(
                user_id="demo_adriax45_uid",
                email=TARGET_EMAIL,
                display_name="Adrian Reyes",
            )
            db.add(user)
            await db.flush()

        uid = user.user_id
        print(f"Seeding demo data for user: {uid} ({TARGET_EMAIL})")

        # Check if demo data already exists (check ahorro as indicator)
        existing = await db.execute(
            select(Ahorro).where(Ahorro.user_id == uid).limit(1)
        )
        if existing.scalars().first():
            print("Demo data already exists. Skipping.")
            return

        # ─── AHORRO (Savings Accounts) ───────────────────────────────────
        savings = [
            {"account_name": "Nu México", "amount": 45000.00},
            {"account_name": "Mercado Pago", "amount": 12500.50},
            {"account_name": "CETES 28 días", "amount": 80000.00},
            {"account_name": "Stori", "amount": 8200.00},
        ]
        for s in savings:
            db.add(Ahorro(
                id=str(uuid.uuid4()),
                user_id=uid,
                account_name=s["account_name"],
                amount_encrypted=enc(s["amount"]),
            ))

        # ─── CREDITOS (Credit Cards) ─────────────────────────────────────
        cards = [
            {"card_name": "Nu", "balance": 3500.00, "limit": 25000.00, "min_payment": 450.00},
            {"card_name": "BBVA Azul", "balance": 12800.00, "limit": 40000.00, "min_payment": 1650.00},
            {"card_name": "Rappi Card", "balance": 800.00, "limit": 15000.00, "min_payment": 180.00},
        ]
        for c in cards:
            db.add(Credito(
                id=str(uuid.uuid4()),
                user_id=uid,
                card_name=c["card_name"],
                balance_encrypted=enc(c["balance"]),
                limit_encrypted=enc(c["limit"]),
                min_payment_encrypted=enc(c["min_payment"]),
            ))

        # ─── DEUDAS (Debts) ──────────────────────────────────────────────
        debts = [
            {"creditor": "Fonacot", "total": 28000.00, "monthly": 2800.00, "rate": 24.5, "start": date(2024, 6, 15)},
            {"creditor": "Liverpool MSI", "total": 9600.00, "monthly": 1600.00, "rate": 0.0, "start": date(2025, 1, 10)},
        ]
        for d in debts:
            db.add(Deuda(
                id=str(uuid.uuid4()),
                user_id=uid,
                creditor_name=d["creditor"],
                total_amount_encrypted=enc(d["total"]),
                monthly_payment_encrypted=enc(d["monthly"]),
                interest_rate=Decimal(str(d["rate"])),
                start_date=d["start"],
            ))

        # ─── CATEGORIES ──────────────────────────────────────────────────
        cat_names = ["Comida", "Transporte", "Entretenimiento", "Servicios", "Salario", "Freelance"]
        cat_ids = {}
        for name in cat_names:
            cid = str(uuid.uuid4())
            cat_ids[name] = cid
            db.add(Category(
                id=cid,
                user_id=uid,
                name=name,
                is_system=False,
            ))

        # ─── GASTOS / INGRESOS (last 30 days) ────────────────────────────
        today = date.today()
        expenses = [
            {"desc": "Uber Eats", "amount": 189.00, "cat": "Comida", "days_ago": 1},
            {"desc": "Gasolina", "amount": 850.00, "cat": "Transporte", "days_ago": 3},
            {"desc": "Netflix", "amount": 299.00, "cat": "Entretenimiento", "days_ago": 5},
            {"desc": "Spotify", "amount": 149.00, "cat": "Entretenimiento", "days_ago": 5},
            {"desc": "CFE", "amount": 420.00, "cat": "Servicios", "days_ago": 8},
            {"desc": "Super Walmart", "amount": 1250.00, "cat": "Comida", "days_ago": 10},
            {"desc": "Internet Telmex", "amount": 599.00, "cat": "Servicios", "days_ago": 12},
            {"desc": "Uber", "amount": 145.00, "cat": "Transporte", "days_ago": 14},
            {"desc": "Restaurante", "amount": 680.00, "cat": "Comida", "days_ago": 16},
            {"desc": "Amazon Prime", "amount": 99.00, "cat": "Entretenimiento", "days_ago": 18},
            {"desc": "Mandado semanal", "amount": 980.00, "cat": "Comida", "days_ago": 21},
            {"desc": "Gasolina", "amount": 900.00, "cat": "Transporte", "days_ago": 24},
            {"desc": "Cine", "amount": 320.00, "cat": "Entretenimiento", "days_ago": 26},
            {"desc": "Agua", "amount": 180.00, "cat": "Servicios", "days_ago": 28},
        ]
        incomes = [
            {"desc": "Nómina quincenal", "amount": 18500.00, "cat": "Salario", "days_ago": 2},
            {"desc": "Nómina quincenal", "amount": 18500.00, "cat": "Salario", "days_ago": 17},
            {"desc": "Proyecto web freelance", "amount": 5000.00, "cat": "Freelance", "days_ago": 9},
        ]

        for e in expenses:
            db.add(GastoIngreso(
                id=str(uuid.uuid4()),
                user_id=uid,
                type="expense",
                amount_encrypted=enc(e["amount"]),
                description_encrypted=enc(e["desc"]),
                category_id=cat_ids[e["cat"]],
                entry_date=today - timedelta(days=e["days_ago"]),
            ))

        for i in incomes:
            db.add(GastoIngreso(
                id=str(uuid.uuid4()),
                user_id=uid,
                type="income",
                amount_encrypted=enc(i["amount"]),
                description_encrypted=enc(i["desc"]),
                category_id=cat_ids[i["cat"]],
                entry_date=today - timedelta(days=i["days_ago"]),
            ))

        # ─── APORTACIONES (Contributions) ────────────────────────────────
        contributions = [
            {"target": "Fondo de emergencia", "amount": 2000.00, "freq": "biweekly", "start": date(2025, 1, 1)},
            {"target": "Vacaciones", "amount": 1500.00, "freq": "monthly", "start": date(2025, 3, 1)},
            {"target": "Inversión CETES", "amount": 3000.00, "freq": "monthly", "start": date(2025, 2, 15)},
        ]
        for a in contributions:
            db.add(Aportacion(
                id=str(uuid.uuid4()),
                user_id=uid,
                amount_encrypted=enc(a["amount"]),
                frequency=a["freq"],
                target_name=a["target"],
                start_date=a["start"],
            ))

        # ─── AFORE (Retirement) ──────────────────────────────────────────
        db.add(Afore(
            id=str(uuid.uuid4()),
            user_id=uid,
            provider_name="Profuturo",
            balance_encrypted=enc(125800.50),
            last_update_date=date(2026, 7, 1),
        ))

        # ─── GBM PORTFOLIO ───────────────────────────────────────────────
        positions = [
            {"ticker": "VOO", "shares": 3.5, "avg_cost": 420.50, "market_value": 1580.00},
            {"ticker": "NAFTRAC", "shares": 150.0, "avg_cost": 52.30, "market_value": 8250.00},
            {"ticker": "FUNO 11", "shares": 200.0, "avg_cost": 22.80, "market_value": 4800.00},
            {"ticker": "BITO", "shares": 10.0, "avg_cost": 18.90, "market_value": 215.00},
        ]
        for p in positions:
            db.add(GbmPortfolio(
                id=str(uuid.uuid4()),
                user_id=uid,
                ticker=p["ticker"],
                shares=Decimal(str(p["shares"])),
                avg_cost_encrypted=enc(p["avg_cost"]),
                market_value_encrypted=enc(p["market_value"]),
            ))

        await db.commit()
        print("Demo data seeded successfully!")
        print(f"  - {len(savings)} savings accounts")
        print(f"  - {len(cards)} credit cards")
        print(f"  - {len(debts)} debts")
        print(f"  - {len(expenses)} expenses + {len(incomes)} incomes")
        print(f"  - {len(contributions)} contributions")
        print(f"  - 1 afore account")
        print(f"  - {len(positions)} GBM positions")


async def main() -> None:
    await seed_demo()


if __name__ == "__main__":
    asyncio.run(main())
