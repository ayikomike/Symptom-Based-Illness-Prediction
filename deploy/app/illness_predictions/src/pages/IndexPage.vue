<template>
  <q-page class="app-root">
    <!-- ═══════════════════ HEADER ═══════════════════ -->
    <header class="site-header">
      <div class="header-inner">
        <div class="header-text">
          <p class="eyebrow">CLINICAL INTELLIGENCE</p>
          <h1 class="site-title">Illness Prediction<br>System</h1>
          <p class="site-desc">
            Select presenting symptoms to predict probable illness using
            MLP and XGBoost ensemble models.
          </p>
          <div class="author-chip">
            <span class="author-icon">👤</span>
            Mike Ayiko &nbsp;·&nbsp; 20241201555
          </div>
        </div>
        <div class="stats-panel" aria-hidden="true">
          <div class="stats-panel-label">DIAGNOSTIC MODELS</div>
          <div class="stat-row">
            <div class="stat-item">
              <span class="stat-num">{{ ALL_SYMPTOMS.length }}</span>
              <span class="stat-lbl">Symptoms</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-num">—</span>
              <span class="stat-lbl">Categories</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-num">3</span>
              <span class="stat-lbl">Models</span>
            </div>
          </div>
          <div class="model-list">
            <div class="model-tag">MLP Neural Net</div>
            <div class="model-tag">XGBoost</div>
            <div class="model-tag model-tag--em">Ensemble</div>
          </div>
        </div>
      </div>
    </header>

    <main class="main-content">
      <!-- Mode & Model selector -->
      <div class="control-bar">
        <div class="mode-tabs">
          <button
            v-for="m in modes"
            :key="m.value"
            :class="['mode-tab', activeMode === m.value && 'mode-tab--active']"
            @click="activeMode = m.value"
          >
            <span>{{ m.icon }}</span> {{ m.label }}
          </button>
        </div>
        <div class="model-toggle-wrap">
          <span class="toggle-lbl">Model:</span>
          <div class="model-toggle">
            <button :class="['mtoggle-btn', modelType === 'all' && 'mtoggle-btn--active']" @click="modelType = 'all'">All (Ensemble)</button>
            <button :class="['mtoggle-btn', modelType === 'mlp' && 'mtoggle-btn--active']" @click="modelType = 'mlp'">MLP only</button>
            <button :class="['mtoggle-btn', modelType === 'xgb' && 'mtoggle-btn--active']" @click="modelType = 'xgb'">XGBoost only</button>
          </div>
        </div>
      </div>

      <!-- Single Symptom Entry -->
      <div v-if="activeMode === 'single'" class="form-card">
        <div class="form-section symptom-header-row">
          <div>
            <p class="form-section-label">Select Symptoms</p>
            <p class="symptom-subtext">
              Check all symptoms the patient is presenting. Missing symptoms are treated as absent (0).
            </p>
          </div>
          <div class="selected-count-badge" :class="selectedSymptoms.length > 0 && 'selected-count-badge--active'">
            {{ selectedSymptoms.length }} symptom{{ selectedSymptoms.length !== 1 ? 's' : '' }} selected
          </div>
        </div>

        <div class="form-section symptom-search-row">
          <q-input
            v-model="symptomSearch"
            outlined
            dense
            placeholder="Search symptoms…"
            class="search-input"
            clearable
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>
          <button v-if="selectedSymptoms.length > 0" class="clear-all-btn" @click="selectedSymptoms = []">
            Clear all
          </button>
        </div>

        <div v-if="selectedSymptoms.length > 0" class="form-section selected-chips-row">
          <p class="chips-label">Selected:</p>
          <div class="chips-wrap">
            <span
              v-for="sym in selectedSymptoms"
              :key="sym"
              class="symptom-chip symptom-chip--selected"
              @click="toggleSymptom(sym)"
            >
              {{ formatSymptomLabel(sym) }} <span class="chip-x">✕</span>
            </span>
          </div>
        </div>

        <div class="form-section symptom-grid-section">
          <div class="symptom-category">
            <div class="cat-header">
              <span class="cat-icon">📋</span>
              <span class="cat-name">All Symptoms</span>
              <span class="cat-count">{{ filteredSymptoms.length }} / {{ ALL_SYMPTOMS.length }}</span>
            </div>
            <div class="cat-symptoms">
              <button
                v-for="sym in filteredSymptoms"
                :key="sym"
                :class="['sym-btn', selectedSymptoms.includes(sym) && 'sym-btn--active']"
                @click="toggleSymptom(sym)"
              >
                <span class="sym-check">{{ selectedSymptoms.includes(sym) ? '✓' : '' }}</span>
                {{ formatSymptomLabel(sym) }}
              </button>
            </div>
          </div>
          <div v-if="filteredSymptoms.length === 0 && symptomSearch" class="no-results">
            No symptoms match "<strong>{{ symptomSearch }}</strong>"
          </div>
        </div>

        <div class="form-actions">
          <button class="run-btn" :disabled="loading || selectedSymptoms.length === 0" @click="predictSingle">
            <q-spinner v-if="loading" size="15px" color="white" />
            <span v-else>→</span>
            {{ loading ? 'Analysing…' : 'Predict Illness' }}
          </button>
        </div>
      </div>

      <!-- CSV Batch -->
      <div v-if="activeMode === 'csv'" class="form-card">
        <div class="form-section">
          <p class="form-section-label">Upload CSV</p>
          <p class="csv-hint">
            Each row represents one patient. Columns should be symptom names (e.g. <code>itching</code>, <code>skin_rash</code>).
            Values should be <code>1</code> (present) or <code>0</code> (absent). Missing columns default to <code>0</code>.
          </p>

          <div
            class="drop-zone"
            :class="{ 'drop-zone--over': isDragging, 'drop-zone--filled': parsedCsvData.length > 0 }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
            @click="() => fileRef?.click()"
          >
            <input ref="fileRef" type="file" accept=".csv" style="display:none" @change="onFileChange" />
            <template v-if="!parsedCsvData.length">
              <svg class="drop-svg" width="40" height="40" viewBox="0 0 40 40" fill="none">
                <rect x="8" y="5" width="24" height="30" rx="3" stroke="currentColor" stroke-width="1.6"/>
                <path d="M14 15h12M14 21h8M14 27h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M24 3v9h9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M24 3l9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <p class="drop-text">Drop CSV here or <span class="drop-link">browse</span></p>
            </template>
            <template v-else>
              <div class="drop-ok">✓</div>
              <p class="drop-text drop-text--ok"><strong>{{ csvFileName }}</strong> — {{ parsedCsvData.length }} patient{{ parsedCsvData.length !== 1 ? 's' : '' }}</p>
              <button class="clear-file-btn" @click.stop="clearCsv">Remove</button>
            </template>
          </div>

          <div v-if="csvPreviewRows.length" class="preview-wrap">
            <p class="preview-heading">Preview — first {{ csvPreviewRows.length }} of {{ parsedCsvData.length }} rows</p>
            <div class="preview-scroll">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Symptoms Present</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in csvPreviewRows" :key="row._idx">
                    <td class="mono muted">{{ row._idx }}</td>
                    <td>
                      <div class="preview-chips">
                        <span v-for="sym in row._symptoms.slice(0, 6)" :key="sym" class="preview-chip">
                          {{ formatSymptomLabel(sym) }}
                        </span>
                        <span v-if="row._symptoms.length > 6" class="preview-chip preview-chip--more">
                          +{{ row._symptoms.length - 6 }} more
                        </span>
                      </div>
                    </td>
                    <td class="mono">{{ row._symptoms.length }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="csvError" class="field-error">{{ csvError }}</div>
        </div>

        <div class="form-actions">
          <button class="run-btn" :disabled="loading || !parsedCsvData.length" @click="predictFromCSV">
            <q-spinner v-if="loading" size="15px" color="white" />
            <span v-else>→</span>
            {{ loading ? 'Analysing…' : 'Run Batch Prediction' }}
          </button>
        </div>
      </div>

      <!-- API Error -->
      <div v-if="apiError" class="api-error">
        <span>⚠</span>
        {{ apiError }}
        <button class="error-dismiss" @click="apiError = null">✕</button>
      </div>

      <!-- Results -->
      <section v-if="results.length" class="results-section">
        <div class="results-header-row">
          <p class="form-section-label" style="margin:0">Diagnosis Results</p>
          <span class="results-count-pill">{{ results.length }} patient{{ results.length !== 1 ? 's' : '' }}</span>
        </div>

        <div class="results-scroll">
          <table class="results-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Symptoms Presented</th>
                <th v-if="modelType === 'mlp' || modelType === 'all'" class="th-mlp">MLP Prediction</th>
                <th v-if="modelType === 'mlp' || modelType === 'all'" class="th-mlp">MLP Confidence</th>
                <th v-if="modelType === 'xgb' || modelType === 'all'" class="th-xgb">XGBoost Prediction</th>
                <th v-if="modelType === 'xgb' || modelType === 'all'" class="th-xgb">XGBoost Confidence</th>
                <th v-if="modelType === 'all'" class="th-ens">Ensemble Verdict</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in results" :key="row._idx">
                <td class="mono muted">{{ row._idx }}</td>
                <td>
                  <div class="result-chips">
                    <span v-for="sym in row._symptoms.slice(0, 4)" :key="sym" class="preview-chip">
                      {{ formatSymptomLabel(sym) }}
                    </span>
                    <span v-if="row._symptoms.length > 4" class="preview-chip preview-chip--more">
                      +{{ row._symptoms.length - 4 }}
                    </span>
                  </div>
                </td>
                <!-- MLP -->
                <template v-if="modelType === 'mlp' || modelType === 'all'">
                  <td>
                    <span v-if="row.mlp_prediction" class="disease-badge">{{ row.mlp_prediction }}</span>
                    <span v-else class="muted mono">—</span>
                  </td>
                  <td class="mono td-right">
                    <span v-if="row.mlp_confidence !== undefined" :class="confClass(row.mlp_confidence)">
                      {{ fmtConf(row.mlp_confidence) }}
                    </span>
                    <span v-else class="muted">—</span>
                  </td>
                </template>
                <!-- XGB -->
                <template v-if="modelType === 'xgb' || modelType === 'all'">
                  <td>
                    <span v-if="row.xgb_prediction" class="disease-badge disease-badge--xgb">{{ row.xgb_prediction }}</span>
                    <span v-else class="muted mono">—</span>
                  </td>
                  <td class="mono td-right">
                    <span v-if="row.xgb_confidence !== undefined" :class="confClass(row.xgb_confidence)">
                      {{ fmtConf(row.xgb_confidence) }}
                    </span>
                    <span v-else class="muted">—</span>
                  </td>
                </template>
                <!-- Ensemble verdict -->
                <template v-if="modelType === 'all'">
                  <td>
                    <span
                      v-if="row.ensemble_prediction"
                      :class="['verdict-badge', row.mlp_prediction === row.xgb_prediction ? 'verdict-badge--agree' : 'verdict-badge--split']"
                    >
                      {{ row.ensemble_prediction }}
                      <span class="verdict-agree-tag">{{ row.mlp_prediction === row.xgb_prediction ? '✓ Agree' : '⚡ Split' }}</span>
                    </span>
                    <span v-else class="muted mono">—</span>
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      Illness Prediction System · YUKUVILLAGE Clinical Intelligence · Mike Ayiko · 20241201555
    </footer>
  </q-page>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'
import Papa from 'papaparse'

const BASE_URL = 'https://illness.predictions.api.yukuvillage.com'

// ─── Complete symptom list extracted from your CSV header ───
const ALL_SYMPTOMS = [
  'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing',
  'shivering', 'chills', 'joint_pain', 'stomach_pain', 'acidity',
  'ulcers_on_tongue', 'muscle_wasting', 'vomiting', 'burning_micturition',
  'spotting_ urination', 'fatigue', 'weight_gain', 'anxiety',
  'cold_hands_and_feets', 'mood_swings', 'weight_loss', 'restlessness',
  'lethargy', 'patches_in_throat', 'irregular_sugar_level', 'cough',
  'high_fever', 'sunken_eyes', 'breathlessness', 'sweating', 'dehydration',
  'indigestion', 'headache', 'yellowish_skin', 'dark_urine', 'nausea',
  'loss_of_appetite', 'pain_behind_the_eyes', 'back_pain', 'constipation',
  'abdominal_pain', 'diarrhoea', 'mild_fever', 'yellow_urine',
  'yellowing_of_eyes', 'acute_liver_failure', 'fluid_overload',
  'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise',
  'blurred_and_distorted_vision', 'phlegm', 'throat_irritation',
  'redness_of_eyes', 'sinus_pressure', 'runny_nose', 'congestion',
  'chest_pain', 'weakness_in_limbs', 'fast_heart_rate',
  'pain_during_bowel_movements', 'pain_in_anal_region', 'bloody_stool',
  'irritation_in_anus', 'neck_pain', 'dizziness', 'cramps', 'bruising',
  'obesity', 'swollen_legs', 'swollen_blood_vessels', 'puffy_face_and_eyes',
  'enlarged_thyroid', 'brittle_nails', 'swollen_extremeties',
  'excessive_hunger', 'extra_marital_contacts', 'drying_and_tingling_lips',
  'slurred_speech', 'knee_pain', 'hip_joint_pain', 'muscle_weakness',
  'stiff_neck', 'swelling_joints', 'movement_stiffness',
  'spinning_movements', 'loss_of_balance', 'unsteadiness',
  'weakness_of_one_body_side', 'loss_of_smell', 'bladder_discomfort',
  'foul_smell_of urine', 'continuous_feel_of_urine', 'passage_of_gases',
  'internal_itching', 'toxic_look_(typhos)', 'depression', 'irritability',
  'muscle_pain', 'altered_sensorium', 'red_spots_over_body', 'belly_pain',
  'abnormal_menstruation', 'dischromic _patches', 'watering_from_eyes',
  'increased_appetite', 'polyuria', 'family_history', 'mucoid_sputum',
  'rusty_sputum', 'lack_of_concentration', 'visual_disturbances',
  'receiving_blood_transfusion', 'receiving_unsterile_injections', 'coma',
  'stomach_bleeding', 'distention_of_abdomen', 'history_of_alcohol_consumption',
  'fluid_overload.1', 'blood_in_sputum', 'prominent_veins_on_calf',
  'palpitations', 'painful_walking', 'pus_filled_pimples', 'blackheads',
  'scurring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails',
  'inflammatory_nails', 'blister', 'red_sore_around_nose', 'yellow_crust_ooze'
]

function formatLabel(sym) {
  return sym.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// Builds a full instance dict with all symptoms (0 or 1)
function buildInstance(symptoms) {
  const instance = {}
  ALL_SYMPTOMS.forEach(s => {
    instance[s] = symptoms.includes(s) ? 1 : 0
  })
  return instance
}

function extractSymptoms(row) {
  return ALL_SYMPTOMS.filter(sym => String(row[sym] || 0).trim() === '1')
}

export default defineComponent({
  name: 'IllnessPredictor',
  setup() {
    const $q = useQuasar()

    const activeMode = ref('single')
    const modes = [
      { value: 'single', label: 'Symptom Selector', icon: '✏️' },
      { value: 'csv',    label: 'Batch CSV',         icon: '📄' },
    ]
    const modelType = ref('all')

    const selectedSymptoms = ref([])
    const symptomSearch = ref('')

    const isDragging = ref(false)
    const csvFileName = ref('')
    const parsedCsvData = ref([])
    const csvError = ref('')
    const fileRef = ref(null)

    const loading = ref(false)
    const results = ref([])
    const apiError = ref(null)

    const filteredSymptoms = computed(() => {
      const q = (symptomSearch.value || '').toLowerCase().trim()
      if (!q) return ALL_SYMPTOMS
      return ALL_SYMPTOMS.filter(s => s.replace(/_/g, ' ').includes(q))
    })

    const csvPreviewRows = computed(() => {
      return parsedCsvData.value.slice(0, 5).map((row, i) => ({
        _idx: i + 1,
        _symptoms: extractSymptoms(row),
      }))
    })

    function formatSymptomLabel(sym) {
      return formatLabel(sym)
    }

    function toggleSymptom(sym) {
      const idx = selectedSymptoms.value.indexOf(sym)
      if (idx === -1) selectedSymptoms.value.push(sym)
      else selectedSymptoms.value.splice(idx, 1)
    }

    function fmtConf(val) {
      if (val === undefined || val === null) return '—'
      return (Number(val) * 100).toFixed(1) + '%'
    }

    function confClass(val) {
      if (val === undefined || val === null) return ''
      const n = Number(val)
      if (n >= 0.80) return 'conf-high'
      if (n >= 0.50) return 'conf-mid'
      return 'conf-low'
    }

    async function callEndpoint(endpoint, instances) {
      // console.log('Sending payload:', { instances })
      const { data } = await axios.post(`${BASE_URL}${endpoint}`, { instances })
      return data
    }

    function parseResponse(data, instanceSymptoms, modelType) {
        const preds = data.predictions || data.results || data || []
        return (Array.isArray(preds) ? preds : [preds]).map((p, i) => {
          const syms = instanceSymptoms[i] ?? []
          let mlpDisease = null, mlpConf = null
          let xgbDisease = null, xgbConf = null
          let ensemblePred = null

          // Check if it's the combined response (has mlp and xgboost objects)
          if (p.mlp && p.xgboost) {
            mlpDisease = p.mlp.predicted_disease || null
            mlpConf = p.mlp.confidence ?? null
            xgbDisease = p.xgboost.predicted_disease || null
            xgbConf = p.xgboost.confidence ?? null
            // Ensemble verdict
            if (mlpDisease && xgbDisease) {
              ensemblePred = mlpDisease === xgbDisease ? mlpDisease : '⚡ Split'
            } else {
              ensemblePred = mlpDisease || xgbDisease
            }
          } else {
            // Single model response – top‑level predicted_disease & confidence
            const disease = p.predicted_disease || null
            const conf = p.confidence ?? null
            if (modelType === 'mlp') {
              mlpDisease = disease
              mlpConf = conf
            } else if (modelType === 'xgb') {
              xgbDisease = disease
              xgbConf = conf
            }
            // For single model, the ensemble prediction is just that model's prediction
            ensemblePred = disease
          }

          return {
            _idx: i + 1,
            _symptoms: syms,
            mlp_prediction: mlpDisease,
            mlp_confidence: mlpConf,
            xgb_prediction: xgbDisease,
            xgb_confidence: xgbConf,
            ensemble_prediction: ensemblePred,
          }
        })
      }

    async function runPrediction(instances, instanceSymptoms) {
        loading.value = true
        apiError.value = null
        results.value = []
        try {
          let data
          if (modelType.value === 'all') {
            data = await callEndpoint('/predict_all', instances)
          } else if (modelType.value === 'mlp') {
            data = await callEndpoint('/predict_mlp', instances)
          } else {
            data = await callEndpoint('/predict_xgboost', instances)
          }
          // Pass modelType.value to parseResponse
          results.value = parseResponse(data, instanceSymptoms, modelType.value)
        } catch (err) {
          apiError.value = err.response?.data?.detail || err.message || 'Request failed'
        } finally {
          loading.value = false
        }
      }

    async function predictSingle() {
      if (!selectedSymptoms.value.length) {
        apiError.value = 'Please select at least one symptom.'
        return
      }
      const instance = buildInstance(selectedSymptoms.value)
      // console.log([instance], [selectedSymptoms.value])
      await runPrediction([instance], [selectedSymptoms.value])
    }

    function onDrop(e) {
      isDragging.value = false
      const file = e.dataTransfer.files[0]
      if (file) parseFile(file)
    }

    function onFileChange(e) {
      const file = e.target.files[0]
      if (file) parseFile(file)
    }

    function parseFile(file) {
      csvFileName.value = file.name
      csvError.value = ''
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (res) => {
          parsedCsvData.value = res.data
        },
        error: (err) => {
          csvError.value = `Parse error: ${err.message}`
          parsedCsvData.value = []
        },
      })
    }

    function clearCsv() {
      parsedCsvData.value = []
      csvFileName.value = ''
      csvError.value = ''
      results.value = []
      if (fileRef.value) fileRef.value.value = ''
    }

    async function predictFromCSV() {
      if (!parsedCsvData.value.length) return
      const instanceSymptoms = parsedCsvData.value.map(row => extractSymptoms(row))
      const instances = instanceSymptoms.map(syms => buildInstance(syms))
      // console.log(instances, instanceSymptoms)
      await runPrediction(instances, instanceSymptoms)
    }

    onMounted(() => {
      // Any startup logic
    })

    return {
      ALL_SYMPTOMS,
      activeMode,
      modes,
      modelType,
      selectedSymptoms,
      symptomSearch,
      isDragging,
      csvFileName,
      parsedCsvData,
      csvError,
      fileRef,
      loading,
      results,
      apiError,
      filteredSymptoms,
      csvPreviewRows,
      formatSymptomLabel,
      toggleSymptom,
      fmtConf,
      confClass,
      predictSingle,
      onDrop,
      onFileChange,
      parseFile,
      clearCsv,
      predictFromCSV,
    }
  }
})
</script>


