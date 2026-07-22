<template>
  <article class="prose prose-sm md:prose-base max-w-none">
    <h1 class="text-2xl md:text-3xl font-bold text-[#2D2B6B] mb-2">Velas japonesas</h1>
    <p class="text-gray-500 mb-6">La forma más común de leer el precio en una gráfica de trading.</p>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">¿Qué es una vela japonesa?</h2>
      <p class="text-gray-700 leading-relaxed mb-4">
        Una vela japonesa es una figura que resume cómo se movió el precio durante un periodo de tiempo (un minuto, una
        hora, un día, etc.). Cada vela te dice cuatro cosas: a qué precio abrió, a qué precio cerró, el punto más alto y
        el punto más bajo en ese periodo.
      </p>
      <p class="text-gray-700 leading-relaxed">
        Las velas son tan populares porque, de un solo vistazo, te muestran si en ese periodo ganaron los compradores o
        los vendedores.
      </p>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Partes de una vela</h2>
      <ul class="list-disc list-inside text-gray-700 space-y-2 mb-4">
        <li><strong>Cuerpo:</strong> la parte ancha. Va del precio de apertura al de cierre.</li>
        <li><strong>Mechas o sombras:</strong> las líneas finas arriba y abajo. Marcan el precio máximo y mínimo alcanzado.</li>
        <li><strong>Color:</strong> normalmente verde (o blanco) si el precio subió, y rojo (o negro) si bajó.</li>
      </ul>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-green-50 border border-green-200 rounded-xl p-4">
          <h3 class="font-semibold text-green-800 mb-1">Vela alcista (verde)</h3>
          <p class="text-sm text-green-700">El precio cerró más arriba de donde abrió. Ganaron los compradores.</p>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-xl p-4">
          <h3 class="font-semibold text-red-800 mb-1">Vela bajista (roja)</h3>
          <p class="text-sm text-red-700">El precio cerró más abajo de donde abrió. Ganaron los vendedores.</p>
        </div>
      </div>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Velas individuales más conocidas</h2>
      <ul class="list-disc list-inside text-gray-700 space-y-2">
        <li><strong>Doji:</strong> abre y cierra casi en el mismo precio. Indica duda o indecisión en el mercado.</li>
        <li><strong>Martillo:</strong> cuerpo pequeño arriba y mecha larga abajo. Suele aparecer al final de una caída y sugerir un posible rebote.</li>
        <li><strong>Estrella fugaz:</strong> cuerpo pequeño abajo y mecha larga arriba. Puede anticipar una caída tras una subida.</li>
        <li><strong>Marubozu:</strong> vela con cuerpo grande y casi sin mechas. Indica una fuerza clara de un lado.</li>
      </ul>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Temporalidad de las velas</h2>
      <p class="text-gray-700 leading-relaxed">
        Cada vela representa un periodo que tú eliges. En una gráfica de 1 minuto, cada vela es un minuto; en una de 1
        día, cada vela es un día completo. Los traders de plazos cortos usan velas de minutos, mientras que quienes
        operan a más días suelen mirar velas diarias o semanales.
      </p>
    </section>
  </article>
</template>
