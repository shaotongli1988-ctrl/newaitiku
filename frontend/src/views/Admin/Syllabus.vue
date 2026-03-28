<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { UploadFilled } from '@/ui/icons'
import {
  createSyllabusVersion,
  fetchAdminSyllabusData,
  parseSyllabusWithAi,
  saveSyllabusWeights,
} from '../../api/services/questionBank'

const loading = ref(false)
const creating = ref(false)
const saving = ref(false)
const parsing = ref(false)
const versions = ref([])
const selectedVersionId = ref('')
const tableRows = ref([])
const aiParserReport = ref(null)
const aiUploadFile = ref(null)
const aiUploadFileList = ref([])

const createForm = reactive({
  versionName: '',
  copyFromVersionId: '',
})

const selectedVersion = computed(() => versions.value.find((item) => item.versionId === selectedVersionId.value) || null)

const totalWeight = computed(() => {
  const total = tableRows.value.reduce((sum, item) => sum + Number(item.targetWeight || 0), 0)
  return Number(total.toFixed(6))
})

const isWeightTotalValid = computed(() => Math.abs(totalWeight.value - 1) <= 0.000001)

function normalizeWeight(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return 0
  }
  if (numeric < 0) {
    return 0
  }
  if (numeric > 1) {
    return 1
  }
  return Number(numeric.toFixed(6))
}

function cloneVersionWeights(version) {
  const sourceRows = Array.isArray(version?.knowledgeWeights) ? version.knowledgeWeights : []
  return sourceRows.map((item, index) => ({
    rowKey: `${item.knowledgeId}-${index}`,
    knowledgeId: String(item.knowledgeId || ''),
    knowledgeName: String(item.knowledgeName || item.knowledgeId || ''),
    sort: Number(item.sort || (index + 1) * 10),
    targetWeight: normalizeWeight(item.targetWeight),
  }))
}

function cloneIncomingWeights(weights) {
  const sourceRows = Array.isArray(weights) ? weights : []
  return sourceRows.map((item, index) => ({
    rowKey: `${item.knowledgeId}-${index}`,
    knowledgeId: String(item.knowledgeId || ''),
    knowledgeName: String(item.knowledgeName || item.knowledgeId || ''),
    sort: Number(item.sort || (index + 1) * 10),
    targetWeight: normalizeWeight(item.targetWeight),
  }))
}

function syncRowsBySelectedVersion() {
  const version = selectedVersion.value
  tableRows.value = cloneVersionWeights(version)
}

function applySyllabusPayload(payload) {
  const fetchedVersions = Array.isArray(payload?.versions) ? payload.versions : []
  versions.value = fetchedVersions
  const preferredId = String(payload?.selectedVersionId || '').trim()
  const firstVersionId = String(fetchedVersions[0]?.versionId || '').trim()
  const keepId = String(selectedVersionId.value || '').trim()
  if (preferredId && fetchedVersions.some((item) => item.versionId === preferredId)) {
    selectedVersionId.value = preferredId
  } else if (keepId && fetchedVersions.some((item) => item.versionId === keepId)) {
    selectedVersionId.value = keepId
  } else {
    selectedVersionId.value = firstVersionId
  }
  syncRowsBySelectedVersion()
}

async function loadSyllabusData() {
  loading.value = true
  try {
    const payload = await fetchAdminSyllabusData()
    applySyllabusPayload(payload)
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '大纲仓库数据加载失败'))
  } finally {
    loading.value = false
  }
}