<style scoped>
/* ─── Tokens ─── */
.app-root {
  --teal:        #1a5f5a;
  --teal-mid:    #2a8a80;
  --teal-light:  #e5f3f2;
  --crimson:     #8b1a1a;
  --amber:       #c87820;
  --amber-light: #fdf3e0;
  --cream:       #f7f9f8;
  --white:       #ffffff;
  --ink:         #111c1b;
  --muted:       #637570;
  --border:      #d8e2e0;
  --conf-high:   #1a6a40;
  --conf-mid:    #c87820;
  --conf-low:    #8b1a1a;
  --mono:        'JetBrains Mono', 'Fira Mono', monospace;

  background:  var(--cream);
  font-family: 'Inter', system-ui, sans-serif;
  color:       var(--ink);
  min-height:  100vh;
  padding:     0 !important;
}

/* ─── Header ─── */
.site-header {
  background: var(--teal);
  padding: 40px 0 0;
  overflow: hidden;
}
.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 40px;
}
.eyebrow {
  margin: 0 0 12px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #7de0d8;
}
.site-title {
  margin: 0 0 14px;
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 800;
  line-height: 1.06;
  color: var(--white);
  letter-spacing: -0.02em;
}
.site-desc {
  margin: 0 0 14px;
  font-size: 14px;
  color: #9cccc8;
  max-width: 400px;
  line-height: 1.65;
}
.author-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 20px;
  padding: 5px 14px;
  font-size: 12px;
  color: #c0e0de;
  margin-bottom: 36px;
}
.author-icon { font-size: 14px; }

