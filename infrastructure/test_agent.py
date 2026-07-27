"""Test the Fina agent with various scenarios to validate system prompt compliance."""
import asyncio
import sys
sys.path.insert(0, "/home/ubuntu/Finalat")

from backend.models.database import async_session
from backend.services.fina_agent import fina_chat

async def test_conversation(messages, user_name="Adrian"):
    """Send a conversation and print the response."""
    converse_messages = []
    for msg in messages:
        converse_messages.append({
            "role": msg["role"],
            "content": [{"text": msg["content"]}]
        })
    
    async with async_session() as db:
        response, result = await fina_chat(converse_messages, db, user_name=user_name)
    return response

async def main():
    print("=" * 60)
    print("TEST 1: Quiero invertir 100mil pesos")
    print("  (Should ask ONE question at a time - amount first)")
    print("=" * 60)
    r = await test_conversation([
        {"role": "user", "content": "Quiero invertir 100 mil pesos"}
    ])
    print(f"  RESPONSE: {r[:300]}")
    print()

    # Check: should NOT mention stocks/ETFs, should ask about plazo
    has_etf = any(w in r.lower() for w in ['etf', 'accion', 'portafolio de inversión', 'renta variable'])
    has_one_question = r.count('?') <= 2  # Should only have 1-2 questions max
    print(f"  ✓ No ETFs/acciones: {'PASS' if not has_etf else 'FAIL'}")
    print(f"  ✓ One question at a time: {'PASS' if has_one_question else 'FAIL'}")
    print()

    print("=" * 60)
    print("TEST 2: User says 1 año (after plazo question)")
    print("  (Should ask about liquidity next)")
    print("=" * 60)
    r = await test_conversation([
        {"role": "user", "content": "Quiero invertir 100 mil pesos"},
        {"role": "assistant", "content": "Perfecto Adrian, 100 mil pesos es un buen monto. ¿En cuánto tiempo necesitas ese dinero? [[SLIDER_PLAZO]]"},
        {"role": "user", "content": "1 año"}
    ])
    print(f"  RESPONSE: {r[:300]}")
    print()
    
    has_thinking = any(w in r.lower() for w in ['el usuario', 'necesito', 'voy a pregunt', '<thinking>'])
    print(f"  ✓ No thinking exposed: {'PASS' if not has_thinking else 'FAIL'}")
    print()

    print("=" * 60)
    print("TEST 3: User says NO to accounts with purchase requirements")
    print("  (Should only recommend accounts WITHOUT purchase requirements)")
    print("=" * 60)
    r = await test_conversation([
        {"role": "user", "content": "Quiero invertir 50 mil pesos"},
        {"role": "assistant", "content": "¿En cuánto tiempo necesitas ese dinero? [[SLIDER_PLAZO]]"},
        {"role": "user", "content": "6 meses"},
        {"role": "assistant", "content": "¿Necesitas tener acceso inmediato al dinero o puedes dejarlo quieto durante esos 6 meses?"},
        {"role": "user", "content": "Puede estar quieto"},
        {"role": "assistant", "content": "¿Tienes o estarías dispuesto a abrir cuentas en Nu, Ualá o Didi para aprovechar tasas preferenciales que requieren hacer compras con tarjeta?"},
        {"role": "user", "content": "No, no quiero cuentas que me pidan hacer compras"}
    ])
    print(f"  RESPONSE: {r[:500]}")
    print()

    # Should NOT recommend Nu Turbo, Ualá Plus, Klar Inversión
    has_purchase_account = any(w in r.lower() for w in ['cajita turbo', 'ualá plus', 'ualá cuenta plus', 'klar inversión'])
    has_calculation = '$' in r and 'rendimiento' in r.lower()
    print(f"  ✓ No purchase-required accounts: {'PASS' if not has_purchase_account else 'FAIL'}")
    print(f"  ✓ Has calculation/recommendation: {'PASS' if has_calculation else 'MAYBE (may need more context)'}")
    print()

    print("=" * 60)
    print("TEST 4: Ask about stocks (should redirect)")
    print("=" * 60)
    r = await test_conversation([
        {"role": "user", "content": "¿Me recomiendas algunas acciones para comprar?"}
    ])
    print(f"  RESPONSE: {r[:300]}")
    print()
    
    recommends_stocks = any(w in r.lower() for w in ['te recomiendo comprar', 'estas acciones', 'compra aapl', 'invierte en tesla'])
    redirects = any(w in r.lower() for w in ['ahorro', 'cuenta', 'cetes', 'no recomiendo acciones', 'no asesoro'])
    print(f"  ✓ Does NOT recommend specific stocks: {'PASS' if not recommends_stocks else 'FAIL'}")
    print(f"  ✓ Redirects to savings: {'PASS' if redirects else 'CHECK'}")

asyncio.run(main())
