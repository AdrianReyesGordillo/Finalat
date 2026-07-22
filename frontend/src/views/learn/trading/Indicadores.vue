<template>
  <article class="prose prose-sm md:prose-base max-w-none">
    <h1 class="text-2xl md:text-3xl font-bold text-[#2D2B6B] mb-2">Indicadores</h1>
    <p class="text-gray-500 mb-6">Herramientas matemáticas que se dibujan sobre la gráfica para apoyar tus decisiones.</p>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">¿Qué es un indicador?</h2>
      <p class="text-gray-700 leading-relaxed mb-4">
        Un indicador técnico es un cálculo que se hace con los datos del precio y el volumen, y que se muestra sobre la
        gráfica o debajo de ella. Su objetivo es ayudarte a ver cosas que a simple vista no son tan claras, como la
        fuerza de una tendencia o si un activo está "muy comprado" o "muy vendido".
      </p>
      <p class="text-gray-700 leading-relaxed">
        Los indicadores no predicen el futuro. Son ayudas. Usar muchos a la vez puede confundir más que ayudar, así que
        lo recomendable es empezar con pocos y entenderlos bien.
      </p>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Indicadores más usados</h2>
      <ul class="list-disc list-inside text-gray-700 space-y-2">
        <li><strong>Medias móviles:</strong> suavizan el precio para mostrar la tendencia con más claridad. Las más usadas son las de 50 y 200 periodos.</li>
        <li><strong>RSI (Índice de Fuerza Relativa):</strong> mide si un activo está sobrecomprado (posible caída) o sobrevendido (posible subida). Va de 0 a 100.</li>
        <li><strong>MACD:</strong> ayuda a detectar cambios en la fuerza y dirección de la tendencia mediante el cruce de dos líneas.</li>
        <li><strong>Volumen:</strong> muestra cuántas operaciones hubo. Un movimiento con mucho volumen suele tener más fuerza.</li>
        <li><strong>Bandas de Bollinger:</strong> marcan un rango alrededor del precio; ayudan a ver volatilidad y posibles extremos.</li>
      </ul>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-[#2D2B6B] mt-8 mb-3">Tipos de indicadores</h2>
      <div class="grid md:grid-cols-2 gap-4">
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-1">De tendencia</h3>
          <p class="text-sm text-gray-600">Ayudan a ver la dirección del mercado (por ejemplo, las medias móviles y el MACD).</p>
        </div>
        <div class="bg-white border border-[#E0E0F0] rounded-xl p-4">
          <h3 class="font-semibold text-[#2D2B6B] mb-1">De momento (osciladores)</h3>
          <p class="text-sm text-gray-600">Miden la fuerza y la velocidad del movimiento (por ejemplo, el RSI).</p>
        </div>
      </div>
    </section>

    <section class="mb-8">
      <div class="bg-[#F0F0FA] border border-[#E0E0F0] rounded-xl p-4">
        <p class="text-sm text-gray-700">
          Recuerda: los indicadores funcionan mejor en conjunto y confirmando lo que ya ves en la tendencia y las
          velas. Ninguno por sí solo te dará señales perfectas.
        </p>
      </div>
    </section>
  </article>
</template>