/* Stats panel */
.stats-panel {
  flex-shrink: 0;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  padding: 16px 20px 0;
  min-width: 240px;
}
.stats-panel-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #7de0d8;
  text-align: center;
  margin-bottom: 14px;
}
.stat-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 14px;
}
.stat-item { text-align: center; }
.stat-num {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: var(--white);
  font-family: var(--mono);
}
.stat-lbl { font-size: 10px; color: #9cccc8; }
.stat-divider { width: 1px; height: 30px; background: rgba(255,255,255,0.15); }
.model-list {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding-bottom: 14px;
}
.model-tag {
  font-size: 10px;
  font-weight: 600;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 4px;
  padding: 3px 9px;
  color: #c0e0de;
}
.model-tag--em {
  background: rgba(125, 224, 216, 0.2);
  border-color: #7de0d8;
  color: #7de0d8;
}

/* ─── Main ─── */
.main-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 32px 64px;
}

/* ─── Control bar ─── */
.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 22px;
  flex-wrap: wrap;
}
.mode-tabs { display: flex; gap: 8px; }
.mode-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--white);
  font-size: 13.5px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
}
.mode-tab:hover { border-color: var(--teal-mid); color: var(--teal); }
.mode-tab--active { background: var(--teal); border-color: var(--teal); color: var(--white); }

