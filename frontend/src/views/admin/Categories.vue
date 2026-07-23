<template>
  <div class="admin-categories">
    <h2>分类配置</h2>
    <el-alert type="info" :closable="false" style="margin-bottom: 20px">
      管理单元、业务模块、性质、症状、原因、解决方法的配置。这些配置将在ITSM系统中使用。
    </el-alert>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="管理单元" name="categories">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>管理单元</span>
              <el-button type="primary" size="small" @click="openDialog('categories')">新增</el-button>
            </div>
          </template>
          <el-table :data="categories" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="sla_hours" label="SLA(小时)" width="100" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '启用' : '禁用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('categories', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('categories', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="业务模块" name="modules">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>业务模块</span>
              <el-button type="primary" size="small" @click="openDialog('modules')">新增</el-button>
            </div>
          </template>
          <el-table :data="modules" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column label="所属管理单元" width="120">
              <template #default="{ row }">{{ categories.find(c => c.id === row.category_id)?.name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '启用' : '禁用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('modules', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('modules', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="性质" name="properties">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>性质</span>
              <el-button type="primary" size="small" @click="openDialog('properties')">新增</el-button>
            </div>
          </template>
          <el-table :data="properties" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('properties', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('properties', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="症状" name="symptoms">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>症状</span>
              <el-button type="primary" size="small" @click="openDialog('symptoms')">新增</el-button>
            </div>
          </template>
          <el-table :data="symptoms" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('symptoms', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('symptoms', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="原因" name="causes">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>原因</span>
              <el-button type="primary" size="small" @click="openDialog('causes')">新增</el-button>
            </div>
          </template>
          <el-table :data="causes" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('causes', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('causes', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="解决方法" name="solutions">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>解决方法</span>
              <el-button type="primary" size="small" @click="openDialog('solutions')">新增</el-button>
            </div>
          </template>
          <el-table :data="solutions" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDialog('solutions', row)">编辑</el-button>
                <el-popconfirm title="确认删除？" @confirm="deleteItem('solutions', row.id)">
                  <template #reference><el-button type="danger" link size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 通用对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="formData.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="formData.description" type="textarea" /></el-form-item>
        <el-form-item label="所属管理单元" v-if="currentType === 'modules'">
          <el-select v-model="formData.category_id" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="SLA(小时)" v-if="currentType === 'categories'">
          <el-input-number v-model="formData.sla_hours" :min="1" :max="720" />
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="formData.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api'

const activeTab = ref('categories')
const categories = ref([])
const modules = ref([])
const properties = ref([])
const symptoms = ref([])
const causes = ref([])
const solutions = ref([])

const dialogVisible = ref(false)
const currentType = ref('')
const editingId = ref(null)
const saving = ref(false)

const formData = reactive({ name: '', description: '', sla_hours: 4, sort_order: 0, category_id: null })

const dialogTitle = computed(() => {
  const names = { categories: '管理单元', modules: '业务模块', properties: '性质', symptoms: '症状', causes: '原因', solutions: '解决方法' }
  return `${editingId.value ? '编辑' : '新增'}${names[currentType.value] || ''}`
})

onMounted(() => loadAll())

async function loadAll() {
  const [cats, mods, props, symp, caus, sol] = await Promise.all([
    adminApi.getCategories(), adminApi.getBusinessModules(),
    adminApi.getProperties(), adminApi.getSymptoms(),
    adminApi.getCauses(), adminApi.getSolutions(),
  ])
  categories.value = cats || []
  modules.value = mods || []
  properties.value = props || []
  symptoms.value = symp || []
  causes.value = caus || []
  solutions.value = sol || []
}

function openDialog(type, item = null) {
  currentType.value = type
  editingId.value = item?.id || null
  formData.name = item?.name || ''
  formData.description = item?.description || ''
  formData.sla_hours = item?.sla_hours || 4
  formData.sort_order = item?.sort_order || 0
  formData.category_id = item?.category_id || null
  dialogVisible.value = true
}

async function handleSave() {
  if (!formData.name) { ElMessage.warning('请输入名称'); return }
  saving.value = true
  try {
    const apiMap = {
      categories: { create: adminApi.createCategory, update: adminApi.updateCategory },
      modules: { create: adminApi.createBusinessModule, update: adminApi.updateBusinessModule },
      properties: { create: adminApi.createProperty, update: adminApi.updateProperty },
      symptoms: { create: adminApi.createSymptom, update: adminApi.updateSymptom },
      causes: { create: adminApi.createCause, update: adminApi.updateCause },
      solutions: { create: adminApi.createSolution, update: adminApi.updateSolution },
    }
    const apis = apiMap[currentType.value]
    if (editingId.value) { await apis.update(editingId.value, formData) }
    else { await apis.create(formData) }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadAll()
  } finally { saving.value = false }
}

async function deleteItem(type, id) {
  const apiMap = {
    categories: adminApi.deleteCategory, modules: adminApi.deleteBusinessModule,
    properties: adminApi.deleteProperty, symptoms: adminApi.deleteSymptom,
    causes: adminApi.deleteCause, solutions: adminApi.deleteSolution,
  }
  try { await apiMap[type](id); ElMessage.success('删除成功'); await loadAll() } catch (e) {}
}
</script>

<style scoped>
h2 { margin-bottom: 16px; }
</style>
