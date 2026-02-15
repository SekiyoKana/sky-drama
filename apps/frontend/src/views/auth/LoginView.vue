<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { useI18n } from 'vue-i18n'
  import { useAuthStore } from '@/stores/auth'
  import NeuCard from '@/components/base/NeuCard.vue'
  import NeuInput from '@/components/base/NeuInput.vue'
  import NeuButton from '@/components/base/NeuButton.vue'
  import { Check, Github } from 'lucide-vue-next'
  import { open } from '@tauri-apps/plugin-shell'
  
  const router = useRouter()
  const authStore = useAuthStore()
  const { t } = useI18n()
  
  const isLogin = ref(true)
  const loading = ref(false)
  const errorMsg = ref('')
  const rememberMe = ref(false)
  
  const openGithub = async () => {
    try {
      await open('https://github.com/Sekiyo/sky-drama')
    } catch (error) {
      console.error('Failed to open link:', error)
      window.open('https://github.com/Sekiyo/sky-drama', '_blank')
    }
  }
  
  const form = ref({
    email: '',
    password: ''
  })
  
  onMounted(async () => {
    const savedEmail = localStorage.getItem('login_email')
    if (savedEmail) {
      form.value.email = savedEmail
      rememberMe.value = true
    }
  })
  
  const handleAuth = async () => {
    if (!form.value.email || !form.value.password) {
      errorMsg.value = t('login.fillRequired')
      return
    }
    
    loading.value = true
    errorMsg.value = ''
  
    try {
      if (isLogin.value) {
        if (rememberMe.value) {
          localStorage.setItem('login_email', form.value.email)
        } else {
          localStorage.removeItem('login_email')
        }
  
        await authStore.login(form.value)
      } else {
        await authStore.register(form.value)
      }
      router.push('/projects')
    } catch (err: any) {
      console.error(err)
      errorMsg.value = err.response?.data?.detail || t('login.actionFailed')
    } finally {
      loading.value = false
    }
  }
  </script>
  
  <template>
    <div class="flex items-center justify-center min-h-screen bg-[#E0E5EC] p-4">
      <NeuCard class="w-full max-w-md" padding="p-10">
        <div class="mb-10 text-center">
          <h1 class="text-3xl font-black tracking-wider text-gray-700">{{ t('common.appName') }}</h1>
          <p class="mt-2 text-sm text-gray-500">
            {{ isLogin ? t('login.welcomeBack') : t('login.createStudio') }}
          </p>
        </div>
  
        <div class="space-y-6">
          <NeuInput 
            v-model="form.email" 
            placeholder="name@example.com" 
            :label="t('login.emailLabel')"
            name="email"
            autocomplete="username" 
          />
          <NeuInput 
            v-model="form.password" 
            type="password" 
            placeholder="••••••••" 
            :label="t('login.passwordLabel')"
            name="password"
            autocomplete="current-password"
            @enter="handleAuth"
          />
          
          <div v-if="isLogin" class="flex items-center px-1">
            <label class="flex items-center cursor-pointer select-none group">
              <input type="checkbox" v-model="rememberMe" class="hidden">
              <div 
                class="w-5 h-5 rounded flex items-center justify-center transition-all duration-200 border border-transparent"
                :class="rememberMe 
                  ? 'shadow-[inset_2px_2px_5px_#b8b9be,inset_-3px_-3px_7px_#ffffff] bg-[#E0E5EC]' 
                  : 'shadow-[3px_3px_6px_#b8b9be,-3px_-3px_6px_#ffffff] bg-[#E0E5EC] group-hover:shadow-[4px_4px_8px_#b8b9be,-4px_-4px_8px_#ffffff]'"
              >
                <Check v-if="rememberMe" class="w-3.5 h-3.5 text-blue-500 stroke-[3]" />
              </div>
              <span class="ml-3 text-sm text-gray-500 group-hover:text-gray-700 transition-colors">{{ t('login.rememberMe') }}</span>
            </label>
          </div>
          
          <div v-if="errorMsg" class="text-red-500 text-sm text-center font-bold">{{ errorMsg }}</div>
          <NeuButton block variant="primary" :loading="loading" @click="handleAuth">
            {{ isLogin ? t('login.login') : t('login.register') }}
          </NeuButton>
        </div>
        
        <p class="mt-8 text-sm text-center text-gray-500">
          {{ isLogin ? t('login.noAccount') : t('login.hasAccount') }}
          <span class="font-bold text-blue-500 cursor-pointer hover:underline" @click="isLogin = !isLogin; errorMsg = ''">
            {{ isLogin ? t('login.signUpNow') : t('login.signInNow') }}
          </span>
        </p>

        <!-- GitHub Link -->
        <div class="mt-6 flex justify-center">
            <button 
              @click="openGithub"
              class="flex items-center gap-2 px-3 py-1.5 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-200/50 transition-all text-xs font-mono group"
            >
              <Github class="w-3.5 h-3.5 group-hover:text-black transition-colors" />
              <span class="opacity-80 group-hover:opacity-100">{{ t('login.openSourceOnGithub') }}</span>
            </button>
        </div>
  
      </NeuCard>
    </div>
  </template>