.model-toggle-wrap { display: flex; align-items: center; gap: 10px; }
.toggle-lbl { font-size: 12px; font-weight: 600; color: var(--muted); }
.model-toggle {
  display: flex;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}
.mtoggle-btn {
  padding: 5px 14px;
  border: none;
  border-radius: 5px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.mtoggle-btn:hover { color: var(--ink); }
.mtoggle-btn--active { background: var(--teal); color: var(--white); }

/* ─── Form card ─── */
.form-card {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 24px;
}
.form-section {
  padding: 20px 28px;
  border-bottom: 1.5px solid var(--border);
}
.form-section:last-child { border-bottom: none; }
.form-section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 10px;
}

/* ─── Symptom header row ─── */
.symptom-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.symptom-subtext {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
}
.selected-count-badge {
  flex-shrink: 0;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  background: var(--border);
  color: var(--muted);
  transition: all 0.2s;
  white-space: nowrap;
}
.selected-count-badge--active {
  background: var(--teal-light);
  color: var(--teal);
  border: 1px solid var(--teal-mid);
}

/* ─── Symptom search row ─── */
.symptom-search-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.search-input { flex: 1; }
.clear-all-btn {
  padding: 7px 16px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  white-space: nowrap;
}
.clear-all-btn:hover { border-color: var(--crimson); color: var(--crimson); }

