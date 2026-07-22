<template>
  <article class="prose prose-sm md:prose-base max-w-none">
    <h1 class="text-2xl md:text-3xl font-bold text-[#2D2B6B] mb-2">¿Cómo funciona una tarjeta de crédito?</h1>
    <p class="text-gray-500 mb-6">Entiende el mecanismo detrás de este instrumento financiero, sus costos y cómo usarla a tu favor.</p>

    <!-- Intro -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">¿Qué es una tarjeta de crédito?</h2>
      <p>
        Una tarjeta de crédito es un medio de pago que te permite realizar compras con dinero que el banco te presta.
        A diferencia de una tarjeta de débito (donde gastas tu propio saldo), con una de crédito estás usando una
        <strong>línea de crédito</strong> que debes pagar después.
      </p>
    </section>

    <!-- Ciclo de facturación -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">El ciclo de facturación</h2>
      <p class="mb-3">Cada tarjeta tiene un ciclo mensual con dos fechas clave:</p>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>Fecha de corte:</strong> El día en que se cierra tu estado de cuenta y se calcula cuánto debes.</li>
        <li><strong>Fecha límite de pago:</strong> El último día para pagar sin generar intereses (generalmente 20 días después del corte).</li>
      </ul>
      <div class="bg-[#F0F0FA] border border-[#E0E0F0] rounded-xl p-4 mt-4">
        <p class="text-sm text-[#2D2B6B] font-medium">💡 Si pagas el total antes de la fecha límite, no pagas intereses. Es como un préstamo gratis de hasta ~50 días.</p>
      </div>
    </section>

    <!-- Pagos -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">Tipos de pago</h2>
      <div class="grid gap-4 md:grid-cols-3">
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-1">Pago total</h3>
          <p class="text-sm text-gray-600">Pagas todo lo que debes. Sin intereses. Es la mejor opción siempre.</p>
        </div>
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-1">Pago mínimo</h3>
          <p class="text-sm text-gray-600">Evitas que te reporten en Buró, pero el resto genera intereses altos (30-60% anual).</p>
        </div>
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-1">No pagar</h3>
          <p class="text-sm text-gray-600">Se generan intereses moratorios, comisiones y un impacto negativo en tu historial crediticio.</p>
        </div>
      </div>
    </section>

    <!-- CAT y tasas -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">Costos: tasa de interés y CAT</h2>
      <ul class="list-disc pl-5 space-y-2">
        <li><strong>Tasa de interés anual:</strong> Lo que el banco cobra sobre el saldo no pagado. En México va del 25% al 70%+ dependiendo de la tarjeta.</li>
        <li><strong>CAT (Costo Anual Total):</strong> Incluye intereses + comisiones + anualidad. Es el indicador real del costo de tu tarjeta.</li>
        <li><strong>Anualidad:</strong> Cobro anual por tener la tarjeta. Muchas tarjetas la eliminan si alcanzas cierto nivel de gasto.</li>
      </ul>
    </section>

    <!-- Ventajas y riesgos -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">Ventajas y riesgos</h2>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="bg-green-50 border border-green-200 rounded-xl p-4">
          <h3 class="font-semibold text-green-800 mb-2">✅ Ventajas</h3>
          <ul class="text-sm text-green-900 space-y-1 list-disc pl-4">
            <li>Construyes historial crediticio</li>
            <li>Financiamiento sin intereses (pagando total)</li>
            <li>Protección en compras y seguros</li>
            <li>Recompensas, cashback o puntos</li>
            <li>Meses sin intereses en comercios</li>
          </ul>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-xl p-4">
          <h3 class="font-semibold text-red-800 mb-2">⚠️ Riesgos</h3>
          <ul class="text-sm text-red-900 space-y-1 list-disc pl-4">
            <li>Intereses muy altos si no pagas el total</li>
            <li>Fácil caer en deuda al gastar de más</li>
            <li>Comisiones por disposición de efectivo</li>
            <li>Pago mínimo crea una trampa de deuda</li>
            <li>Puede afectar tu score de Buró</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Tips -->
    <section class="mb-8">
      <h2 class="text-xl font-semibold text-[#2D2B6B] mb-3">Consejos para usarla bien</h2>
      <ol class="list-decimal pl-5 space-y-2">
        <li><strong>Paga siempre el total</strong> antes de la fecha límite.</li>
        <li><strong>No uses más del 30%</strong> de tu línea de crédito (mejora tu score).</li>
        <li><strong>Nunca saques efectivo</strong> del cajero con tu TDC: comisión + intereses desde el día 1.</li>
        <li><strong>Revisa tu estado de cuenta</strong> cada mes para detectar cargos no reconocidos.</li>
        <li><strong>Compara el CAT</strong>, no solo la tasa, al elegir una tarjeta.</li>
      </ol>
    </section>

    <!-- Resumen -->
    <div class="bg-[#FAFAFE] border border-[#E0E0F0] rounded-xl p-6">
      <h3 class="font-semibold text-[#2D2B6B] mb-2">En resumen</h3>
      <p class="text-sm text-gray-600">
        Una tarjeta de crédito es una herramienta poderosa si se usa con disciplina: te da financiamiento gratis,
        construye tu historial y ofrece beneficios. Pero si no pagas el total cada mes, los intereses pueden
        convertirla en una trampa costosa. La clave es tratarla como si fuera débito: no gastes lo que no tienes.
      </p>
    </div>
  </article>
</template>
