/**
 * Preguntas de evaluación por sección del curso de aprendizaje.
 * Cada sección tiene 10 preguntas de opción múltiple.
 * Se necesita un puntaje mínimo de 7/10 para avanzar.
 */

export interface QuizQuestion {
  question: string
  options: string[]
  correctIndex: number
}

export interface SectionQuiz {
  sectionId: string
  sectionName: string
  questions: QuizQuestion[]
}

export const SECTION_QUIZZES: SectionQuiz[] = [
  {
    sectionId: 'como-empiezo',
    sectionName: '¿Cómo empiezo?',
    questions: [
      {
        question: '¿Cuál es el primer paso para mejorar tus finanzas personales?',
        options: ['Invertir en acciones', 'Conocer tu situación financiera actual', 'Pedir un préstamo', 'Abrir una cuenta de ahorro'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es la renta fija?',
        options: ['Inversión donde el rendimiento es variable', 'Inversión donde conoces el rendimiento de antemano', 'Un tipo de impuesto', 'Un gasto mensual fijo'],
        correctIndex: 1,
      },
      {
        question: '¿Cuál es una ventaja principal de la renta fija?',
        options: ['Altos rendimientos garantizados', 'Previsibilidad del rendimiento', 'No requiere ningún capital', 'Es gratis'],
        correctIndex: 1,
      },
      {
        question: '¿Qué caracteriza a la renta variable?',
        options: ['El rendimiento está garantizado', 'El rendimiento puede subir o bajar', 'Solo la usan bancos', 'No tiene riesgo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué ejemplo es de renta variable?',
        options: ['CETES', 'Cuentas de ahorro', 'Acciones en la bolsa', 'Pagarés bancarios'],
        correctIndex: 2,
      },
      {
        question: '¿Qué ejemplo es de renta fija?',
        options: ['Criptomonedas', 'Acciones', 'CETES', 'Fondos de renta variable'],
        correctIndex: 2,
      },
      {
        question: '¿Por qué es importante hacer un presupuesto?',
        options: ['Para gastar más', 'Para saber cuánto ganas y gastas', 'No es importante', 'Solo para empresas'],
        correctIndex: 1,
      },
      {
        question: '¿Qué significa diversificar?',
        options: ['Poner todo tu dinero en un solo lugar', 'Repartir tu dinero en diferentes inversiones', 'Gastar en diversión', 'Ahorrar solo en el banco'],
        correctIndex: 1,
      },
      {
        question: '¿Cuál es un riesgo de la renta variable?',
        options: ['Que no genere ningún interés', 'Que el valor de tu inversión baje', 'Que el banco cierre', 'Ninguno, no tiene riesgo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué deberías hacer antes de invertir?',
        options: ['Pedir un crédito', 'Tener un fondo de emergencia', 'Comprar un auto', 'Nada, solo invertir'],
        correctIndex: 1,
      },
    ],
  },
  {
    sectionId: 'instrumentos',
    sectionName: 'Instrumentos',
    questions: [
      {
        question: '¿Qué son los CETES?',
        options: ['Acciones de empresas', 'Certificados de la Tesorería del gobierno mexicano', 'Cuentas de ahorro', 'Tarjetas de crédito'],
        correctIndex: 1,
      },
      {
        question: '¿Cuál es el plazo mínimo típico para invertir en CETES?',
        options: ['1 día', '28 días', '1 año', '5 años'],
        correctIndex: 1,
      },
      {
        question: '¿Quién respalda los CETES?',
        options: ['Bancos privados', 'El gobierno federal de México', 'Empresas privadas', 'Inversionistas extranjeros'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es una cuenta de ahorro?',
        options: ['Un producto para invertir en bolsa', 'Un producto bancario que genera intereses sobre tu dinero', 'Un tipo de crédito', 'Una tarjeta de débito'],
        correctIndex: 1,
      },
      {
        question: '¿Qué ventaja tiene una cuenta de ahorro sobre guardar dinero en casa?',
        options: ['Es más difícil de acceder', 'Genera rendimientos y está protegida', 'No tiene ninguna ventaja', 'Cobra comisiones altas'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es el GAT en una cuenta de ahorro?',
        options: ['Un impuesto', 'La Ganancia Anual Total que indica el rendimiento real', 'El monto mínimo de apertura', 'Una comisión'],
        correctIndex: 1,
      },
      {
        question: '¿Qué plataforma en México permite comprar CETES directamente?',
        options: ['Netflix', 'cetesdirecto.com', 'Amazon', 'MercadoLibre'],
        correctIndex: 1,
      },
      {
        question: '¿Cuál es un riesgo de las cuentas de ahorro tradicionales?',
        options: ['Perder todo tu dinero', 'Que el rendimiento sea menor a la inflación', 'Que el banco quiebre sin protección', 'No tienen ningún riesgo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué institución protege tu dinero en bancos en México?',
        options: ['SAT', 'IPAB', 'IMSS', 'CFE'],
        correctIndex: 1,
      },
      {
        question: '¿Hasta cuánto protege el IPAB por persona por banco?',
        options: ['$100,000 MXN', '400,000 UDIS (aprox. $3 millones MXN)', '$1 millón MXN', 'No tiene límite'],
        correctIndex: 1,
      },
    ],
  },
  {
    sectionId: 'trading',
    sectionName: 'Trading',
    questions: [
      {
        question: '¿Qué es el trading?',
        options: ['Ahorrar dinero en el banco', 'Comprar y vender activos financieros buscando ganancias', 'Un tipo de crédito', 'Una forma de ahorro a largo plazo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es una tendencia alcista?',
        options: ['Cuando el precio baja constantemente', 'Cuando el precio sube formando máximos y mínimos más altos', 'Cuando el precio no se mueve', 'Cuando hay mucho volumen'],
        correctIndex: 1,
      },
      {
        question: '¿Qué representan las velas japonesas?',
        options: ['El volumen de operaciones', 'El precio de apertura, cierre, máximo y mínimo en un período', 'Solo el precio de cierre', 'Las noticias del mercado'],
        correctIndex: 1,
      },
      {
        question: '¿Qué indica una vela roja/bajista?',
        options: ['El precio subió', 'El precio cerró más bajo que donde abrió', 'No hay movimiento', 'Es una señal de compra'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es un patrón de doble techo?',
        options: ['Una señal de continuación alcista', 'Una señal de posible cambio de tendencia a la baja', 'Un indicador de volumen', 'Un tipo de media móvil'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es el RSI?',
        options: ['Un tipo de orden', 'Un indicador que mide si un activo está sobrecomprado o sobrevendido', 'Un patrón de velas', 'Una comisión del broker'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es un stop-loss?',
        options: ['Una orden para comprar más', 'Una orden que cierra tu posición si el precio baja a cierto nivel', 'Un indicador técnico', 'Un tipo de gráfico'],
        correctIndex: 1,
      },
      {
        question: '¿Cuánto de tu capital se recomienda arriesgar por operación?',
        options: ['50%', '1-2%', '25%', 'Todo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es la gestión de riesgo en trading?',
        options: ['Invertir todo en una sola acción', 'Controlar cuánto puedes perder para proteger tu capital', 'No usar stop-loss', 'Operar con apalancamiento máximo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es una media móvil?',
        options: ['Un patrón de velas', 'Un indicador que suaviza el precio promediando valores pasados', 'Un tipo de orden', 'El volumen promedio'],
        correctIndex: 1,
      },
    ],
  },
  {
    sectionId: 'conceptos',
    sectionName: 'Conceptos',
    questions: [
      {
        question: '¿Qué es un fondo de emergencia?',
        options: ['Dinero para invertir en bolsa', 'Dinero reservado para gastos inesperados', 'Un tipo de seguro', 'Una tarjeta de crédito'],
        correctIndex: 1,
      },
      {
        question: '¿Cuántos meses de gastos se recomienda tener en un fondo de emergencia?',
        options: ['1 mes', '3 a 6 meses', '12 meses', '2 semanas'],
        correctIndex: 1,
      },
      {
        question: '¿Por qué es importante la diversificación?',
        options: ['Para gastar más', 'Para reducir el riesgo de perder todo', 'No es importante', 'Para pagar menos impuestos'],
        correctIndex: 1,
      },
      {
        question: '¿Qué significa diversificar tus inversiones?',
        options: ['Invertir todo en acciones', 'Repartir tu dinero en diferentes tipos de activos', 'Ahorrar solo en el banco', 'Comprar solo CETES'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es el interés compuesto?',
        options: ['Un impuesto sobre inversiones', 'Ganar intereses sobre los intereses previamente generados', 'Una comisión bancaria', 'Un tipo de préstamo'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es la tasa de interés de una tarjeta de crédito?',
        options: ['Lo que te pagan por usarla', 'El costo que pagas si no liquidas tu saldo completo', 'Un beneficio gratuito', 'El límite de crédito'],
        correctIndex: 1,
      },
      {
        question: '¿Qué pasa si solo pagas el mínimo de tu tarjeta de crédito?',
        options: ['Pagas menos intereses', 'Acumulas más deuda por intereses', 'No pasa nada', 'Te bajan la tasa'],
        correctIndex: 1,
      },
      {
        question: '¿Cuál es la mejor práctica con una tarjeta de crédito?',
        options: ['Usarla al máximo siempre', 'Pagar el total antes de la fecha de corte', 'Solo pagar el mínimo', 'No usarla nunca'],
        correctIndex: 1,
      },
      {
        question: '¿Dónde se recomienda guardar el fondo de emergencia?',
        options: ['En acciones volátiles', 'En un lugar seguro y líquido como una cuenta de ahorro', 'Debajo del colchón', 'En criptomonedas'],
        correctIndex: 1,
      },
      {
        question: '¿Qué es la inflación?',
        options: ['Cuando tu dinero vale más', 'El aumento general de precios que reduce el poder adquisitivo', 'Un tipo de inversión', 'Una tasa bancaria'],
        correctIndex: 1,
      },
    ],
  },
]

/**
 * Obtiene el quiz correspondiente a una sección por su ID.
 */
export function getQuizBySection(sectionId: string): SectionQuiz | undefined {
  return SECTION_QUIZZES.find(q => q.sectionId === sectionId)
}
