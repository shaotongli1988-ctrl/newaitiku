<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useUserStore } from '../../stores/userStore.js'
import { buildContentLabelMaps, resolveContentLabel } from '../../utils/contentBaseline.js'
import {
  exportManagedStudentsDirectory,
  fetchManagedUsersPage,
  importManagedStudents,
  saveManagedUserRecord,
} from '../../api/services/questionBank'

const userStore = useUserStore()

const loading = ref(true)
const managedUsersLoading = ref(false)
const savingUser = ref(false)
const importing = ref(false)
const exporting = ref(false)
const editingUserId = ref('')
const importSummary = ref(null)
const exportPreview = ref('')
const exportFormat = ref('csv')
const managedUsers = ref([])
const managedUsersTotal = ref(0)

const managedUserForm = reactive(createManagedUserForm())
const managedUserQuery = reactive({
  keyword: '',
  page: 1,
  size: 20,
})
const importForm = reactive({
  csvText: [
    'userId,name,mobile,examCategoryCode,jointExamGroupCode,vocationalMajor,prepStage',
    'student-003,管理考生,13800000007,MANAGEMENT,MANAGEMENT_1,财经商贸类,基础阶段',
  ].join('\n'),
})

const canManageStudents = computed(() => userStore.hasPermission('student:manage'))
const assignedJointGroupCode = computed(() =>
  String(userStore.assigned_joint_group_code || userStore.jointExamGroupCode || '').trim(),
)
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const resolveExamCategoryLabel = (code) => resolveContentLabel(scopeLabelMaps.value.examCategoryNameMap, code)
const resolveJointExamGroupLabel = (code) => resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, code)
const scopeDescription = computed(() =>
  assignedJointGroupCode.value
    ? `当前账号已绑定专业组 ${resolveJointExamGroupLabel(assignedJointGroupCode.value)}，学生账号开通仅对该范围生效。`
    : '当前账号未绑定单一专业组，学生账号开通按你当前可管理范围执行。',
)
const totalManagedUserPages = computed(() => Math.max(1, Math.ceil(managedUsersTotal.value / managedUserQuery.size)))

function createManagedUserForm() {
  return {
    userId: '',
    name: '',
    mobile: '',
    enabled: true,
    examCategoryCode: '',
    jointExamGroupCode: '',
    vocationalMajor: '',
    prepStage: '',
  }
}

function resetManagedUserForm() {
  Object.assign(managedUserForm, createManagedUserForm())
  editingUserId.value = ''
}

function populateManagedUserForm(user) {
  Object.assign(managedUserForm, {
    userId: String(user?.userId || ''),
    name: String(user?.name || ''),
    mobile: String(user?.mobile || ''),
    enabled: Boolean(user?.enabled),
    examCategoryCode: String(user?.examCategoryCode || ''),
    jointExamGroupCode: String(user?.jointExamGroupCode || ''),
    vocationalMajor: String(user?.vocationalMajor || ''),
    prepStage: String(user?.prepStage || ''),
  })
  editingUserId.value = managedUserForm.userId
}

function validateManagedUserForm() {
  if (!String(managedUserForm.userId || '').trim()) {
    throw new Error('请填写学生用户ID。')
  }
  if (!String(managedUserForm.name || '').trim()) {
    throw new Error('请填写学生姓名。')
  }
  if (!/^1\d{10}$/.test(String(managedUserForm.mobile || '').trim())) {
    throw new Error('mobile 必须是合法中国大陆手机号。')
  }
  if (!String(managedUserForm.examCategoryCode || '').trim() || !String(managedUserForm.jointExamGroupCode || '').trim()) {
    throw new Error('学生账号必须填写学科门类与联考专业组。')
  }
}

async function loadManagedUsers() {
  managedUsersLoading.value = true
  try {
    const pageData = await fetchManagedUsersPage({
      role: 'student',
      keyword: managedUserQuery.keyword,
      page: managedUserQuery.page,
      size: managedUserQuery.size,
    })
    managedUsers.value = Array.isArray(pageData.items) ? pageData.items : []
    managedUsersTotal.value = Number(pageData.total || 0)
    managedUserQuery.page = Number(pageData.page || managedUserQuery.page)
    managedUserQuery.size = Number(pageData.size || managedUserQuery.size)
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '学生账号列表加载失败'))
  } finally {
    managedUsersLoading.value = false
  }
}

