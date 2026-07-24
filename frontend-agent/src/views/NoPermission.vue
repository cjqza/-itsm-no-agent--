<template>
  <div class="no-permission">
    <el-result icon="warning" title="暂无权限" sub-title="您当前没有ITSM工单系统访问权限，请申请权限后重试">
      <template #extra>
        <el-button type="primary" @click="showRequestDialog = true">申请权限</el-button>
        <el-button @click="router.push('/login')">重新登录</el-button>
      </template>
    </el-result>

    <el-dialog v-model="showRequestDialog" title="申请权限" width="500px">
      <el-form :model="requestForm">
        <el-form-item label="申请理由">
          <el-input v-model="requestForm.reason" type="textarea" placeholder="请输入申请理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRequestDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRequest">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api'

const router = useRouter()
const showRequestDialog = ref(false)
const requestForm = reactive({
  reason: '',
})

async function submitRequest() {
  try {
    await adminApi.createPermissionRequest({
      request_type: 'itsm',
      reason: requestForm.reason,
    })
    ElMessage.success('权限申请已提交，请等待管理员审批')
    showRequestDialog.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  }
}
</script>

<style scoped>
.no-permission {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}
</style>
