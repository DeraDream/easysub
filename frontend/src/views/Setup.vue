<template>
  <div class="auth-wrap">
    <div class="card setup-card">
      <h2>🗄️ {{ t('setup.title') }}</h2>
      <p class="muted">{{ t('setup.subtitle') }}</p>

      <div class="row">
        <div style="flex:2">
          <label>{{ t('setup.host') }}</label>
          <input v-model="cfg.host" placeholder="db / 192.168.1.10" />
        </div>
        <div style="flex:1">
          <label>{{ t('setup.port') }}</label>
          <input v-model.number="cfg.port" type="number" />
        </div>
      </div>
      <div class="row">
        <div style="flex:1">
          <label>{{ t('setup.user') }}</label>
          <input v-model="cfg.user" placeholder="root / easysub" />
        </div>
        <div style="flex:1">
          <label>{{ t('setup.password') }}</label>
          <input v-model="cfg.password" type="password" />
        </div>
      </div>
      <label>{{ t('setup.database') }}</label>
      <input v-model="cfg.database" placeholder="easysub" />

      <p class="tip">{{ t('setup.tip') }}</p>

      <p v-if="msg" :class="ok ? 'ok' : 'err'">{{ msg }}</p>

      <div class="row" style="margin-top:16px">
        <button class="btn ghost" style="flex:1" :disabled="busy" @click="testConn">
          {{ testing ? t('setup.testing') : t('setup.test') }}
        </button>
        <button class="btn" style="flex:1" :disabled="busy || !ok" @click="save">
          {{ saving ? t('setup.saving') : t('setup.save') }}
        </button>
      </div>

      <div class="lang">
        <a href="#" @click.prevent="setLang('zh')">中文</a> ·
        <a href="#" @click.prevent="setLang('en')">EN</a> ·
        <a href="#" @click.prevent="setLang('ru')">RU</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t, locale } = useI18n()
const cfg = reactive({ host: 'db', port: 3306, user: 'root', password: '', database: 'easysub' })
const msg = ref('')
const ok = ref(false)
const testing = ref(false)
const saving = ref(false)
const busy = ref(false)

function setLang(l) { locale.value = l; localStorage.setItem('locale', l) }

async function testConn() {
  busy.value = true; testing.value = true; msg.value = ''; ok.value = false
  try {
    const { data } = await axios.post('/api/setup/test', cfg)
    ok.value = true; msg.value = `✓ ${t('setup.testOk')}: ${data.message || ''}`
  } catch (e) {
    ok.value = false; msg.value = `✗ ${t('setup.testFail')}: ${e.response?.data?.detail || e.message}`
  } finally { busy.value = false; testing.value = false }
}

async function save() {
  busy.value = true; saving.value = true; msg.value = ''
  try {
    await axios.post('/api/setup/save', cfg)
    msg.value = t('setup.done')
    setTimeout(() => { window.location.href = '/login' }, 800)
  } catch (e) {
    ok.value = false; msg.value = `✗ ${e.response?.data?.detail || e.message}`
    busy.value = false; saving.value = false
  }
}
</script>

<style scoped>
.auth-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.setup-card { width: 460px; max-width: 94vw; }
h2 { margin: 0 0 6px; }
.tip { font-size: 12px; color: var(--text-soft); background: var(--primary-soft); padding: 8px 10px; border-radius: 8px; margin-top: 14px; }
.ok { color: var(--success); font-size: 13px; }
.err { color: var(--danger); font-size: 13px; word-break: break-all; }
.lang { text-align: center; margin-top: 16px; font-size: 13px; color: var(--text-soft); }
</style>
