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