/* ─── Selected chips ─── */
.selected-chips-row { padding-top: 12px; padding-bottom: 12px; }
.chips-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
.chips-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.symptom-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  border-radius: 20px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.symptom-chip--selected {
  background: var(--teal);
  color: var(--white);
  border: 1.5px solid var(--teal);
}
.symptom-chip--selected:hover { background: var(--crimson); border-color: var(--crimson); }
.chip-x { font-size: 10px; opacity: 0.7; }

/* ─── Symptom grid ─── */
.symptom-grid-section {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
}
.symptom-category {
  border-bottom: 1px solid var(--border);
}
.symptom-category:last-child { border-bottom: none; }
.cat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px 8px;
  background: var(--cream);
}
.cat-icon  { font-size: 16px; }
.cat-name  { font-size: 13px; font-weight: 700; color: var(--ink); }
.cat-count { font-size: 11px; color: var(--muted); margin-left: auto; font-family: var(--mono); }
.cat-symptoms {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 28px 14px;
}
.sym-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1.5px solid var(--border);
  border-radius: 20px;
  background: var(--white);
  font-size: 12.5px;
  font-weight: 500;
  color: var(--ink);
  cursor: pointer;
  transition: all 0.15s;
}
.sym-btn:hover { border-color: var(--teal-mid); color: var(--teal); }
.sym-btn--active {
  background: var(--teal);
  border-color: var(--teal);
  color: var(--white);
  font-weight: 600;
}
.sym-check {
  font-size: 10px;
  width: 12px;
  display: inline-block;
}

