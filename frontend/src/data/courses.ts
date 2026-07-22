/**
 * Definición de cursos del módulo de Aprendizaje.
 * Cada curso tiene su propia estructura de secciones, lecciones y tests.
 * El usuario puede tomar varios cursos a la vez.
 */

export interface CourseLesson {
  id: string
  title: string
  route: string
  section: string
}

export interface CourseDefinition {
  id: string
  title: string
  description: string
  icon: string
  color: string
  lessons: CourseLesson[]
  /** IDs de sección que tienen test al final */
  testSections: string[]
}

export const COURSES: CourseDefinition[] = [
  {
    id: 'finanzas-personales',
    title: 'Introducción a las Finanzas Personales',
    description: 'Aprende los conceptos esenciales para manejar tu dinero: presupuestos, ahorro, deuda y cómo construir una base financiera sólida.',
    icon: 'pi-wallet',
    color: '#2AAFAA',
    testSections: ['fundamentos', 'conceptos-clave'],
    lessons: [
      { id: 'introduccion', title: 'Introducción', route: '/aprende/finanzas-personales/introduccion', section: 'Fundamentos' },
      { id: 'conceptos', title: 'Conceptos generales', route: '/aprende/finanzas-personales/conceptos', section: 'Fundamentos' },
      { id: 'fondo-emergencia', title: 'Fondo de emergencia', route: '/aprende/finanzas-personales/fondo-emergencia', section: 'Conceptos clave' },
      { id: 'diversificacion', title: 'Diversificación', route: '/aprende/finanzas-personales/diversificacion', section: 'Conceptos clave' },
      { id: 'tarjeta-credito', title: '¿Cómo funciona una TDC?', route: '/aprende/finanzas-personales/tarjeta-credito', section: 'Conceptos clave' },
    ],
  },
  {
    id: 'renta-fija-variable',
    title: 'Renta Fija y Renta Variable',
    description: 'Entiende las diferencias entre instrumentos de renta fija y variable, desde CETES hasta acciones en la bolsa.',
    icon: 'pi-chart-bar',
    color: '#6366f1',
    testSections: ['teoria', 'instrumentos'],
    lessons: [
      { id: 'renta-fija', title: 'Renta fija', route: '/aprende/renta-fija-variable/renta-fija', section: 'Teoría' },
      { id: 'renta-variable', title: 'Renta variable', route: '/aprende/renta-fija-variable/renta-variable', section: 'Teoría' },
      { id: 'cetes', title: 'CETES', route: '/aprende/renta-fija-variable/cetes', section: 'Instrumentos' },
      { id: 'cuentas-ahorro', title: 'Cuentas de ahorro', route: '/aprende/renta-fija-variable/cuentas-ahorro', section: 'Instrumentos' },
      { id: 'acciones', title: 'Acciones', route: '/aprende/renta-fija-variable/acciones', section: 'Instrumentos' },
    ],
  },
  {
    id: 'fundamentos-trading',
    title: 'Fundamentos de Trading',
    description: 'Conoce los principios del trading: análisis técnico, patrones, indicadores y gestión de riesgo para operar en los mercados.',
    icon: 'pi-chart-line',
    color: '#f59e0b',
    testSections: ['introduccion-trading', 'analisis-tecnico'],
    lessons: [
      { id: 'trading', title: 'Introducción al Trading', route: '/aprende/fundamentos-trading/trading', section: 'Introducción' },
      { id: 'tendencias', title: 'Tendencias', route: '/aprende/fundamentos-trading/tendencias', section: 'Introducción' },
      { id: 'velas', title: 'Velas japonesas', route: '/aprende/fundamentos-trading/velas', section: 'Análisis técnico' },
      { id: 'patrones', title: 'Patrones', route: '/aprende/fundamentos-trading/patrones', section: 'Análisis técnico' },
      { id: 'indicadores', title: 'Indicadores', route: '/aprende/fundamentos-trading/indicadores', section: 'Análisis técnico' },
      { id: 'gestion-riesgo', title: 'Gestión de riesgo', route: '/aprende/fundamentos-trading/gestion-riesgo', section: 'Análisis técnico' },
    ],
  },
]

/**
 * Obtiene un curso por su ID.
 */
export function getCourseById(courseId: string): CourseDefinition | undefined {
  return COURSES.find(c => c.id === courseId)
}

/**
 * Obtiene el section ID normalizado para un nombre de sección.
 */
export function getSectionId(sectionName: string): string {
  return sectionName
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}
