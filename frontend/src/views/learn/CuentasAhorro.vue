<template>
  <article class="prose prose-sm md:prose-base max-w-none">
    <h1 class="text-2xl md:text-3xl font-bold text-[#2D2B6B] mb-2">Cuentas de ahorro</h1>
    <p class="text-gray-500 mb-6">Las cuentas de ahorro con rendimiento son una forma sencilla y líquida de hacer crecer tu dinero.</p>

    <!-- Qué son -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">¿Qué son?</h2>
      <p class="text-gray-700 leading-relaxed mb-4">
        Una cuenta de ahorro con rendimiento es un producto bancario o de fintech donde tu dinero genera intereses
        diariamente, sin tener que comprometerlo a un plazo fijo. Puedes retirarlo cuando quieras y, mientras tanto,
        sigue ganando rendimientos.
      </p>
      <p class="text-gray-700 leading-relaxed">
        En México, fintechs como Nu, Mercado Pago, Stori, Ualá, Klar, Finsus y Didi han popularizado este tipo de
        cuentas con tasas competitivas, muchas veces superiores a las que ofrecen los bancos tradicionales.
      </p>
    </section>

    <!-- Cómo funcionan -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">¿Cómo funcionan?</h2>
      <ul class="list-disc list-inside text-gray-700 space-y-2">
        <li><strong>Rendimiento diario:</strong> Los intereses se calculan cada día sobre tu saldo y se abonan periódicamente (diario, semanal o mensual según la institución).</li>
        <li><strong>Tasa anual (GAT):</strong> Se expresa como Ganancia Anual Total. Es lo que ganarías en un año si la tasa se mantiene igual.</li>
        <li><strong>Liquidez total:</strong> Puedes disponer de tu dinero en cualquier momento, sin penalizaciones.</li>
        <li><strong>Sin monto mínimo:</strong> La mayoría no exige un saldo mínimo para empezar.</li>
      </ul>
    </section>

    <!-- Tipos de cuentas -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Tipos de cuentas</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-2">A la vista (líquidas)</h3>
          <p class="text-sm text-gray-600">Tu dinero está disponible 24/7. Tasas más bajas pero máxima flexibilidad. Ideal para fondo de emergencia.</p>
        </div>
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-2">A plazo (congeladas)</h3>
          <p class="text-sm text-gray-600">Comprometes tu dinero por días o meses a cambio de una tasa más alta. Si retiras antes, pierdes intereses.</p>
        </div>
      </div>
    </section>

    <!-- Seguridad -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Seguridad: IPAB y PROSOFIPO</h2>
      <p class="text-gray-700 leading-relaxed mb-4">
        Las cuentas de ahorro en México están protegidas dependiendo del tipo de institución:
      </p>
      <ul class="list-disc list-inside text-gray-700 space-y-2">
        <li><strong>IPAB (bancos):</strong> Protege hasta 400,000 UDIs (~3.2 millones de pesos) por persona, por institución.</li>
        <li><strong>PROSOFIPO (SOFIPOS):</strong> Protege hasta 25,000 UDIs (~200 mil pesos) por persona, por institución.</li>
        <li><strong>Fintechs (IFPE):</strong> No tienen seguro de depósito directo. Suelen apoyarse en un banco aliado o en fideicomisos.</li>
      </ul>
    </section>

    <!-- Ventajas y desventajas -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Ventajas y desventajas</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-green-50 border border-green-200 rounded-xl p-4">
          <h3 class="font-semibold text-green-800 mb-2">Ventajas</h3>
          <ul class="text-sm text-green-700 space-y-1">
            <li>• Liquidez total (a la vista)</li>
            <li>• Sin monto mínimo</li>
            <li>• Apertura 100% digital</li>
            <li>• Rendimiento diario</li>
            <li>• Tasas competitivas vs. bancos tradicionales</li>
          </ul>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-xl p-4">
          <h3 class="font-semibold text-red-800 mb-2">Desventajas</h3>
          <ul class="text-sm text-red-700 space-y-1">
            <li>• Las tasas pueden cambiar sin aviso</li>
            <li>• Algunas tienen tope máximo para tasa preferente</li>
            <li>• Menos cobertura del seguro de depósito en SOFIPOS/fintechs</li>
            <li>• ISR retenido sobre los intereses</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Conclusión -->
    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Conclusión</h2>
      <p class="text-gray-700 leading-relaxed mb-4">
        Las cuentas de ahorro con rendimiento son perfectas para tu fondo de emergencia y para el dinero que necesitas
        tener disponible. Combinan seguridad, liquidez y un rendimiento que al menos te ayuda a no perder tanto frente
        a la inflación.
      </p>
      <p class="text-gray-700 leading-relaxed">
        Compara las tasas vigentes en nuestra
        <router-link to="/tasas" class="text-[#2D2B6B] font-semibold underline hover:text-[#4A48A0]">sección de tasas</router-link>
        para encontrar la mejor opción según tu perfil.
      </p>
    </section>
  </article>
</template>
