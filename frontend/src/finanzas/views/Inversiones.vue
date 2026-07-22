<template>
  <div class="inversiones">
    <h1 class="page-title">Inversiones</h1>

    <!-- Resumen Total -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon portfolio"><i class="pi pi-briefcase"></i></div>
        <div class="stat-info">
          <span class="stat-label">Portafolio Total</span>
          <span class="stat-value">${{ formatMoney(totalPortfolio) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon savings"><i class="pi pi-wallet"></i></div>
        <div class="stat-info">
          <span class="stat-label">Liquidez</span>
          <span class="stat-value">${{ formatMoney(liquidez) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon savings"><i class="pi pi-wallet"></i></div>
        <div class="stat-info">
          <span class="stat-label">Ingreso Diario</span>
          <span class="stat-value">+${{ formatMoney(dailyIncomeRevolutNu) }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon market"><i class="pi pi-chart-line"></i></div>
        <div class="stat-info">
          <span class="stat-label">Ingreso Congelado</span>
          <span class="stat-value">${{ formatMoney(frozenIncome) }}</span>
        </div>
      </div>
    </div>

    <!-- Tabs de secciones -->
    <div v-if="prefsStore.loaded" class="section-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <i :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- SECCIÓN: CUENTAS DE AHORRO -->
    <div v-if="activeTab === 'savings'" class="section-content">

      <!-- Indicador de última actualización -->
      <div v-if="updateStatus.lastUpdate" class="update-ok">
        <i class="pi pi-check-circle"></i>
        <span>Datos actualizados el {{ formatDate(updateStatus.lastUpdate) }}</span>
      </div>

      <!-- Modal de edición individual de cuenta de ahorro -->
      <div v-if="showSingleAhorroModal" class="upload-overlay" @click.self="showSingleAhorroModal = false">
        <div class="upload-modal">
          <div class="upload-modal-header">
            <h3><i class="pi pi-wallet"></i> Editar {{ singleAhorroAccount?.name }}</h3>
            <button class="btn-close" @click="showSingleAhorroModal = false"><i class="pi pi-times"></i></button>
          </div>

          <div class="upload-modal-body">
            <p class="upload-hint">Ingresa el saldo actual de esta cuenta.</p>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" :style="{ backgroundColor: singleAhorroAccount?.color }"></span>
                Saldo Actual
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input
                  type="text"
                  inputmode="decimal"
                  class="balance-input"
                  :placeholder="formatMoney(singleAhorroAccount?.balance || 0)"
                  v-model="singleAhorroBalance"
                />
              </div>
            </div>

            <div v-if="singleAhorroError" class="upload-error">
              <i class="pi pi-exclamation-triangle"></i> {{ singleAhorroError }}
            </div>
          </div>

          <div class="upload-modal-footer">
            <button class="btn-cancel" @click="showSingleAhorroModal = false">Cancelar</button>
            <button
              class="btn-upload-confirm"
              :disabled="singleAhorroSaving || singleAhorroBalance === null || singleAhorroBalance === undefined || singleAhorroBalance === ''"
              @click="submitSingleAhorroBalance"
            >
              <i :class="singleAhorroSaving ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
              {{ singleAhorroSaving ? 'Guardando...' : 'Guardar saldo' }}
            </button>
          </div>
        </div>
      </div>

      <div class="savings-cards">
        <div v-for="account in savingsAccounts" :key="account.name" class="savings-card" :style="{ borderTopColor: account.color }">
          <div class="savings-header">
            <div class="savings-brand" :style="{ backgroundColor: account.color + '20', color: account.color }">
              <i class="pi pi-wallet"></i>
            </div>
            <div>
              <h3>{{ account.name }}</h3>
              <span class="savings-subtitle">{{ account.description }}</span>
            </div>
            <button class="btn-edit-card" :style="{ color: account.color }" @click="openSingleAhorroModal(account)">
              <i class="pi pi-pencil"></i>
            </button>
          </div>

          <div class="savings-balance">
            <span class="balance-label">Saldo Actual</span>
            <span class="balance-value">${{ formatMoney(account.balance) }}</span>
          </div>

          <div class="savings-rate">
            <span class="rate-badge" :style="{ backgroundColor: account.color + '20', color: account.color }">
              {{ account.annualRate }}% anual
            </span>
            <span class="daily-gain">+${{ formatMoney(account.dailyGain) }}/día</span>
          </div>

          <!-- Selector de periodo -->
          <div class="period-selector">
            <button
              v-for="period in periods"
              :key="period.key"
              class="period-btn"
              :class="{ active: account.selectedPeriod === period.key }"
              @click="account.selectedPeriod = period.key"
            >
              {{ period.label }}
            </button>
          </div>

          <!-- Gráfica de interés compuesto -->
          <div class="chart-container">
            <Line :data="getCompoundChart(account)" :options="lineOptions" />
          </div>

          <div class="projection-summary">
            <div class="proj-item">
              <span class="proj-label">Proyección</span>
              <span class="proj-value income">${{ formatMoney(getProjection(account)) }}</span>
            </div>
            <div class="proj-item">
              <span class="proj-label">Ganancia</span>
              <span class="proj-value income">+${{ formatMoney(getProjection(account) - account.balance) }}</span>
            </div>
          </div>
        </div>
      </div>

      <p class="savings-disclaimer">
        <i class="pi pi-info-circle"></i>
        La proyección de interés diario y en todas las temporalidades puede variar según la cantidad de impuestos que te sean retenidos. Únicamente es una proyección lo más exacta posible.
      </p>
    </div>

    <!-- SECCIÓN: PRÉSTAMOS -->
    <div v-if="activeTab === 'loans'" class="section-content">

      <div class="loans-header-info">
        <div class="loans-header-row">
          <div></div>
          <button class="btn-new-loan" @click="showNuevoPrestamoModal = true">
            <i class="pi pi-plus"></i> Nuevo Préstamo
          </button>
        </div>
      </div>

      <!-- Modal Nuevo Préstamo -->
      <div v-if="showNuevoPrestamoModal" class="upload-overlay" @click.self="showNuevoPrestamoModal = false">
        <div class="upload-modal">
          <div class="upload-modal-header">
            <h3><i class="pi pi-plus-circle"></i> Nuevo Préstamo</h3>
            <button class="btn-close" @click="showNuevoPrestamoModal = false"><i class="pi pi-times"></i></button>
          </div>

          <div class="upload-modal-body">
            <p class="upload-hint">Registra un nuevo préstamo. El interés y retorno total se calculan automáticamente.</p>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #10b981"></span>
                Monto del Préstamo (Capital)
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0.01" class="balance-input"
                  placeholder="0.00"
                  v-model.number="nuevoPrestamoForm.principal" />
              </div>
            </div>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #f59e0b"></span>
                Tasa (%)
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">%</span>
                <input type="number" step="0.01" min="0.01" class="balance-input"
                  placeholder="0.00"
                  v-model.number="nuevoPrestamoForm.rate" />
              </div>
            </div>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #1da1f2"></span>
                Plazo (meses)
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">#</span>
                <input type="number" min="1" class="balance-input"
                  placeholder="12"
                  v-model.number="nuevoPrestamoForm.termMonths" />
              </div>
            </div>

            <!-- Preview -->
            <div v-if="nuevoPrestamoForm.principal && nuevoPrestamoForm.rate && nuevoPrestamoForm.termMonths" class="nuevo-prestamo-preview">
              <div class="preview-row">
                <span>Interés Esperado</span>
                <span class="income">+${{ formatMoney(nuevoPrestamoInterest) }}</span>
              </div>
              <div class="preview-row">
                <span>Retorno Total</span>
                <span class="highlight">$ {{ formatMoney(nuevoPrestamoTotal) }}</span>
              </div>
            </div>

            <div v-if="nuevoPrestamoError" class="upload-error">
              <i class="pi pi-exclamation-triangle"></i> {{ nuevoPrestamoError }}
            </div>
          </div>

          <div class="upload-modal-footer">
            <button class="btn-cancel" @click="showNuevoPrestamoModal = false">Cancelar</button>
            <button
              class="btn-upload-confirm"
              :disabled="nuevoPrestamoSubmitting || !nuevoPrestamoValid"
              @click="submitNuevoPrestamo"
            >
              <i :class="nuevoPrestamoSubmitting ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
              {{ nuevoPrestamoSubmitting ? 'Registrando...' : 'Registrar Préstamo' }}
            </button>
          </div>
        </div>
      </div>

      <div class="loans-summary">
        <div class="loan-stat">
          <span class="loan-stat-label">Capital Prestado</span>
          <span class="loan-stat-value">${{ formatMoney(totalLoans) }}</span>
        </div>
        <div class="loan-stat">
          <span class="loan-stat-label">Intereses Esperados</span>
          <span class="loan-stat-value income">+${{ formatMoney(totalLoanInterest) }}</span>
        </div>
        <div class="loan-stat">
          <span class="loan-stat-label">Retorno Promedio</span>
          <span class="loan-stat-value">{{ avgLoanRate }}%</span>
        </div>
      </div>

      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Capital</th>
              <th>Tasa</th>
              <th>Plazo</th>
              <th>Interés Esperado</th>
              <th>Retorno Total</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="loan in loans" :key="loan.id">
              <td>${{ formatMoney(loan.principal) }}</td>
              <td><span class="rate-badge-sm">{{ loan.rate }}%</span></td>
              <td>{{ loan.term }}</td>
              <td class="income">+${{ formatMoney(loan.expectedInterest) }}</td>
              <td>${{ formatMoney(loan.totalReturn) }}</td>
              <td><span class="status-badge" :class="loan.status">{{ loan.statusLabel }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SECCIÓN: AFORE -->
    <div v-if="activeTab === 'afore'" class="section-content">

      <!-- Banner de actualización Afore (solo día 1 del mes sin actualizar) -->
      <div v-if="aforeUpdateStatus.needsUpdate" class="update-banner">
        <div class="update-banner-info">
          <i class="pi pi-refresh"></i>
          <div>
            <span class="update-banner-title">Afore pendiente de actualizar</span>
            <span class="update-banner-sub">
              Es día 1 del mes — revisa y actualiza tu saldo de Afore.
              <span v-if="aforeUpdateStatus.lastUpdate">
                Última actualización: {{ formatDate(aforeUpdateStatus.lastUpdate) }}
                (hace {{ aforeUpdateStatus.daysSinceUpdate }} días)
              </span>
              <span v-else>Nunca actualizado.</span>
            </span>
          </div>
        </div>
        <button class="btn-update" @click="showAforeModal = true">
          <i class="pi pi-pencil"></i> Actualizar datos
        </button>
      </div>

      <!-- Indicador de última actualización Afore -->
      <div v-else-if="aforeUpdateStatus.lastUpdate" class="update-ok">
        <i class="pi pi-check-circle"></i>
        <span>Afore actualizado el {{ formatDate(aforeUpdateStatus.lastUpdate) }}</span>
      </div>

      <!-- Modal de actualización Afore -->
      <div v-if="showAforeModal" class="upload-overlay" @click.self="showAforeModal = false">
        <div class="upload-modal">
          <div class="upload-modal-header">
            <h3><i class="pi pi-shield"></i> Actualizar Datos Afore</h3>
            <button class="btn-close" @click="showAforeModal = false"><i class="pi pi-times"></i></button>
          </div>

          <div class="upload-modal-body">
            <p class="upload-hint">Ingresa los datos actuales de tu Afore. Los campos vacíos no se modificarán.</p>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #1da1f2"></span>
                Saldo Acumulado
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(afore.balance)"
                  v-model.number="aforeFormData.balance" />
              </div>
            </div>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #10b981"></span>
                Rendimiento Anual (%)
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">%</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="afore.annualReturn"
                  v-model.number="aforeFormData.annualReturn" />
              </div>
            </div>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #f59e0b"></span>
                Aportación Bimestral
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(afore.bimonthlyContribution)"
                  v-model.number="aforeFormData.bimonthlyContribution" />
              </div>
            </div>

            <div class="balance-field">
              <label>
                <span class="balance-field-dot" style="background-color: #8b5cf6"></span>
                Aportación Voluntaria (semanal)
              </label>
              <div class="balance-input-wrap">
                <span class="balance-input-prefix">$</span>
                <input type="number" step="0.01" min="0" class="balance-input"
                  :placeholder="formatMoney(afore.voluntaryContribution)"
                  v-model.number="aforeFormData.voluntaryContribution" />
              </div>
            </div>

            <div v-if="aforeUpdateError" class="upload-error">
              <i class="pi pi-exclamation-triangle"></i> {{ aforeUpdateError }}
            </div>
          </div>

          <div class="upload-modal-footer">
            <button class="btn-cancel" @click="showAforeModal = false">Cancelar</button>
            <button
              class="btn-upload-confirm"
              :disabled="aforeUpdating || !hasAnyAforeField"
              @click="submitAforeData"
            >
              <i :class="aforeUpdating ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
              {{ aforeUpdating ? 'Guardando...' : 'Guardar datos' }}
            </button>
          </div>
        </div>
      </div>

      <div class="afore-card">
        <div class="afore-header">
          <div class="afore-brand"><i class="pi pi-shield"></i></div>
          <div>
            <h2>Afore</h2>
            <span class="section-desc">Cuenta de retiro</span>
          </div>
        </div>

        <div class="afore-stats">
          <div class="afore-stat">
            <span class="afore-stat-label">Saldo Acumulado</span>
            <span class="afore-stat-value">${{ formatMoney(afore.balance) }}</span>
          </div>
          <div class="afore-stat">
            <span class="afore-stat-label">Rendimiento Anual</span>
            <span class="afore-stat-value income">{{ afore.annualReturn }}%</span>
          </div>
          <div class="afore-stat">
            <span class="afore-stat-label">Aportación Bimestral</span>
            <span class="afore-stat-value">${{ formatMoney(afore.bimonthlyContribution) }}</span>
          </div>
          <div class="afore-stat">
            <span class="afore-stat-label">Aportación Voluntaria</span>
            <span class="afore-stat-value">${{ formatMoney(afore.voluntaryContribution) }}/semana</span>
          </div>
        </div>

        <div class="chart-container">
          <Line :data="aforeChartData" :options="lineOptions" />
        </div>

        <div class="afore-projection">
          <p>Proyección a 30 años con aportaciones actuales: <strong class="income">${{ formatNumber(aforeProjection30) }}</strong></p>
        </div>
      </div>
    </div>

    <!-- SECCIÓN: GBM -->
    <div v-if="activeTab === 'gbm'" class="section-content">

      <!-- Banner de actualización GBM (solo lunes sin actualizar) -->
      <div v-if="gbmUpdateStatus.needsUpdate" class="update-banner">
        <div class="update-banner-info">
          <i class="pi pi-refresh"></i>
          <div>
            <span class="update-banner-title">Portafolio GBM pendiente de actualizar</span>
            <span class="update-banner-sub">
              Es viernes — sube los archivos Excel descargados de la app GBM.
              <span v-if="gbmUpdateStatus.lastUpdate">
                Última actualización: {{ formatDate(gbmUpdateStatus.lastUpdate) }}
                (hace {{ gbmUpdateStatus.daysSinceUpdate }} días)
              </span>
              <span v-else>Nunca actualizado.</span>
            </span>
          </div>
        </div>
        <button class="btn-update" @click="showGbmUpload = true">
          <i class="pi pi-upload"></i> Subir archivos
        </button>
      </div>

      <!-- Indicador de última actualización GBM -->
      <div v-else-if="gbmUpdateStatus.lastUpdate" class="update-ok">
        <i class="pi pi-check-circle"></i>
        <span>Portafolio actualizado el {{ formatDate(gbmUpdateStatus.lastUpdate) }}</span>
      </div>

      <!-- Modal de upload -->
      <div v-if="showGbmUpload" class="upload-overlay" @click.self="showGbmUpload = false">
        <div class="upload-modal">
          <div class="upload-modal-header">
            <h3><i class="pi pi-upload"></i> Actualizar Portafolio GBM</h3>
            <button class="btn-close" @click="showGbmUpload = false"><i class="pi pi-times"></i></button>
          </div>

          <div class="upload-modal-body">
            <p class="upload-hint">Descarga los archivos desde la app GBM y súbelos aquí. El sistema los identificará automáticamente por su nombre.</p>

            <!-- Drop zone Nacional -->
            <div class="upload-field">
              <label>Portafolio Nacional (MXN)</label>
              <div class="drop-zone" :class="{ 'has-file': files.nacional }" @click="$refs.inputNacional.click()">
                <input ref="inputNacional" type="file" accept=".xlsx" style="display:none" @change="onFileChange('nacional', $event)" />
                <i :class="files.nacional ? 'pi pi-file-excel' : 'pi pi-cloud-upload'"></i>
                <span>{{ files.nacional ? files.nacional.name : 'Click para seleccionar o arrastra el archivo' }}</span>
              </div>
            </div>

            <!-- Drop zone USA -->
            <div class="upload-field">
              <label>Portafolio USA (USD)</label>
              <div class="drop-zone" :class="{ 'has-file': files.usa }" @click="$refs.inputUsa.click()">
                <input ref="inputUsa" type="file" accept=".xlsx" style="display:none" @change="onFileChange('usa', $event)" />
                <i :class="files.usa ? 'pi pi-file-excel' : 'pi pi-cloud-upload'"></i>
                <span>{{ files.usa ? files.usa.name : 'Click para seleccionar o arrastra el archivo' }}</span>
              </div>
            </div>

            <div v-if="uploadError" class="upload-error">
              <i class="pi pi-exclamation-triangle"></i> {{ uploadError }}
            </div>
          </div>

          <div class="upload-modal-footer">
            <button class="btn-cancel" @click="showGbmUpload = false">Cancelar</button>
            <button
              class="btn-upload-confirm"
              :disabled="!files.nacional || !files.usa || uploading"
              @click="uploadGbm"
            >
              <i :class="uploading ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
              {{ uploading ? 'Subiendo...' : 'Actualizar portafolio' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="gbmLoading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i> Cargando portafolio...
      </div>

      <div v-else>
        <div class="gbm-summary">
          <div class="gbm-stat">
            <span class="gbm-stat-label">Valor Total (MXN)</span>
            <span class="gbm-stat-value">${{ formatMoney(gbmSummary.totalValueMXN) }}</span>
          </div>
          <div class="gbm-stat">
            <span class="gbm-stat-label">Nacional (MXN)</span>
            <span class="gbm-stat-value">${{ formatMoney(gbmSummary.nacionalValueMXN) }}</span>
          </div>
          <div class="gbm-stat">
            <span class="gbm-stat-label">USA (USD)</span>
            <span class="gbm-stat-value">${{ formatMoney(gbmSummary.usaValueUSD) }}</span>
          </div>
          <div class="gbm-stat">
            <span class="gbm-stat-label">Rendimiento Total</span>
            <span class="gbm-stat-value" :class="gbmSummary.totalReturnPct >= 0 ? 'income' : 'expense'">
              {{ gbmSummary.totalReturnPct >= 0 ? '+' : '' }}{{ formatPct(gbmSummary.totalReturnPct) }}%
            </span>
          </div>
          <div class="gbm-stat">
            <span class="gbm-stat-label">TC USD/MXN</span>
            <span class="gbm-stat-value">{{ gbmSummary.usdMxnRate ? '$' + formatMoney(gbmSummary.usdMxnRate) : '...' }}</span>
          </div>
        </div>

        <!-- Gráficas de distribución -->
        <div class="charts-grid">
          <div class="chart-card">
            <h3>Portafolio Nacional (MXN)</h3>
            <Doughnut :data="gbmNacionalDistribution" :options="doughnutOptions" />
          </div>
          <div class="chart-card">
            <h3>Portafolio USA (USD)</h3>
            <Doughnut :data="gbmUsaDistribution" :options="doughnutOptions" />
          </div>
        </div>

        <!-- Gráficas de rendimiento -->
        <div class="charts-grid">
          <div class="chart-card">
            <h3>Rendimiento por Instrumento (%)</h3>
            <Bar :data="gbmPerformanceData" :options="barOptions" />
          </div>
          <div class="chart-card">
            <h3>Rendimiento en Efectivo ($)</h3>
            <Bar :data="gbmCashPerformanceData" :options="barOptions" />
          </div>
        </div>

        <!-- Tabla Nacional -->
        <div class="table-card">
          <h3>Mercado Nacional (MXN)</h3>
          <table class="data-table">
            <thead>
              <tr>
                <th>Emisora</th>
                <th>Títulos</th>
                <th>Costo Prom.</th>
                <th>Precio Mercado</th>
                <th>Valor Mercado</th>
                <th>+/- $</th>
                <th>Rendimiento %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in gbmNacional" :key="inv.ticker">
                <td><span class="ticker-name">{{ inv.ticker }}</span></td>
                <td>{{ inv.shares }}</td>
                <td>${{ formatMoney(inv.avgCost) }}</td>
                <td>${{ formatMoney(inv.marketPrice) }}</td>
                <td>${{ formatMoney(inv.marketValue) }}</td>
                <td :class="inv.gainLoss >= 0 ? 'income' : 'expense'">
                  {{ inv.gainLoss >= 0 ? '+' : '' }}${{ formatMoney(inv.gainLoss) }}
                </td>
                <td :class="inv.returnPct >= 0 ? 'income' : 'expense'">
                  {{ inv.returnPct >= 0 ? '+' : '' }}{{ formatPct(inv.returnPct) }}%
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td><strong>Total</strong></td>
                <td></td>
                <td></td>
                <td></td>
                <td><strong>${{ formatMoney(gbmNacionalTotals.marketValue) }}</strong></td>
                <td :class="gbmNacionalTotals.gainLoss >= 0 ? 'income' : 'expense'">
                  <strong>{{ gbmNacionalTotals.gainLoss >= 0 ? '+' : '' }}${{ formatMoney(gbmNacionalTotals.gainLoss) }}</strong>
                </td>
                <td :class="gbmNacionalTotals.returnPct >= 0 ? 'income' : 'expense'">
                  <strong>{{ gbmNacionalTotals.returnPct >= 0 ? '+' : '' }}{{ formatPct(gbmNacionalTotals.returnPct) }}%</strong>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Tabla USA -->
        <div class="table-card">
          <h3>Mercado USA (USD)</h3>
          <table class="data-table">
            <thead>
              <tr>
                <th>Emisora</th>
                <th>Títulos</th>
                <th>Costo Prom.</th>
                <th>Precio Mercado</th>
                <th>Valor (USD)</th>
                <th>+/- $</th>
                <th>Rendimiento %</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in gbmUSA" :key="inv.ticker">
                <td><span class="ticker-name">{{ inv.ticker }}</span></td>
                <td>{{ formatPct(inv.shares, 8) }}</td>
                <td>${{ formatMoney(inv.avgCost) }}</td>
                <td>${{ formatMoney(inv.marketPrice) }}</td>
                <td>${{ formatMoney(inv.marketValue) }}</td>
                <td :class="inv.gainLoss >= 0 ? 'income' : 'expense'">
                  {{ inv.gainLoss >= 0 ? '+' : '' }}${{ formatMoney(inv.gainLoss) }}
                </td>
                <td :class="inv.returnPct >= 0 ? 'income' : 'expense'">
                  {{ inv.returnPct >= 0 ? '+' : '' }}{{ formatPct(inv.returnPct) }}%
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td><strong>Total</strong></td>
                <td></td>
                <td></td>
                <td></td>
                <td><strong>${{ formatMoney(gbmUsaTotals.marketValue) }}</strong></td>
                <td :class="gbmUsaTotals.gainLoss >= 0 ? 'income' : 'expense'">
                  <strong>{{ gbmUsaTotals.gainLoss >= 0 ? '+' : '' }}${{ formatMoney(gbmUsaTotals.gainLoss) }}</strong>
                </td>
                <td :class="gbmUsaTotals.returnPct >= 0 ? 'income' : 'expense'">
                  <strong>{{ gbmUsaTotals.returnPct >= 0 ? '+' : '' }}{{ formatPct(gbmUsaTotals.returnPct) }}%</strong>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { Line, Doughnut, Bar } from 'vue-chartjs'
import finApi from '../utils/api'
import { cachedGet } from '../utils/cache'
import { usePreferencesStore } from '../stores/preferences'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler)

import { formatMoney, formatNumber, formatPct } from '../utils/format.js'

const activeTab = ref('savings')

const prefsStore = usePreferencesStore()

// Ensure preferences are loaded
if (!prefsStore.loaded) {
  prefsStore.load()
}

const allTabs = [
  { id: 'savings', label: 'Ahorro', icon: 'pi pi-wallet', pref: 'ahorro' },
  { id: 'loans', label: 'Préstamos', icon: 'pi pi-users', pref: 'prestamos' },
  { id: 'afore', label: 'Afore', icon: 'pi pi-shield', pref: 'afore' },
  { id: 'gbm', label: 'Acciones', icon: 'pi pi-chart-line', pref: 'acciones' }
]

const tabs = computed(() => {
  const filtered = allTabs.filter(t => prefsStore.isPanelEnabled(t.pref))
  // If active tab is no longer visible, switch to first available
  if (filtered.length && !filtered.find(t => t.id === activeTab.value)) {
    activeTab.value = filtered[0].id
  }
  return filtered
})

const periods = [
  { key: '1w', label: '1S', days: 7 },
  { key: '1m', label: '1M', days: 30 },
  { key: '3m', label: '3M', days: 90 },
  { key: '6m', label: '6M', days: 180 },
  { key: '1y', label: '1A', days: 365 },
  { key: '5y', label: '5A', days: 1825 },
  { key: '10y', label: '10A', days: 3650 }
]

// ===== CUENTAS DE AHORRO =====
const savingsAccounts = reactive([])

// ===== PRÉSTAMOS =====
const loans = ref([])
const totalLoans = ref(0)
const totalLoanInterest = ref(0)
const avgLoanRate = ref(0)

// ===== AFORE =====
const afore = reactive({
  balance: 0,
  annualReturn: 0,
  bimonthlyContribution: 0,
  voluntaryContribution: 0
})

function getCompoundData(balance, annualRate, periodKey, rateCap = 0, excessRate = 0) {
  const period = periods.find(p => p.key === periodKey)
  const days = period.days
  const taxRate = 0.9
  const points = []
  const labels = []

  let numPoints
  if (days <= 7) numPoints = 7
  else if (days <= 30) numPoints = 30
  else if (days <= 90) numPoints = 12
  else if (days <= 180) numPoints = 12
  else if (days <= 365) numPoints = 12
  else numPoints = 20

  for (let i = 0; i <= numPoints; i++) {
    const dayAt = Math.round((days / numPoints) * i)
    let value = balance
    for (let d = 0; d < dayAt; d++) {
      let dailyGain
      if (rateCap > 0 && value > rateCap) {
        dailyGain = (rateCap * (annualRate - taxRate) / 100 / 365) + ((value - rateCap) * (excessRate - taxRate) / 100 / 365)
      } else {
        dailyGain = value * (annualRate - taxRate) / 100 / 365
      }
      value += dailyGain
    }
    points.push(Math.round(value * 100) / 100)

    if (days <= 7) labels.push(`Día ${i}`)
    else if (days <= 30) labels.push(`Día ${dayAt}`)
    else if (days <= 365) labels.push(`Mes ${Math.round(dayAt / 30)}`)
    else labels.push(`Año ${(dayAt / 365).toFixed(1)}`)
  }

  return { points, labels }
}

function getCompoundChart(account) {
  const data = getCompoundData(account.balance, account.annualRate, account.selectedPeriod, account.rateCap || 0, account.excessRate || 0)
  return {
    labels: data.labels,
    datasets: [{
      label: 'Saldo Proyectado',
      data: data.points,
      borderColor: account.color,
      backgroundColor: account.color + '20',
      fill: true,
      tension: 0.4,
      pointRadius: 2
    }]
  }
}

function getProjection(account) {
  const period = periods.find(p => p.key === account.selectedPeriod)
  const taxRate = 0.9
  const rateCap = account.rateCap || 0
  const excessRate = account.excessRate || 0
  let value = account.balance
  for (let d = 0; d < period.days; d++) {
    let dailyGain
    if (rateCap > 0 && value > rateCap) {
      dailyGain = (rateCap * (account.annualRate - taxRate) / 100 / 365) + ((value - rateCap) * (excessRate - taxRate) / 100 / 365)
    } else {
      dailyGain = value * (account.annualRate - taxRate) / 100 / 365
    }
    value += dailyGain
  }
  return value
}

const lineOptions = {
  responsive: true,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: {
      ticks: { color: '#8899a6', maxTicksLimit: 8 },
      grid: { color: 'rgba(120,135,150,0.18)' }
    },
    y: {
      ticks: { color: '#8899a6' },
      grid: { color: 'rgba(120,135,150,0.18)' }
    }
  }
}

// (loans loaded from API)

// ===== AFORE (chart computeds) =====

const aforeChartData = computed(() => {
  const labels = []
  const data = []
  let balance = afore.balance
  const monthlyRate = afore.annualReturn / 100 / 12
  const monthlyContrib = afore.bimonthlyContribution / 2 + (afore.voluntaryContribution * 4.33)

  for (let year = 0; year <= 30; year += 5) {
    labels.push(`Año ${year}`)
    data.push(Math.round(balance))
    for (let m = 0; m < 60 && year < 30; m++) {
      balance = balance * (1 + monthlyRate) + monthlyContrib
    }
  }

  return {
    labels,
    datasets: [{
      label: 'Saldo Afore',
      data,
      borderColor: '#1da1f2',
      backgroundColor: 'rgba(29, 161, 242, 0.1)',
      fill: true,
      tension: 0.4
    }]
  }
})

const aforeProjection30 = computed(() => {
  let balance = afore.balance
  const monthlyRate = afore.annualReturn / 100 / 12
  const monthlyContrib = afore.bimonthlyContribution / 2 + (afore.voluntaryContribution * 4.33)
  for (let m = 0; m < 360; m++) {
    balance = balance * (1 + monthlyRate) + monthlyContrib
  }
  return balance
})

// ===== GBM (from API) =====
const gbmLoading = ref(true)
const gbmNacional = ref([])
const gbmUSA = ref([])
const gbmSummary = ref({
  nacionalValueMXN: 0,
  usaValueUSD: 0,
  usaValueMXN: 0,
  totalValueMXN: 0,
  totalGainMXN: 0,
  totalReturnPct: 0,
  usdMxnRate: 0
})

const gbmColors = ['#1da1f2', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6', '#e11d48', '#a855f7']

const gbmNacionalDistribution = computed(() => {
  const instruments = gbmNacional.value
  const total = instruments.reduce((s, i) => s + i.marketValue, 0)
  return {
    labels: instruments.map(i => i.ticker),
    datasets: [{
      data: instruments.map(i => total > 0 ? Math.round((i.marketValue / total) * 1000) / 10 : 0),
      backgroundColor: instruments.map((_, idx) => gbmColors[idx % gbmColors.length]),
      borderWidth: 0
    }]
  }
})

const gbmUsaDistribution = computed(() => {
  const instruments = gbmUSA.value
  const total = instruments.reduce((s, i) => s + i.marketValue, 0)
  return {
    labels: instruments.map(i => i.ticker),
    datasets: [{
      data: instruments.map(i => total > 0 ? Math.round((i.marketValue / total) * 1000) / 10 : 0),
      backgroundColor: instruments.map((_, idx) => gbmColors[(idx + 5) % gbmColors.length]),
      borderWidth: 0
    }]
  }
})

const gbmInstrumentsOnly = computed(() => {
  const cashSections = ['Efectivo', 'Liquidez']
  return [...gbmNacional.value, ...gbmUSA.value].filter(i => !cashSections.includes(i.section))
})

const gbmNacionalTotals = computed(() => {
  const items = gbmNacional.value
  const marketValue = items.reduce((s, i) => s + i.marketValue, 0)
  const gainLoss = items.reduce((s, i) => s + i.gainLoss, 0)
  const totalCost = items.reduce((s, i) => s + (i.avgCost * i.shares), 0)
  const returnPct = totalCost > 0 ? ((marketValue - totalCost) / totalCost) * 100 : 0
  return { marketValue, gainLoss, returnPct }
})

const gbmUsaTotals = computed(() => {
  const items = gbmUSA.value
  const marketValue = items.reduce((s, i) => s + i.marketValue, 0)
  const gainLoss = items.reduce((s, i) => s + i.gainLoss, 0)
  const totalCost = items.reduce((s, i) => s + (i.avgCost * i.shares), 0)
  const returnPct = totalCost > 0 ? ((marketValue - totalCost) / totalCost) * 100 : 0
  return { marketValue, gainLoss, returnPct }
})

const gbmPerformanceData = computed(() => {
  const allInstruments = gbmInstrumentsOnly.value.filter(i => i.returnPct !== 0)
  return {
    labels: allInstruments.map(i => i.ticker),
    datasets: [{
      label: 'Rendimiento %',
      data: allInstruments.map(i => i.returnPct),
      backgroundColor: allInstruments.map(i => i.returnPct >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'),
      borderRadius: 4
    }]
  }
})

const gbmCashPerformanceData = computed(() => {
  const instruments = gbmInstrumentsOnly.value.filter(i => i.gainLoss !== 0)
  return {
    labels: instruments.map(i => i.ticker),
    datasets: [{
      label: 'Rendimiento $',
      data: instruments.map(i => i.gainLoss),
      backgroundColor: instruments.map(i => i.gainLoss >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'),
      borderRadius: 4
    }]
  }
})

async function loadGBMData() {
  try {
    const response = await cachedGet('/api/gbm/portfolio')
    gbmNacional.value = response.data.nacional
    gbmUSA.value = response.data.usa
    gbmSummary.value = response.data.summary
  } catch (error) {
    console.error('Error loading GBM data:', error)
  } finally {
    gbmLoading.value = false
  }
}

async function loadInversiones() {
  try {
    const response = await cachedGet('/api/inversiones')
    const data = response.data

    // Ahorro
    data.ahorro.forEach(a => {
      savingsAccounts.push({ ...a, selectedPeriod: '1m' })
    })

    // Préstamos
    loans.value = data.prestamos
    totalLoans.value = data.summary.totalLoans
    totalLoanInterest.value = data.summary.totalLoanInterest
    avgLoanRate.value = data.summary.avgLoanRate

    // Afore
    Object.assign(afore, data.afore)
  } catch (error) {
    console.error('Error loading inversiones data:', error)
  }
}

// ===== ESTADO DE ACTUALIZACIÓN =====
const updateStatus = ref({ needsUpdate: false, lastUpdate: null, isMonday: false, daysSinceUpdate: null })
const updating = ref(false)
const aforeUpdateStatus = ref({ needsUpdate: false, lastUpdate: null, isFirstOfMonth: false, daysSinceUpdate: null })
const prestamosUpdateStatus = ref({ needsUpdate: false, lastUpdate: null, isFifteenth: false, daysSinceUpdate: null })

async function loadUpdateStatus() {
  try {
    const res = await cachedGet('/api/inversiones/update-status')
    updateStatus.value = res.data
  } catch { /* silencioso */ }
}

async function loadAforeUpdateStatus() {
  try {
    const res = await cachedGet('/api/inversiones/afore/update-status')
    aforeUpdateStatus.value = res.data
  } catch { /* silencioso */ }
}

async function loadPrestamosUpdateStatus() {
  try {
    const res = await cachedGet('/api/inversiones/prestamos/update-status')
    prestamosUpdateStatus.value = res.data
  } catch { /* silencioso */ }
}

// ===== MODAL ACTUALIZACIÓN AFORE =====
const showAforeModal = ref(false)
const aforeUpdating = ref(false)
const aforeUpdateError = ref('')
const aforeFormData = ref({})

const hasAnyAforeField = computed(() =>
  Object.values(aforeFormData.value).some(v => v !== null && v !== undefined && v !== '')
)

async function submitAforeData() {
  aforeUpdating.value = true
  aforeUpdateError.value = ''
  try {
    const fields = {}
    for (const [key, val] of Object.entries(aforeFormData.value)) {
      if (val !== null && val !== undefined && val !== '') {
        fields[key] = parseFloat(val)
      }
    }
    await finApi.post('/api/inversiones/afore/update-data', fields)
    // Recargar datos
    savingsAccounts.splice(0)
    await loadInversiones()
    await loadAforeUpdateStatus()
    showAforeModal.value = false
    aforeFormData.value = {}
  } catch (e) {
    aforeUpdateError.value = e.response?.data?.detail || 'Error al guardar los datos.'
  } finally {
    aforeUpdating.value = false
  }
}

// ===== MODAL ACTUALIZACIÓN PRÉSTAMOS =====
const showPrestamosModal = ref(false)
const prestamosUpdating = ref(false)
const prestamosUpdateError = ref('')
const prestamosFormData = ref({})

const hasAnyPrestamoField = computed(() =>
  Object.values(prestamosFormData.value).some(v => v !== null && v !== undefined && v !== '')
)

// ===== MODAL NUEVO PRÉSTAMO =====
const showNuevoPrestamoModal = ref(false)
const nuevoPrestamoSubmitting = ref(false)
const nuevoPrestamoError = ref('')
const nuevoPrestamoForm = ref({ principal: null, rate: null, termMonths: null })

const nuevoPrestamoValid = computed(() =>
  nuevoPrestamoForm.value.principal > 0 && nuevoPrestamoForm.value.rate > 0 && nuevoPrestamoForm.value.termMonths > 0
)

const nuevoPrestamoInterest = computed(() => {
  const f = nuevoPrestamoForm.value
  if (!f.principal || !f.rate || !f.termMonths) return 0
  return f.principal * (f.rate / 100) * (f.termMonths / 12)
})

const nuevoPrestamoTotal = computed(() => {
  const f = nuevoPrestamoForm.value
  if (!f.principal) return 0
  return f.principal + nuevoPrestamoInterest.value
})

async function submitNuevoPrestamo() {
  nuevoPrestamoSubmitting.value = true
  nuevoPrestamoError.value = ''
  try {
    await finApi.post('/api/inversiones/prestamos', {
      principal: nuevoPrestamoForm.value.principal,
      rate: nuevoPrestamoForm.value.rate,
      termMonths: nuevoPrestamoForm.value.termMonths
    })
    // Recargar datos
    savingsAccounts.splice(0)
    await loadInversiones()
    showNuevoPrestamoModal.value = false
    nuevoPrestamoForm.value = { principal: null, rate: null, termMonths: null }
  } catch (e) {
    nuevoPrestamoError.value = e.response?.data?.detail || 'Error al registrar el préstamo.'
  } finally {
    nuevoPrestamoSubmitting.value = false
  }
}

async function submitPrestamosData() {
  prestamosUpdating.value = true
  prestamosUpdateError.value = ''
  try {
    const updates = []
    for (const [id, val] of Object.entries(prestamosFormData.value)) {
      if (val !== null && val !== undefined && val !== '') {
        updates.push({ id: parseInt(id), principal: parseFloat(val) })
      }
    }
    await finApi.post('/api/inversiones/prestamos/update-data', { updates })
    // Recargar datos
    savingsAccounts.splice(0)
    await loadInversiones()
    await loadPrestamosUpdateStatus()
    showPrestamosModal.value = false
    prestamosFormData.value = {}
  } catch (e) {
    prestamosUpdateError.value = e.response?.data?.detail || 'Error al guardar los datos.'
  } finally {
    prestamosUpdating.value = false
  }
}

async function markUpdated() {
  updating.value = true
  try {
    await finApi.post('/api/inversiones/mark-updated')
    await loadUpdateStatus()
  } catch { /* silencioso */ } finally {
    updating.value = false
  }
}

// ===== MODAL ACTUALIZACIÓN SALDOS AHORRO =====
const showAhorroModal = ref(false)
const ahorroUpdating = ref(false)
const ahorroUpdateError = ref('')
const ahorroBalances = ref({})

const hasAnyBalance = computed(() =>
  Object.values(ahorroBalances.value).some(v => v !== null && v !== undefined && v !== '')
)

async function submitAhorroBalances() {
  ahorroUpdating.value = true
  ahorroUpdateError.value = ''
  try {
    // Solo enviar cuentas que tienen valor ingresado
    const balances = {}
    for (const [name, val] of Object.entries(ahorroBalances.value)) {
      if (val !== null && val !== undefined && val !== '') {
        balances[name] = Number(String(val).trim())
      }
    }
    await finApi.post('/api/inversiones/update-balances', { balances })
    // Recargar datos y estado
    savingsAccounts.splice(0)
    await loadInversiones()
    await loadUpdateStatus()
    showAhorroModal.value = false
    ahorroBalances.value = {}
  } catch (e) {
    ahorroUpdateError.value = e.response?.data?.detail || 'Error al guardar los saldos.'
  } finally {
    ahorroUpdating.value = false
  }
}

// ===== MODAL EDICIÓN INDIVIDUAL DE CUENTA DE AHORRO =====
const showSingleAhorroModal = ref(false)
const singleAhorroAccount = ref(null)
const singleAhorroBalance = ref(null)
const singleAhorroSaving = ref(false)
const singleAhorroError = ref('')

function openSingleAhorroModal(account) {
  singleAhorroAccount.value = account
  singleAhorroBalance.value = null
  singleAhorroError.value = ''
  showSingleAhorroModal.value = true
}

async function submitSingleAhorroBalance() {
  singleAhorroSaving.value = true
  singleAhorroError.value = ''
  try {
    const balances = {}
    const raw = String(singleAhorroBalance.value).trim()
    balances[singleAhorroAccount.value.name] = Number(raw)
    await finApi.post('/api/inversiones/update-balances', { balances })
    // Recargar datos y estado
    savingsAccounts.splice(0)
    await loadInversiones()
    await loadUpdateStatus()
    showSingleAhorroModal.value = false
    singleAhorroBalance.value = null
  } catch (e) {
    singleAhorroError.value = e.response?.data?.detail || 'Error al guardar el saldo.'
  } finally {
    singleAhorroSaving.value = false
  }
}

// ===== ESTADO DE ACTUALIZACIÓN GBM =====
const gbmUpdateStatus = ref({ needsUpdate: false, lastUpdate: null, isMonday: false, daysSinceUpdate: null })
const showGbmUpload = ref(false)
const uploading = ref(false)
const uploadError = ref('')
const files = ref({ nacional: null, usa: null })

async function loadGbmUpdateStatus() {
  try {
    const res = await cachedGet('/api/gbm/update-status')
    gbmUpdateStatus.value = res.data
  } catch { /* silencioso */ }
}

function onFileChange(type, event) {
  const file = event.target.files[0]
  if (file) files.value[type] = file
}

async function uploadGbm() {
  uploading.value = true
  uploadError.value = ''
  try {
    const form = new FormData()
    form.append('nacional', files.value.nacional)
    form.append('usa', files.value.usa)

    await finApi.post('/api/gbm/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // Recargar datos del portafolio con los nuevos archivos
    gbmLoading.value = true
    await loadGBMData()
    await loadGbmUpdateStatus()

    showGbmUpload.value = false
    files.value = { nacional: null, usa: null }
  } catch (e) {
    uploadError.value = e.response?.data?.detail || 'Error al subir los archivos.'
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadGBMData()
  loadInversiones()
  loadUpdateStatus()
  loadGbmUpdateStatus()
  loadAforeUpdateStatus()
  loadPrestamosUpdateStatus()
})

const doughnutOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom', labels: { color: '#8899a6', padding: 12 } },
    tooltip: {
      callbacks: {
        label: function(context) {
          return `${context.label}: ${context.parsed}%`
        }
      }
    }
  }
}

const barOptions = {
  responsive: true,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } },
    y: { ticks: { color: '#8899a6' }, grid: { color: 'rgba(120,135,150,0.18)' } }
  }
}

// ===== TOTALES =====
const dailyIncomeRevolutNu = computed(() => {
  return savingsAccounts.reduce((sum, a) => sum + (a.dailyGain || 0), 0)
})
const liquidez = computed(() => {
  return savingsAccounts.reduce((sum, a) => sum + (a.balance || 0), 0)
})
const totalSavings = computed(() => savingsAccounts.reduce((s, a) => s + a.balance, 0))
const totalMarket = computed(() => gbmSummary.value.totalValueMXN + afore.balance)
const frozenIncome = computed(() => gbmSummary.value.totalValueMXN + afore.balance + totalLoans.value)
const totalPortfolio = computed(() => totalSavings.value + totalLoans.value + totalMarket.value)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-')
  return `${d}-${m}-${y}`
}
</script>

<style scoped>
.inversiones {
  max-width: 1200px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--fin-text);
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.stat-icon.portfolio { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.stat-icon.savings { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
.stat-icon.loans { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.stat-icon.market { background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6; }

.stat-info { display: flex; flex-direction: column; }
.stat-label { font-size: 0.8rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: var(--fin-text); }

/* Tabs */
.section-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 10px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--fin-text-muted);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.tab-btn:hover { color: var(--fin-text); }
.tab-btn.active { background-color: #1da1f2; color: white; }

/* Savings Cards */
.savings-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 16px;
}

.savings-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-top: 3px solid;
  border-radius: 12px;
  padding: 20px;
}

.savings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.savings-brand {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.savings-header h3 { color: var(--fin-text); margin: 0; font-size: 1.1rem; }
.savings-subtitle { color: var(--fin-text-muted); font-size: 0.75rem; }

/* ── Botón editar en cada tarjeta de ahorro ──────────────────────────── */
.btn-edit-card {
  margin-left: auto;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  opacity: 0.5;
  transition: opacity 0.2s;
  padding: 4px;
}
.btn-edit-card:hover { opacity: 1; }

.savings-balance { margin-bottom: 12px; }
.balance-label { display: block; font-size: 0.75rem; color: var(--fin-text-muted); margin-bottom: 4px; }
.balance-value { font-size: 1.5rem; font-weight: 700; color: var(--fin-text); }

.savings-rate {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.rate-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.daily-gain { color: #10b981; font-size: 0.8rem; }

.period-selector {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  padding: 3px;
}

.period-btn {
  flex: 1;
  padding: 6px 8px;
  border: none;
  background: transparent;
  color: var(--fin-text-muted);
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.period-btn:hover { color: var(--fin-text); }
.period-btn.active { background-color: #1da1f2; color: white; }

.chart-container { margin-bottom: 12px; }

.projection-summary {
  display: flex;
  gap: 24px;
  padding: 12px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
}

.proj-item { display: flex; flex-direction: column; gap: 2px; }
.proj-label { font-size: 0.7rem; color: var(--fin-text-muted); }
.proj-value { font-size: 0.95rem; font-weight: 700; }

/* Loans */
.loans-header-info, .gbm-header-info { margin-bottom: 20px; }

.loading-state {
  text-align: center;
  padding: 40px;
  color: var(--fin-text-muted);
  font-size: 1rem;
}

.loading-state i {
  font-size: 1.5rem;
  margin-right: 8px;
}

.loans-header-info h2, .gbm-header-info h2 { color: var(--fin-text); font-size: 1.3rem; margin-bottom: 4px; }
.section-desc { color: var(--fin-text-muted); font-size: 0.85rem; }

.loans-summary, .gbm-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
}

.loan-stat, .gbm-stat { display: flex; flex-direction: column; gap: 4px; }
.loan-stat-label, .gbm-stat-label { font-size: 0.75rem; color: var(--fin-text-muted); }
.loan-stat-value, .gbm-stat-value { font-size: 1.2rem; font-weight: 700; color: var(--fin-text); }

/* Table */
.table-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
  overflow-x: auto;
  margin-bottom: 20px;
}

.table-card h3 { color: var(--fin-text); margin-bottom: 16px; font-size: 1rem; }

.data-table { width: 100%; border-collapse: collapse; }

.data-table th {
  text-align: left;
  padding: 12px 14px;
  font-size: 0.72rem;
  text-transform: uppercase;
  color: var(--fin-text-muted);
  border-bottom: 1px solid var(--fin-border);
  background-color: var(--fin-surface-2);
}

.data-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--fin-border);
  color: var(--fin-text);
  font-size: 0.83rem;
}

.data-table tr:hover td { background-color: var(--fin-hover); }

.data-table .total-row td {
  border-top: 2px solid #3d4f5f;
  border-bottom: none;
  background-color: #1a2733;
  padding: 14px;
}

.rate-badge-sm {
  background-color: rgba(16, 185, 129, 0.15);
  color: #10b981;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
}

.status-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.status-badge.active { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.status-badge.paid { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }

.income { color: #10b981; font-weight: 600; }
.expense { color: #ef4444; font-weight: 600; }

/* GBM */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 20px;
}

.chart-card h3 { color: var(--fin-text); margin-bottom: 12px; font-size: 0.95rem; }

.performance-cash-chart {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--fin-border);
}

.performance-cash-chart h4 {
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.ticker-cell { display: flex; flex-direction: column; }
.ticker-name { font-weight: 700; color: var(--fin-text); }
.ticker-desc { font-size: 0.7rem; color: var(--fin-text-muted); }

.type-badge-inv {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.type-badge-inv.etf { background-color: rgba(29, 161, 242, 0.15); color: #1da1f2; }
.type-badge-inv.stock { background-color: rgba(139, 92, 246, 0.15); color: #8b5cf6; }
.type-badge-inv.fibra { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; }

.recommendation {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.recommendation.buy { background-color: rgba(16, 185, 129, 0.15); color: #10b981; }
.recommendation.hold { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.recommendation.sell { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; }

/* Analysis */
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.analysis-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 10px;
  padding: 16px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ticker-tag {
  font-weight: 700;
  color: #1da1f2;
  font-size: 0.9rem;
}

.analysis-text {
  color: var(--fin-text-muted);
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 10px;
}

.analysis-metrics {
  display: flex;
  gap: 16px;
  font-size: 0.72rem;
  color: var(--fin-text-muted);
}

/* Afore */
.afore-card {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 12px;
  padding: 24px;
}

.afore-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.afore-brand {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background-color: rgba(29, 161, 242, 0.15);
  color: #1da1f2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
}

.afore-header h2 { color: var(--fin-text); margin: 0; }

.afore-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.afore-stat { display: flex; flex-direction: column; gap: 4px; }
.afore-stat-label { font-size: 0.75rem; color: var(--fin-text-muted); }
.afore-stat-value { font-size: 1.1rem; font-weight: 700; color: var(--fin-text); }

.afore-projection {
  margin-top: 16px;
  padding: 12px 16px;
  background-color: var(--fin-surface-2);
  border-radius: 8px;
  color: var(--fin-text-muted);
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .charts-grid { grid-template-columns: 1fr; }
  .savings-cards { grid-template-columns: 1fr; }
  .loans-summary, .gbm-summary { flex-direction: column; gap: 12px; }
  .section-tabs { flex-wrap: wrap; }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .stat-card {
    padding: 14px;
    gap: 10px;
  }

  .stat-icon {
    width: 38px;
    height: 38px;
    font-size: 1rem;
  }

  .stat-value {
    font-size: 1.1rem;
  }

  .page-title {
    font-size: 1.4rem;
  }

  .table-card {
    padding: 12px;
  }

  .data-table th,
  .data-table td {
    padding: 8px 10px;
    font-size: 0.72rem;
  }

  /* Hide less critical columns on mobile */
  .data-table th:nth-child(3),
  .data-table td:nth-child(3),
  .data-table th:nth-child(4),
  .data-table td:nth-child(4) {
    display: none;
  }

  .update-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .btn-update {
    width: 100%;
    justify-content: center;
  }

  .upload-modal {
    width: 95vw;
    max-height: 90vh;
  }

  .period-selector {
    flex-wrap: wrap;
  }

  .afore-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .afore-stats {
    grid-template-columns: 1fr;
  }

  .section-tabs {
    gap: 2px;
    padding: 3px;
  }

  .tab-btn {
    padding: 8px 10px;
    font-size: 0.75rem;
    gap: 4px;
  }
}

/* ── Banner de actualización ─────────────────────────────────────────── */
.update-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  margin-bottom: 20px;
  background-color: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 10px;
}

.update-banner-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: #f59e0b;
  font-size: 1.1rem;
}

.update-banner-info > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.update-banner-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #f59e0b;
}

.update-banner-sub {
  font-size: 0.78rem;
  color: var(--fin-text-muted);
}

.btn-update {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  background-color: #f59e0b;
  color: var(--fin-bg-2);
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-update:hover:not(:disabled) { background-color: #d97706; }
.btn-update:disabled { opacity: 0.6; cursor: not-allowed; }

.update-ok {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin-bottom: 20px;
  background-color: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 10px;
  color: #10b981;
  font-size: 0.82rem;
}

/* ── Modal de upload GBM ─────────────────────────────────────────────── */
.upload-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.upload-modal {
  background-color: var(--fin-surface);
  border: 1px solid var(--fin-border);
  border-radius: 14px;
  width: 480px;
  max-width: 95vw;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: hidden;
}

.upload-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--fin-border);
}

.upload-modal-header h3 {
  color: var(--fin-text);
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--fin-text-muted);
  font-size: 1rem;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: color 0.2s;
}
.btn-close:hover { color: var(--fin-text); }

.upload-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-hint {
  font-size: 0.82rem;
  color: var(--fin-text-muted);
  margin: 0;
}

.upload-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.upload-field label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--fin-text-muted);
  font-weight: 600;
}

.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  border: 2px dashed var(--fin-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--fin-text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.drop-zone:hover { border-color: #1da1f2; color: var(--fin-text); }

.drop-zone.has-file {
  border-color: #10b981;
  background-color: rgba(16, 185, 129, 0.06);
  color: #10b981;
}

.drop-zone i { font-size: 1.6rem; }

.upload-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 0.82rem;
}

.upload-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--fin-border);
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--fin-border);
  color: var(--fin-text-muted);
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel:hover { color: var(--fin-text); border-color: var(--fin-text-muted); }

.btn-upload-confirm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  background-color: #1da1f2;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-upload-confirm:hover:not(:disabled) { background-color: #1a91da; }
.btn-upload-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Botón editar saldos (inline en update-ok) ───────────────────────── */
.btn-update-sm {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: auto;
  padding: 5px 12px;
  background: transparent;
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #10b981;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-update-sm:hover { background: rgba(16, 185, 129, 0.1); }

/* ── Campos de saldo en modal de ahorro ──────────────────────────────── */
.balance-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.balance-field label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--fin-text);
  font-weight: 600;
}

.balance-field-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.balance-field-desc {
  font-size: 0.78rem;
  color: var(--fin-text-muted);
  font-weight: 400;
}

.balance-input-wrap {
  display: flex;
  align-items: center;
  background-color: var(--fin-bg-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.balance-input-wrap:focus-within { border-color: #1da1f2; }

.balance-input-prefix {
  padding: 0 10px;
  color: var(--fin-text-muted);
  font-size: 0.9rem;
  border-right: 1px solid var(--fin-border);
  line-height: 38px;
}

.balance-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--fin-text);
  font-size: 0.9rem;
  padding: 9px 12px;
}
.balance-input::placeholder { color: #4a5568; }
.balance-input::-webkit-inner-spin-button,
.balance-input::-webkit-outer-spin-button { opacity: 0.4; }

/* Botón Nuevo Préstamo */
.loans-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.btn-new-loan {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.2s;
}
.btn-new-loan:hover { background-color: #059669; }

.nuevo-prestamo-preview {
  background-color: var(--fin-bg-2);
  border: 1px solid var(--fin-border);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.preview-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--fin-text-muted);
}
.preview-row .income { color: #10b981; font-weight: 600; }
.preview-row .highlight { color: #f59e0b; font-weight: 600; }

/* ── Disclaimer de proyección ──────────────────────────────── */
.savings-disclaimer {
  margin-top: 1.5rem;
  padding: 0.75rem 1rem;
  background: rgba(120, 135, 150, 0.08);
  border-radius: 8px;
  color: #8899a6;
  font-size: 0.8rem;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}
.savings-disclaimer i {
  margin-top: 2px;
  font-size: 0.85rem;
  flex-shrink: 0;
}
</style>