async function loadPage() {
  loading.value = true
  try {
    await loadManagedUsers()
  } finally {
    loading.value = false
  }
}

async function submitManagedUser() {
  if (savingUser.value) {
    return
  }
  try {
    validateManagedUserForm()
  } catch (error) {
    ElMessage.warning(String(error?.message || error))
    return
  }
  savingUser.value = true
  try {
    await saveManagedUserRecord({
      userId: managedUserForm.userId,
      role: 'student',
      name: managedUserForm.name,
      mobile: managedUserForm.mobile,
      enabled: Boolean(managedUserForm.enabled),
      permissions: [],
      examCategoryCode: managedUserForm.examCategoryCode,
      jointExamGroupCode: managedUserForm.jointExamGroupCode,
      vocationalMajor: managedUserForm.vocationalMajor,
      prepStage: managedUserForm.prepStage,
    })
    resetManagedUserForm()
    managedUserQuery.page = 1
    await loadManagedUsers()
    ElMessage.success('学生账号已更新。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '学生账号保存失败'))
  } finally {
    savingUser.value = false
  }
}

async function submitImport() {
  if (importing.value) {
    return
  }
  if (!String(importForm.csvText || '').trim()) {
    ElMessage.warning('请先填写导入模板内容。')
    return
  }
  importing.value = true
  try {
    importSummary.value = await importManagedStudents({ csvText: importForm.csvText })
    managedUserQuery.page = 1
    await loadManagedUsers()
    ElMessage.success('学生账号批量导入已执行。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '学生账号导入失败'))
  } finally {
    importing.value = false
  }
}

async function handleExport() {
  if (exporting.value) {
    return
  }
  exporting.value = true
  try {
    const result = await exportManagedStudentsDirectory({ format: exportFormat.value })
    exportPreview.value = String(result?.content || '')
    ElMessage.success('学生账号目录已导出。')
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '学生账号导出失败'))
  } finally {
    exporting.value = false
  }
}

async function refreshManagedUsers() {
  managedUserQuery.page = 1
  await loadManagedUsers()
}

async function handlePageChange(page) {
  managedUserQuery.page = Number(page || 1)
  await loadManagedUsers()
}

async function handlePageSizeChange(size) {
  managedUserQuery.size = Number(size || 20)
  managedUserQuery.page = 1
  await loadManagedUsers()
}

onMounted(() => {
  loadPage()
})
</script>

