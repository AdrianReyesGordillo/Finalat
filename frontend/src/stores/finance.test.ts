import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFinanceStore } from './finance'

// Mock the useApi composable
vi.mock('../composables/useApi', () => ({
  apiGet: vi.fn(),
}))

import { apiGet } from '../composables/useApi'

const mockApiGet = vi.mocked(apiGet)

describe('useFinanceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has empty arrays and null patrimonio', () => {
      const store = useFinanceStore()
      expect(store.savings).toEqual([])
      expect(store.credits).toEqual([])
      expect(store.debts).toEqual([])
      expect(store.afore).toEqual([])
      expect(store.gbmPositions).toEqual([])
      expect(store.patrimonio).toBeNull()
    })

    it('has all module states not loading and no errors', () => {
      const store = useFinanceStore()
      expect(store.savingsState.loading).toBe(false)
      expect(store.savingsState.error).toBeNull()
      expect(store.creditsState.loading).toBe(false)
      expect(store.debtsState.loading).toBe(false)
      expect(store.aforeState.loading).toBe(false)
      expect(store.gbmState.loading).toBe(false)
      expect(store.patrimonioState.loading).toBe(false)
    })

    it('computes zero aggregates when data is empty', () => {
      const store = useFinanceStore()
      expect(store.totalSavings).toBe(0)
      expect(store.totalCredit).toBe(0)
      expect(store.totalDebt).toBe(0)
      expect(store.totalMonthlyPayment).toBe(0)
      expect(store.totalAfore).toBe(0)
      expect(store.totalGbm).toBe(0)
      expect(store.netWorth).toBe(0)
    })
  })

  describe('aggregate computations', () => {
    it('calculates totalSavings from savings entries', () => {
      const store = useFinanceStore()
      store.savings = [
        { id: '1', amount: 1000, account_name: 'Nu', created_at: '', updated_at: '' },
        { id: '2', amount: 2500, account_name: 'CETES', created_at: '', updated_at: '' },
      ]
      expect(store.totalSavings).toBe(3500)
    })

    it('calculates totalCredit from credit balances', () => {
      const store = useFinanceStore()
      store.credits = [
        { id: '1', balance: 5000, limit: 20000, minimum_payment: 500, card_name: 'Visa', utilization: 25, created_at: '', updated_at: '' },
        { id: '2', balance: 3000, limit: 10000, minimum_payment: 300, card_name: 'MC', utilization: 30, created_at: '', updated_at: '' },
      ]
      expect(store.totalCredit).toBe(8000)
    })

    it('calculates totalDebt and totalMonthlyPayment', () => {
      const store = useFinanceStore()
      store.debts = [
        { id: '1', creditor_name: 'Bank', total_amount: 50000, monthly_payment: 2000, interest_rate: 12, start_date: '', remaining_balance: 50000, estimated_payoff_date: '', total_interest: 0, created_at: '', updated_at: '' },
        { id: '2', creditor_name: 'Friend', total_amount: 10000, monthly_payment: 1000, interest_rate: 0, start_date: '', remaining_balance: 10000, estimated_payoff_date: '', total_interest: 0, created_at: '', updated_at: '' },
      ]
      expect(store.totalDebt).toBe(60000)
      expect(store.totalMonthlyPayment).toBe(3000)
    })

    it('calculates totalAfore from afore balances', () => {
      const store = useFinanceStore()
      store.afore = [
        { id: '1', provider_name: 'Profuturo', balance: 100000, last_update_date: '', created_at: '', updated_at: '' },
      ]
      expect(store.totalAfore).toBe(100000)
    })

    it('calculates totalGbm from position market values', () => {
      const store = useFinanceStore()
      store.gbmPositions = [
        { id: '1', ticker: 'AAPL', shares: 10, avg_cost: 150, market_value: 1700, gain_loss_pct: 13.3, created_at: '', updated_at: '' },
        { id: '2', ticker: 'MSFT', shares: 5, avg_cost: 300, market_value: 1800, gain_loss_pct: 20, created_at: '', updated_at: '' },
      ]
      expect(store.totalGbm).toBe(3500)
    })

    it('calculates netWorth as assets minus liabilities (fallback)', () => {
      const store = useFinanceStore()
      store.savings = [{ id: '1', amount: 10000, account_name: 'Nu', created_at: '', updated_at: '' }]
      store.afore = [{ id: '1', provider_name: 'P', balance: 50000, last_update_date: '', created_at: '', updated_at: '' }]
      store.gbmPositions = [{ id: '1', ticker: 'X', shares: 1, avg_cost: 100, market_value: 5000, gain_loss_pct: 0, created_at: '', updated_at: '' }]
      store.debts = [{ id: '1', creditor_name: 'B', total_amount: 20000, monthly_payment: 1000, interest_rate: 10, start_date: '', remaining_balance: 20000, estimated_payoff_date: '', total_interest: 0, created_at: '', updated_at: '' }]
      store.credits = [{ id: '1', balance: 5000, limit: 20000, minimum_payment: 500, card_name: 'V', utilization: 25, created_at: '', updated_at: '' }]

      // assets: 10000 + 50000 + 5000 = 65000
      // liabilities: 20000 + 5000 = 25000
      expect(store.netWorth).toBe(40000)
    })

    it('uses patrimonio.total when patrimonio is available', () => {
      const store = useFinanceStore()
      store.patrimonio = {
        total: 123456,
        assets: { ahorro: 50000, afore: 60000, gbm: 30000, total: 140000 },
        liabilities: { deudas: 10000, creditos: 6544, total: 16544 },
      }
      expect(store.netWorth).toBe(123456)
    })
  })

  describe('fetchSavings', () => {
    it('fetches savings and updates state on success', async () => {
      const store = useFinanceStore()
      const mockData = [
        { id: '1', amount: 5000, account_name: 'Nu', created_at: '', updated_at: '' },
      ]
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchSavings()

      expect(mockApiGet).toHaveBeenCalledWith('/api/ahorro')
      expect(store.savings).toEqual(mockData)
      expect(store.savingsState.loading).toBe(false)
      expect(store.savingsState.error).toBeNull()
      expect(store.savingsState.lastFetched).toBeInstanceOf(Date)
    })

    it('sets error on failure', async () => {
      const store = useFinanceStore()
      mockApiGet.mockRejectedValueOnce(new Error('Network error'))

      await store.fetchSavings()

      expect(store.savings).toEqual([])
      expect(store.savingsState.loading).toBe(false)
      expect(store.savingsState.error).toBe('Network error')
    })
  })

  describe('fetchCredits', () => {
    it('fetches credits successfully', async () => {
      const store = useFinanceStore()
      const mockData = [
        { id: '1', balance: 3000, limit: 10000, minimum_payment: 300, card_name: 'MC', utilization: 30, created_at: '', updated_at: '' },
      ]
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchCredits()

      expect(mockApiGet).toHaveBeenCalledWith('/api/creditos')
      expect(store.credits).toEqual(mockData)
      expect(store.creditsState.error).toBeNull()
    })
  })

  describe('fetchDebts', () => {
    it('fetches debts successfully', async () => {
      const store = useFinanceStore()
      const mockData = [
        { id: '1', creditor_name: 'Bank', total_amount: 50000, monthly_payment: 2000, interest_rate: 12, start_date: '', remaining_balance: 50000, estimated_payoff_date: '', total_interest: 0, created_at: '', updated_at: '' },
      ]
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchDebts()

      expect(mockApiGet).toHaveBeenCalledWith('/api/deudas')
      expect(store.debts).toEqual(mockData)
    })
  })

  describe('fetchAfore', () => {
    it('fetches afore successfully', async () => {
      const store = useFinanceStore()
      const mockData = [
        { id: '1', provider_name: 'Profuturo', balance: 100000, last_update_date: '', created_at: '', updated_at: '' },
      ]
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchAfore()

      expect(mockApiGet).toHaveBeenCalledWith('/api/afore')
      expect(store.afore).toEqual(mockData)
    })
  })

  describe('fetchGbm', () => {
    it('fetches GBM positions successfully', async () => {
      const store = useFinanceStore()
      const mockData = [
        { id: '1', ticker: 'AAPL', shares: 10, avg_cost: 150, market_value: 1700, gain_loss_pct: 13.3, created_at: '', updated_at: '' },
      ]
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchGbm()

      expect(mockApiGet).toHaveBeenCalledWith('/api/gbm')
      expect(store.gbmPositions).toEqual(mockData)
    })
  })

  describe('fetchPatrimonio', () => {
    it('fetches patrimonio successfully', async () => {
      const store = useFinanceStore()
      const mockData = {
        total: 100000,
        assets: { ahorro: 60000, afore: 30000, gbm: 30000, total: 120000 },
        liabilities: { deudas: 15000, creditos: 5000, total: 20000 },
      }
      mockApiGet.mockResolvedValueOnce(mockData)

      await store.fetchPatrimonio()

      expect(mockApiGet).toHaveBeenCalledWith('/api/patrimonio')
      expect(store.patrimonio).toEqual(mockData)
    })
  })

  describe('fetchAll', () => {
    it('fetches all modules in parallel', async () => {
      const store = useFinanceStore()
      mockApiGet.mockResolvedValue([])

      await store.fetchAll()

      expect(mockApiGet).toHaveBeenCalledWith('/api/ahorro')
      expect(mockApiGet).toHaveBeenCalledWith('/api/creditos')
      expect(mockApiGet).toHaveBeenCalledWith('/api/deudas')
      expect(mockApiGet).toHaveBeenCalledWith('/api/afore')
      expect(mockApiGet).toHaveBeenCalledWith('/api/gbm')
      expect(mockApiGet).toHaveBeenCalledWith('/api/patrimonio')
    })

    it('does not fail entirely when one module errors', async () => {
      const store = useFinanceStore()
      mockApiGet.mockImplementation((url: string) => {
        if (url === '/api/ahorro') return Promise.reject(new Error('fail'))
        return Promise.resolve([])
      })

      await store.fetchAll()

      expect(store.savingsState.error).toBe('fail')
      expect(store.creditsState.error).toBeNull()
      expect(store.debtsState.error).toBeNull()
    })
  })

  describe('refreshAll', () => {
    it('is an alias for fetchAll', async () => {
      const store = useFinanceStore()
      mockApiGet.mockResolvedValue([])

      await store.refreshAll()

      expect(mockApiGet).toHaveBeenCalledTimes(6)
    })
  })

  describe('invalidateModule', () => {
    it('clears and re-fetches a specific module', async () => {
      const store = useFinanceStore()
      store.savings = [{ id: '1', amount: 1000, account_name: 'X', created_at: '', updated_at: '' }]

      const newData = [{ id: '2', amount: 2000, account_name: 'Y', created_at: '', updated_at: '' }]
      mockApiGet.mockResolvedValueOnce(newData)

      await store.invalidateModule('savings')

      expect(store.savings).toEqual(newData)
    })

    it('clears patrimonio and re-fetches', async () => {
      const store = useFinanceStore()
      store.patrimonio = { total: 50000, assets: { ahorro: 50000, afore: 0, gbm: 0, total: 50000 }, liabilities: { deudas: 0, creditos: 0, total: 0 } }

      const newData = { total: 70000, assets: { ahorro: 70000, afore: 0, gbm: 0, total: 70000 }, liabilities: { deudas: 0, creditos: 0, total: 0 } }
      mockApiGet.mockResolvedValueOnce(newData)

      await store.invalidateModule('patrimonio')

      expect(store.patrimonio).toEqual(newData)
    })
  })

  describe('$reset', () => {
    it('resets all data to initial state', () => {
      const store = useFinanceStore()
      store.savings = [{ id: '1', amount: 1000, account_name: 'X', created_at: '', updated_at: '' }]
      store.credits = [{ id: '1', balance: 500, limit: 5000, minimum_payment: 50, card_name: 'V', utilization: 10, created_at: '', updated_at: '' }]
      store.savingsState.lastFetched = new Date()

      store.$reset()

      expect(store.savings).toEqual([])
      expect(store.credits).toEqual([])
      expect(store.debts).toEqual([])
      expect(store.afore).toEqual([])
      expect(store.gbmPositions).toEqual([])
      expect(store.patrimonio).toBeNull()
      expect(store.savingsState.loading).toBe(false)
      expect(store.savingsState.error).toBeNull()
      expect(store.savingsState.lastFetched).toBeNull()
    })
  })

  describe('loading computed', () => {
    it('returns true when any module is loading', () => {
      const store = useFinanceStore()
      expect(store.loading).toBe(false)

      store.debtsState.loading = true
      expect(store.loading).toBe(true)
    })
  })
})
