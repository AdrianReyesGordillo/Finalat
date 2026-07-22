/** Standard API response envelope */
export interface APIResponse<T> {
  success: boolean
  data: T | null
  error: {
    code: string
    message: string
    fields?: Record<string, string>
  } | null
}

/** Savings account entry */
export interface Ahorro {
  id: string
  amount: number
  account_name: string
  created_at: string
  updated_at: string
}

/** Credit card entry */
export interface Creditos {
  id: string
  balance: number
  limit: number
  minimum_payment: number
  card_name: string
  utilization: number | string
  created_at: string
  updated_at: string
}

/** Expense or income entry */
export interface GastosIngresos {
  id: string
  type: 'income' | 'expense'
  amount: number
  description: string
  category_id: string
  category_name?: string
  entry_date: string
  created_at: string
  updated_at: string
}

/** Debt entry */
export interface Deudas {
  id: string
  creditor_name: string
  total_amount: number
  monthly_payment: number
  interest_rate: number
  start_date: string
  remaining_balance: number
  estimated_payoff_date: string
  total_interest: number
  created_at: string
  updated_at: string
}

/** Recurring contribution schedule */
export interface Aportaciones {
  id: string
  amount: number
  frequency: 'weekly' | 'biweekly' | 'monthly'
  target_name: string
  start_date: string
  annual_projection: number
  created_at: string
  updated_at: string
}

/** Afore (pension fund) entry */
export interface Afore {
  id: string
  provider_name: string
  balance: number
  last_update_date: string
  created_at: string
  updated_at: string
}

/** GBM portfolio position */
export interface GbmPosition {
  id: string
  ticker: string
  shares: number
  avg_cost: number
  market_value: number
  gain_loss_pct: number
  created_at: string
  updated_at: string
}

/** Net worth breakdown */
export interface PatrimonioNeto {
  total: number
  assets: {
    ahorro: number
    afore: number
    gbm: number
    total: number
  }
  liabilities: {
    deudas: number
    creditos: number
    total: number
  }
  meta?: {
    failed_count: number
  }
}

/** Category for expenses/income */
export interface Category {
  id: string
  name: string
  is_system: boolean
}

/** Tiered rate structure */
export interface TieredRate {
  min_amount: number
  max_amount: number
  rate: number
}

/** Financial instrument */
export interface Instrument {
  id: string
  name: string
  annual_rate: number
  min_investment: number
  max_investment: number
  term: string
  risk_level: string
  liquidity_tier: string
  tiered_rates: TieredRate[] | null
  last_fetch_status: 'success' | 'error' | 'stale'
}


/** Update tracker module status */
export interface ModuleUpdateStatus {
  module_name: string
  last_updated_at: string | null
  stale: boolean
}