.no-results {
  padding: 32px 28px;
  font-size: 14px;
  color: var(--muted);
  text-align: center;
}

/* ─── Form actions ─── */
.form-actions { padding: 20px 28px; }
.run-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px;
  background: var(--teal);
  color: var(--white);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
}
.run-btn:hover:not(:disabled) { background: var(--teal-mid); }
.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ─── CSV ─── */
.csv-hint {
  font-size: 13px;
  color: var(--muted);
  background: var(--teal-light);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
  line-height: 1.7;
}
.csv-hint code {
  font-family: var(--mono);
  font-size: 11.5px;
  background: rgba(0,0,0,0.06);
  border-radius: 4px;
  padding: 1px 5px;
  color: var(--teal);
}
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 10px;
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.18s;
  background: var(--cream);
}
.drop-zone:hover, .drop-zone--over { border-color: var(--teal-mid); background: var(--teal-light); }
.drop-zone--filled { border-style: solid; border-color: var(--teal-mid); background: var(--teal-light); }
.drop-svg { color: var(--muted); }
.drop-ok { font-size: 32px; color: var(--teal-mid); }
.drop-text { margin: 0; font-size: 13.5px; color: var(--muted); text-align: center; }
.drop-text--ok { color: var(--ink); font-weight: 500; }
.drop-link { color: var(--teal-mid); font-weight: 600; }
.clear-file-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 12px;
  color: var(--muted);
  cursor: pointer;
}
.clear-file-btn:hover { border-color: var(--crimson); color: var(--crimson); }
.field-error {
  margin-top: 10px;
  font-size: 13px;
  color: var(--crimson);
  background: #fef2f2;
  border-radius: 7px;
  padding: 8px 12px;
}