async function submitCreateVersion() {
  if (creating.value) {
    return
  }
  const versionName = String(createForm.versionName || '').trim()
  if (!versionName) {
    ElMessage.warning('请先输入大纲版本名称。')
    return
  }
  creating.value = true
  try {
    const payload = await createSyllabusVersion({
      versionName,
      copyFromVersionId: String(createForm.copyFromVersionId || '').trim(),
    })
    applySyllabusPayload(payload)
    createForm.versionName = ''
    ElMessage.success('大纲版本创建成功。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '大纲版本创建失败'))
  } finally {
    creating.value = false
  }
}

function rebalanceToAverage() {
  if (!tableRows.value.length) {
    ElMessage.warning('当前版本没有可编辑的知识点。')
    return
  }
  const totalUnits = 1000000
  const baseUnits = Math.floor(totalUnits / tableRows.value.length)
  const remainderUnits = totalUnits - (baseUnits * tableRows.value.length)
  tableRows.value = tableRows.value.map((item, index) => ({
    ...item,
    targetWeight: Number(((baseUnits + (index < remainderUnits ? 1 : 0)) / totalUnits).toFixed(6)),
  }))
}

function onWeightChange(row, value) {
  row.targetWeight = normalizeWeight(value)
}

function validateAiUploadFile(file) {
  const fileName = String(file?.name || '').toLowerCase()
  if (!fileName.endsWith('.pdf') && !fileName.endsWith('.doc') && !fileName.endsWith('.docx')) {
    ElMessage.warning('仅支持上传 PDF、DOC、DOCX 文件。')
    return false
  }
  const fileSize = Number(file?.size || 0)
  if (fileSize <= 0) {
    ElMessage.warning('上传文件不能为空。')
    return false
  }
  if (fileSize > 10 * 1024 * 1024) {
    ElMessage.warning('上传文件不能超过 10MB。')
    return false
  }
  return true
}

function onAiUploadChange(uploadFile) {
  const rawFile = uploadFile?.raw || null
  if (!rawFile || !validateAiUploadFile(rawFile)) {
    aiUploadFile.value = null
    aiUploadFileList.value = []
    return
  }
  aiUploadFile.value = rawFile
  aiUploadFileList.value = [uploadFile]
}

function onAiUploadRemove() {
  aiUploadFile.value = null
  aiUploadFileList.value = []
}

function onAiUploadExceed(files) {
  const latest = Array.isArray(files) && files.length ? files[files.length - 1] : null
  if (!latest) {
    return
  }
  onAiUploadChange({ raw: latest, name: latest.name, size: latest.size })
}

async function submitAiParse() {
  if (!selectedVersionId.value) {
    ElMessage.warning('请先选择要解析的大纲版本。')
    return
  }
  if (!aiUploadFile.value) {
    ElMessage.warning('请先上传要解析的大纲文件。')
    return
  }
  if (!validateAiUploadFile(aiUploadFile.value)) {
    return
  }
  parsing.value = true
  try {
    const payload = await parseSyllabusWithAi(selectedVersionId.value, aiUploadFile.value)
    const prefilledRows = cloneIncomingWeights(payload?.knowledgeWeights)
    if (!prefilledRows.length) {
      ElMessage.warning('AI 未生成可预填结果，请检查文件内容后重试。')
      return
    }
    tableRows.value = prefilledRows
    aiParserReport.value = payload?.parserReport || null
    ElMessage.success('AI 解析完成，结果已预填到权重表，请确认后保存。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || 'AI 大纲解析失败'))
  } finally {
    parsing.value = false
  }
}

async function submitSaveWeights() {
  if (!selectedVersionId.value) {
    ElMessage.warning('请先选择一个大纲版本。')
    return
  }
  if (!tableRows.value.length) {
    ElMessage.warning('当前版本没有可编辑的知识点。')
    return
  }
  if (!isWeightTotalValid.value) {
    ElMessage.warning(`当前 target_weight 总和为 ${totalWeight.value.toFixed(6)}，必须等于 1.000000。`)
    return
  }
  saving.value = true
  try {
    const payload = await saveSyllabusWeights(
      selectedVersionId.value,
      tableRows.value.map((item) => ({
        knowledgeId: item.knowledgeId,
        targetWeight: normalizeWeight(item.targetWeight),
      })),
    )
    applySyllabusPayload(payload)
    ElMessage.success('知识点权重已保存。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '知识点权重保存失败'))
  } finally {
    saving.value = false
  }
}

watch(selectedVersionId, () => {
  aiParserReport.value = null
  syncRowsBySelectedVersion()
})

onMounted(() => {
  loadSyllabusData()
})
</script>

<template>
  <section class="syllabus-shell" v-loading="loading">
    <header class="page-header">
      <h3>大纲仓库</h3>
      <p>创建大纲版本并批量维护知识点 target_weight，确保同版本总和为 1.0。</p>
    </header>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>创建版本</span>
          <el-tag type="info" effect="light">版本数：{{ versions.length }}</el-tag>
        </div>
      </template>
      <div class="create-grid">
        <el-form label-position="top" class="create-form">
          <el-form-item label="版本名称">
            <el-input
              v-model="createForm.versionName"
              maxlength="80"
              placeholder="例如：2026 冲刺阶段大纲"
              clearable
            />
          </el-form-item>
          <el-form-item label="复制来源（可选）">
            <el-select
              v-model="createForm.copyFromVersionId"
              placeholder="不选则按知识点自动平均初始化"
              clearable
            >
              <el-option
                v-for="item in versions"
                :key="item.versionId"
                :label="item.versionName"
                :value="item.versionId"
              />
            </el-select>
          </el-form-item>
          <el-button type="primary" :loading="creating" @click="submitCreateVersion">创建大纲版本</el-button>
        </el-form>

        <el-form label-position="top" class="select-form">
          <el-form-item label="当前编辑版本">
            <el-select v-model="selectedVersionId" placeholder="请选择大纲版本" clearable>
              <el-option
                v-for="item in versions"
                :key="item.versionId"
                :label="item.versionName"
                :value="item.versionId"
              />
            </el-select>
          </el-form-item>
          <div class="version-meta" v-if="selectedVersion">
            <span>创建时间：{{ selectedVersion.createTime || '-' }}</span>
            <span>更新时间：{{ selectedVersion.updateTime || '-' }}</span>
          </div>
        </el-form>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>AI 大纲解析器</span>
          <el-tag type="warning" effect="light">解析结果仅预填，仍需人工确认</el-tag>
        </div>
      </template>
      <div class="ai-parser-grid">
        <el-upload
          class="ai-upload"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".pdf,.doc,.docx"
          :file-list="aiUploadFileList"
          :on-change="onAiUploadChange"
          :on-remove="onAiUploadRemove"
          :on-exceed="onAiUploadExceed"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            将 PDF / Word 大纲拖拽到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、DOC、DOCX，单文件最大 10MB。系统将先做 OCR，再用 AI 提取知识点建议权重。
            </div>
          </template>
        </el-upload>

        <div class="ai-actions">
          <el-button type="primary" :loading="parsing" :disabled="!selectedVersionId" @click="submitAiParse">
            AI 解析并预填
          </el-button>
          <p>建议流程：选择版本 -> 上传文件 -> AI 预填 -> 人工微调 -> 保存权重。</p>
          <el-descriptions v-if="aiParserReport" :column="1" border size="small">
            <el-descriptions-item label="解析模式">
              {{ aiParserReport.parserMode || '-' }} {{ aiParserReport.model ? `(${aiParserReport.model})` : '' }}
            </el-descriptions-item>
            <el-descriptions-item label="文本提取方式">
              {{ aiParserReport.extractMethod || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="文本长度">
              {{ aiParserReport.extractTextLength || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="匹配结果">
              已匹配 {{ aiParserReport.matchedCount || 0 }} 条，未匹配 {{ aiParserReport.unmatchedCount || 0 }} 条
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识点权重批量编辑</span>
          <div class="action-group">
            <el-tag :type="isWeightTotalValid ? 'success' : 'danger'" effect="dark">
              总和：{{ totalWeight.toFixed(6) }}
            </el-tag>
            <el-button @click="rebalanceToAverage">一键平均分配</el-button>
            <el-button type="primary" :loading="saving" :disabled="!selectedVersionId" @click="submitSaveWeights">
              保存权重
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="tableRows.length && !isWeightTotalValid"
        class="sum-alert"
        type="error"
        :closable="false"
        show-icon
        :title="`同版本 target_weight 总和必须等于 1.0，当前为 ${totalWeight.toFixed(6)}。`"
      />

      <el-empty v-if="!tableRows.length" description="当前版本暂无可编辑知识点" />
      <el-table v-else :data="tableRows" border>
        <el-table-column type="index" label="#" width="64" />
        <el-table-column prop="knowledgeName" label="知识点" min-width="220" />
        <el-table-column prop="knowledgeId" label="知识点ID" min-width="180" />
        <el-table-column label="target_weight" width="220">
          <template #default="scope">
            <el-input-number
              :model-value="scope.row.targetWeight"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="6"
              controls-position="right"
              @change="(value) => onWeightChange(scope.row, value)"
            />
          </template>
        </el-table-column>
        <el-table-column label="权重占比" width="140">
          <template #default="scope">
            {{ (Number(scope.row.targetWeight || 0) * 100).toFixed(2) }}%
          </template>
        </el-table-column>
      </el-table>
    </el-card>

  </section>
</template>

<style scoped>
.syllabus-shell {
  display: grid;
  gap: 12px;
}

.page-header h3,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.create-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.create-form,
.select-form {
  display: grid;
  gap: 8px;
}

.version-meta {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--qb-text-subtle-6);
}

.action-group {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.ai-parser-grid {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(280px, 1fr);
  gap: 14px;
  align-items: start;
}

.ai-upload {
  width: 100%;
}

.ai-actions {
  display: grid;
  gap: 10px;
}

.ai-actions p {
  margin: 0;
  font-size: 13px;
  color: var(--qb-text-subtle-6);
}

.sum-alert {
  margin-bottom: 12px;
}

@media (max-width: 900px) {
  .card-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .action-group {
    flex-wrap: wrap;
  }

  .ai-parser-grid {
    grid-template-columns: 1fr;
  }
}
</style>
