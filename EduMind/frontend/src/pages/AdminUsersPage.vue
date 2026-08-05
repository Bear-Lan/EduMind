<template>
  <div class="users-page">
    <header class="admin-header">
      <div><div class="brand">🛡️ EduMind 管理中心</div><p>学生账户、状态和密码维护</p></div>
      <nav><button @click="router.push('/admin')">模型配置</button><button class="active">用户管理</button><EduButton variant="ghost" size="sm" @click="logout">退出</EduButton></nav>
    </header>

    <main class="users-content">
      <div class="page-title"><div><span class="eyebrow">STUDENT ACCOUNTS</span><h1>学生账户管理</h1><p>可以修改资料、停用异常账户，或为忘记密码的学生设置临时密码。</p></div><strong>{{ total }} 个账户</strong></div>
      <div v-if="message" class="message" :class="messageType">{{ message }}</div>
      <div class="toolbar"><input v-model="search" placeholder="搜索用户名或姓名" @keyup.enter="loadStudents(1)"><button @click="loadStudents(1)">搜索</button></div>

      <div class="table-card">
        <table>
          <thead><tr><th>学生</th><th>年级 / 学科</th><th>目标分数</th><th>注册时间</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="student in students" :key="student.id">
              <td><strong>{{ student.name }}</strong><span>@{{ student.username }} · ID {{ student.id }}</span></td>
              <td>{{ student.grade || '未填写' }} / {{ student.subject || '未填写' }}</td>
              <td>{{ student.target_score ?? '—' }}</td>
              <td>{{ formatDate(student.created_at) }}</td>
              <td><span class="status" :class="student.is_active ? 'ok' : 'off'">{{ student.is_active ? '正常' : '已停用' }}</span><small v-if="student.must_change_password">待修改密码</small></td>
              <td class="actions"><button @click="openEdit(student)">编辑</button><button @click="openReset(student)">重置密码</button><button :class="student.is_active ? 'danger' : 'enable'" @click="toggleStatus(student)">{{ student.is_active ? '停用' : '启用' }}</button></td>
            </tr>
            <tr v-if="!loading && students.length === 0"><td colspan="6" class="empty">没有找到符合条件的学生账户</td></tr>
          </tbody>
        </table>
        <div v-if="loading" class="loading">正在读取账户...</div>
      </div>
      <div class="pagination"><button :disabled="page <= 1" @click="loadStudents(page - 1)">上一页</button><span>第 {{ page }} / {{ totalPages }} 页</span><button :disabled="page >= totalPages" @click="loadStudents(page + 1)">下一页</button></div>
    </main>

    <div v-if="editStudent" class="modal-backdrop" @click.self="editStudent = null">
      <form class="modal" @submit.prevent="saveStudent"><h2>编辑学生资料</h2><label>用户名<input v-model="editStudent.username" required></label><label>姓名<input v-model="editStudent.name" required></label><div class="two"><label>年级<input v-model="editStudent.grade"></label><label>学科<input v-model="editStudent.subject"></label></div><label>目标分数<input v-model.number="editStudent.target_score" type="number" min="0" max="100"></label><div class="modal-actions"><button type="button" @click="editStudent = null">取消</button><button class="primary" type="submit">保存</button></div></form>
    </div>

    <div v-if="resetStudent" class="modal-backdrop" @click.self="closeReset">
      <form class="modal" @submit.prevent="resetPassword"><h2>重置 {{ resetStudent.name }} 的密码</h2><p>请输入至少8位的临时密码。学生下次登录后会看到修改密码提醒。</p><label>临时密码<input v-model="temporaryPassword" type="password" minlength="8" required></label><label>确认临时密码<input v-model="temporaryPasswordConfirm" type="password" minlength="8" required></label><div class="modal-actions"><button type="button" @click="closeReset">取消</button><button class="primary" type="submit">确认重置</button></div></form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../utils/api';
import { useAuthStore } from '../stores/auth';
import EduButton from '../components/EduButton.vue';

const router = useRouter();
const authStore = useAuthStore();
const students = ref([]); const total = ref(0); const page = ref(1); const pageSize = 20;
const search = ref(''); const loading = ref(false); const editStudent = ref(null); const resetStudent = ref(null);
const temporaryPassword = ref(''); const temporaryPasswordConfirm = ref('');
const message = ref(''); const messageType = ref('success');
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));