/* ─── Preview ─── */
.preview-wrap { margin-top: 18px; }
.preview-heading {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 8px;
}
.preview-scroll { overflow-x: auto; }
.preview-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.preview-table th {
  text-align: left;
  padding: 6px 12px;
  background: var(--teal-light);
  color: var(--teal);
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  border-bottom: 1.5px solid var(--border);
}
.preview-table td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
.preview-chips, .result-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.preview-chip {
  display: inline-block;
  background: var(--teal-light);
  border: 1px solid #a0ccc8;
  color: var(--teal);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 11.5px;
  font-weight: 500;
  white-space: nowrap;
}
.preview-chip--more {
  background: var(--cream);
  border-color: var(--border);
  color: var(--muted);
}

/* ─── API error ─── */
.api-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 16px;
  background: #fef2f2;
  border: 1.5px solid #fca5a5;
  border-radius: 9px;
  font-size: 13.5px;
  color: var(--crimson);
  margin-bottom: 20px;
}
.error-dismiss { margin-left: auto; background: none; border: none; color: var(--crimson); cursor: pointer; font-size: 15px; }

/* ─── Results ─── */
.results-section {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}
.results-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--teal-light);
  border-bottom: 1.5px solid var(--border);
}
.results-count-pill {
  font-size: 12px;
  font-weight: 600;
  background: rgba(26,95,90,0.12);
  color: var(--teal);
  border-radius: 20px;
  padding: 3px 12px;
}
.results-scroll { overflow-x: auto; }
.results-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.results-table thead tr { background: var(--teal); }
.results-table th {
  padding: 10px 14px;
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9de8e2;
  text-align: left;
  white-space: nowrap;
}
.th-mlp { border-left: 2px solid #2a5f8a; color: #9db8e8 !important; }
.th-xgb { border-left: 2px solid #8a5a1a; color: #e8c880 !important; }
.th-ens { border-left: 2px solid #5a1a5a; color: #e090e0 !important; }
.results-table td { padding: 10px 14px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
.results-table tbody tr:hover { background: var(--teal-light); }

/* ─── Disease badge ─── */
.disease-badge {
  display: inline-block;
  background: #e8f4ff;
  border: 1px solid #90c0e8;
  color: #1a4a7a;
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 12.5px;
  font-weight: 700;
  white-space: nowrap;
}
.disease-badge--xgb {
  background: var(--amber-light);
  border-color: #e0b060;
  color: #6a3c00;
}

/* ─── Confidence colouring ─── */
.conf-high { color: var(--conf-high); font-weight: 700; font-family: var(--mono); }
.conf-mid  { color: var(--conf-mid);  font-weight: 600; font-family: var(--mono); }
.conf-low  { color: var(--conf-low);  font-weight: 500; font-family: var(--mono); }

/* ─── Verdict badge ─── */
.verdict-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border-radius: 7px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}
.verdict-badge--agree {
  background: #e8f5e9;
  border: 1px solid #80c880;
  color: #1a5a1a;
}
.verdict-badge--split {
  background: var(--amber-light);
  border: 1px solid #e0b060;
  color: #6a3c00;
}
.verdict-agree-tag {
  font-size: 10px;
  font-weight: 700;
  opacity: 0.75;
}

/* ─── Utility ─── */
.mono  { font-family: var(--mono); font-size: 12.5px; }
.muted { color: var(--muted); }
.td-right { text-align: right; }

/* ─── Footer ─── */
.site-footer {
  background: var(--teal);
  color: #5a9c98;
  text-align: center;
  font-size: 11.5px;
  letter-spacing: 0.07em;
  padding: 18px;
}

@media (max-width: 700px) {
  .header-inner   { flex-direction: column; align-items: flex-start; padding: 0 20px; }
  .stats-panel    { display: none; }
  .main-content   { padding: 20px 16px 48px; }
  .form-section   { padding: 16px 16px; }
  .cat-header     { padding: 10px 16px 6px; }
  .cat-symptoms   { padding: 6px 16px 12px; }
  .form-actions   { padding: 16px; }
  .control-bar    { flex-direction: column; align-items: flex-start; }
  .model-toggle-wrap { width: 100%; }
  .symptom-header-row { flex-direction: column; align-items: flex-start; }
}
</style>