<template>
  <section class="page-shell" v-loading="loading">
    <el-card class="hero-card" shadow="never">
      <div class="hero-top">
        <div>
          <p class="eyebrow">Student Provisioning</p>
          <h3>学生账号开通</h3>
          <p class="hero-copy">{{ scopeDescription }}</p>
        </div>
        <el-button @click="refreshManagedUsers">刷新列表</el-button>
      </div>
      <div class="hero-meta">
        <article>
          <span>当前学生总数</span>
          <strong>{{ managedUsersTotal }}</strong>
        </article>
        <article>
          <span>当前页记录</span>
          <strong>{{ managedUsers.length }}</strong>
        </article>
        <article>
          <span>权限状态</span>
          <strong>{{ canManageStudents ? '已开通' : '未开通' }}</strong>
        </article>
      </div>
    </el-card>

    <section class="content-grid">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>{{ editingUserId ? `编辑学生 ${editingUserId}` : '新增学生账号' }}</span>
            <div class="inline-actions">
              <el-button v-if="editingUserId" @click="resetManagedUserForm">取消编辑</el-button>
              <el-button type="primary" :loading="savingUser" @click="submitManagedUser">
                保存学生账号
              </el-button>
            </div>
          </div>
        </template>
        <el-form label-position="top">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="用户ID">
                <el-input v-model="managedUserForm.userId" :disabled="Boolean(editingUserId)" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="手机号">
                <el-input v-model="managedUserForm.mobile" maxlength="11" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="姓名">
                <el-input v-model="managedUserForm.name" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="账号状态">
                <el-switch
                  v-model="managedUserForm.enabled"
                  inline-prompt
                  active-text="启用"
                  inactive-text="停用"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="学科门类">
                <el-input v-model="managedUserForm.examCategoryCode" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联考专业组">
                <el-input v-model="managedUserForm.jointExamGroupCode" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="高职专业">
                <el-input v-model="managedUserForm.vocationalMajor" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="备考阶段">
                <el-input v-model="managedUserForm.prepStage" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>批量导入导出</span>
            <div class="inline-actions">
              <el-select v-model="exportFormat" class="export-select">
                <el-option label="CSV 格式" value="csv" />
                <el-option label="PDF 目录文本" value="pdf" />
              </el-select>
              <el-button :loading="exporting" @click="handleExport">导出目录</el-button>
            </div>
          </div>
        </template>
        <el-form label-position="top">
          <el-form-item label="导入模板">
            <el-input v-model="importForm.csvText" type="textarea" :rows="8" />
          </el-form-item>
          <div class="inline-actions">
            <el-button type="primary" :loading="importing" @click="submitImport">批量导入学生</el-button>
          </div>
        </el-form>
        <el-alert
          v-if="importSummary"
          class="feedback-block"
          type="success"
          :closable="false"
          show-icon
          :title="`导入完成：成功 ${importSummary.imported || 0} 条，失败 ${importSummary.failed || 0} 条。`"
        />
        <pre v-if="importSummary" class="result-block">{{ JSON.stringify(importSummary, null, 2) }}</pre>
        <pre v-if="exportPreview" class="result-block">{{ exportPreview }}</pre>
      </el-card>
    </section>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>学生账号目录</span>
          <div class="inline-actions">
            <el-input
              v-model="managedUserQuery.keyword"
              clearable
              placeholder="搜索 userId / 姓名 / 手机号"
              @keyup.enter="refreshManagedUsers"
            />
            <el-button :loading="managedUsersLoading" @click="refreshManagedUsers">刷新列表</el-button>
          </div>
        </div>
      </template>

      <el-table :data="managedUsers" border v-loading="managedUsersLoading">
        <el-table-column prop="userId" label="用户ID" min-width="140" />
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="mobile" label="手机号" width="140" />
        <el-table-column label="状态" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'info'" effect="light">
              {{ scope.row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="范围信息" min-width="220">
          <template #default="scope">
            <span>{{ resolveExamCategoryLabel(scope.row.examCategoryCode) }} / {{ resolveJointExamGroupLabel(scope.row.jointExamGroupCode) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="vocationalMajor" label="高职专业" min-width="160" />
        <el-table-column prop="prepStage" label="备考阶段" min-width="130" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="populateManagedUserForm(scope.row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <span class="helper-text">第 {{ managedUserQuery.page }} / {{ totalManagedUserPages }} 页，共 {{ managedUsersTotal }} 条</span>
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="managedUserQuery.page"
          :page-size="managedUserQuery.size"
          :page-sizes="[10, 20, 50]"
          :total="managedUsersTotal"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>
  </section>
</template>

<style scoped>
.page-shell {
  display: grid;
  gap: 16px;
}

.hero-card {
  border-color: var(--qb-primary-soft-border);
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(14, 116, 144, 0.08), rgba(255, 255, 255, 0.96));
}

.hero-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--qb-text-subtle-7);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h3,
p {
  margin: 0;
}

h3 {
  font-size: 28px;
  color: var(--qb-text-heading);
}

.hero-copy {
  margin-top: 10px;
  max-width: 720px;
  color: var(--qb-text-subtle-6);
  line-height: 1.7;
}

.hero-meta {
  margin-top: 18px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.hero-meta article {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--qb-primary-soft-border);
  background: rgba(255, 255, 255, 0.76);
  display: grid;
  gap: 8px;
}

.hero-meta span {
  color: var(--qb-text-subtle-6);
  font-size: 13px;
}

.hero-meta strong {
  font-size: 24px;
  color: var(--qb-text-heading);
}

.content-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.inline-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.export-select {
  width: 150px;
}

.feedback-block {
  margin-top: 12px;
}

.result-block {
  margin: 12px 0 0;
  padding: 12px;
  border-radius: 10px;
  background: var(--qb-bg-card);
  border: 1px solid var(--qb-border-muted);
  max-height: 260px;
  overflow: auto;
}

.pagination-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.helper-text {
  color: var(--qb-text-subtle-6);
  font-size: 13px;
}

@media (max-width: 900px) {
  .hero-top,
  .card-header,
  .pagination-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