onMounted(() => loadStudents(1));
function showMessage(text, type = 'success') { message.value = text; messageType.value = type; window.setTimeout(() => { if (message.value === text) message.value = ''; }, 5000); }
async function loadStudents(targetPage = 1) { loading.value = true; try { const response = await api.get('/admin/students', { params: { search: search.value, page: targetPage, page_size: pageSize } }); students.value = response.data.items; total.value = response.data.total; page.value = response.data.page; } catch (error) { showMessage(error.message || '学生账户读取失败', 'error'); } finally { loading.value = false; } }
function openEdit(student) { editStudent.value = { ...student }; }
async function saveStudent() { try { const response = await api.put(`/admin/students/${editStudent.value.id}`, editStudent.value); const index = students.value.findIndex(item => item.id === response.data.id); if (index >= 0) students.value[index] = response.data; editStudent.value = null; showMessage('学生资料已更新'); } catch (error) { showMessage(error.message || '学生资料更新失败', 'error'); } }
function openReset(student) { resetStudent.value = student; temporaryPassword.value = ''; temporaryPasswordConfirm.value = ''; }
function closeReset() { resetStudent.value = null; temporaryPassword.value = ''; temporaryPasswordConfirm.value = ''; }
async function resetPassword() { if (temporaryPassword.value.length < 8) return showMessage('临时密码至少需要8位', 'error'); if (temporaryPassword.value !== temporaryPasswordConfirm.value) return showMessage('两次输入的临时密码不一致', 'error'); try { await api.put(`/admin/students/${resetStudent.value.id}/password`, { new_password: temporaryPassword.value }); const item = students.value.find(student => student.id === resetStudent.value.id); if (item) item.must_change_password = true; closeReset(); showMessage('临时密码已重置，请单独告知学生'); } catch (error) { showMessage(error.message || '密码重置失败', 'error'); } }
async function toggleStatus(student) { const action = student.is_active ? '停用' : '启用'; if (!window.confirm(`确定${action}学生“${student.name}”的账户吗？`)) return; try { const response = await api.put(`/admin/students/${student.id}/status`, { is_active: !student.is_active }); Object.assign(student, response.data); showMessage(`账户已${action}`); } catch (error) { showMessage(error.message || `${action}失败`, 'error'); } }
function formatDate(value) { return value ? new Date(value).toLocaleDateString('zh-CN') : '—'; }
function logout() { authStore.logout(); router.push('/admin-login'); }
</script>

<style scoped>
.users-page { min-height: 100vh; background: #080a16; color: var(--text-primary); }
.admin-header { min-height: 76px; padding: 14px 32px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); background: rgba(12,14,29,.9); }
.brand { color: white; font-size: 20px; font-weight: 800; }.admin-header p { margin: 4px 0 0; color: var(--text-secondary); font-size: 12px; }.admin-header nav { display: flex; align-items: center; gap: 8px; }.admin-header nav > button { border: 1px solid transparent; background: transparent; color: var(--text-secondary); padding: 8px 11px; border-radius: 8px; cursor: pointer; }.admin-header nav > button.active { color: #c4b5fd; background: rgba(99,102,241,.14); border-color: rgba(99,102,241,.25); }
.users-content { width: min(1240px, calc(100% - 40px)); margin: 0 auto; padding: 30px 0 56px; }.page-title { display: flex; justify-content: space-between; align-items: end; margin-bottom: 22px; }.page-title h1 { color: white; margin: 5px 0; }.page-title p { color: var(--text-secondary); margin: 0; }.page-title > strong { color: #a5b4fc; }.eyebrow { color: #818cf8; font-size: 10px; letter-spacing: 1.2px; }
.message { padding: 12px 16px; border-radius: 10px; margin-bottom: 14px; }.message.success { color: #a7f3d0; background: rgba(16,185,129,.12); }.message.error { color: #fecaca; background: rgba(239,68,68,.12); }
.toolbar { display: flex; gap: 10px; margin-bottom: 14px; }.toolbar input { width: min(380px, 70vw); }.toolbar input, .modal input { background: #0d1022; color: white; border: 1px solid rgba(255,255,255,.11); border-radius: 9px; padding: 10px 12px; }.toolbar button, .pagination button, .actions button, .modal-actions button { border: 1px solid rgba(255,255,255,.1); border-radius: 8px; background: rgba(255,255,255,.05); color: var(--text-secondary); padding: 8px 10px; cursor: pointer; }
.table-card { position: relative; overflow-x: auto; border: 1px solid rgba(255,255,255,.08); border-radius: 14px; background: rgba(18,22,46,.72); }table { width: 100%; border-collapse: collapse; }th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(255,255,255,.06); font-size: 13px; }th { color: var(--text-secondary); font-size: 11px; letter-spacing: .4px; }td strong, td span { display: block; }td > span { color: var(--text-secondary); font-size: 11px; margin-top: 4px; }.status { display: inline-block; width: max-content; padding: 4px 8px; border-radius: 999px; }.status.ok { color: #a7f3d0; background: rgba(16,185,129,.13); }.status.off { color: #fecaca; background: rgba(239,68,68,.13); }td small { display: block; margin-top: 5px; color: #fde68a; }.actions { white-space: nowrap; }.actions button { margin-right: 5px; font-size: 11px; }.actions .danger { color: #fca5a5; }.actions .enable { color: #a7f3d0; }.empty, .loading { text-align: center; color: var(--text-secondary); padding: 30px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 14px; margin-top: 16px; color: var(--text-secondary); font-size: 12px; }.pagination button:disabled { opacity: .35; cursor: not-allowed; }
.modal-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; background: rgba(0,0,0,.72); padding: 20px; }.modal { width: min(480px, 100%); padding: 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,.1); background: #12162e; box-shadow: 0 25px 70px rgba(0,0,0,.5); }.modal h2 { color: white; margin: 0 0 8px; }.modal p { color: var(--text-secondary); font-size: 13px; line-height: 1.6; }.modal label { display: grid; gap: 6px; margin-top: 13px; color: var(--text-secondary); font-size: 12px; }.two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 22px; }.modal-actions .primary { color: white; background: #6366f1; }
@media (max-width: 760px) { .admin-header { padding: 12px 16px; }.admin-header > div p { display: none; }.users-content { width: calc(100% - 24px); }.page-title p { display: none; }.actions button { display: block; width: 100%; margin: 4px 0; } }
</style>
