export interface Instrument {
  id: number
  name: string
  institution: string
  instrument_type: string
  annual_rate: number
  min_amount: number
  max_amount_for_rate: number | null
  secondary_rate: number | null
  term_days: number | null
  requires_purchase: boolean
  purchase_min_amount: number | null
  conditions: string | null
  referral_link: string | null
  signup_link: string | null
  logo_url: string | null
  is_active: boolean
  last_updated: string
  created_at: string
}

export interface InvestmentRequest {
  amount: number
  term_days: number
  risk_tolerance: 'low' | 'medium' | 'high'
}

export interface AllocationItem {
  instrument_name: string
  institution: string
  allocated_amount: number
  annual_rate: number
  estimated_return: number
  term_days: number | null
  conditions: string | null
  referral_link: string | null
  signup_link: string | null
  logo_url: string | null
}

export interface InvestmentResponse {
  total_amount: number
  term_days: number
  allocations: AllocationItem[]
  total_estimated_return: number
  effective_annual_rate: number
  notes: string[]
}

// --- Financial module types ---

export interface Ahorro {
  id: string
  amount: number
  account_name: string
  created_at: string
  updated_at: string
}

export interface Creditos {
  id: string
  balance: number
  credit_name: string
  credit_limit: number
  created_at: string
  updated_at: string
}

export interface Deudas {
  id: string
  total_amount: number
  monthly_payment: number
  debt_name: string
  interest_rate: number
  created_at: string
  updated_at: string
}

export interface Afore {
  id: string
  balance: number
  afore_name: string
  created_at: string
  updated_at: string
}

export interface GbmPosition {
  id: string
  ticker: string
  shares: number
  avg_cost: number
  market_value: number
  created_at: string
  updated_at: string
}

export interface PatrimonioNeto {
  total: number
  assets: number
  liabilities: number
  calculated_at: string
}

export interface ModuleUpdateStatus {
  module_name: string
  last_updated_at: string | null
  stale: boolean
}
