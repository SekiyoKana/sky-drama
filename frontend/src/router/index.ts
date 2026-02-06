import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/auth/LoginView.vue'
import ProjectListView from '@/views/projects/ProjectListView.vue'
import WorkbenchView from '@/views/workbench/WorkbenchView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/login', 
      name: 'Login', 
      component: LoginView 
    },
    { 
      path: '/projects', 
      name: 'Projects', 
      component: ProjectListView,
      meta: { requiresAuth: true } // 🔒 需要登录
    },
    { 
      path: '/workbench/:projectId/:episodeId', 
      name: 'Workbench', 
      component: WorkbenchView,
      meta: { requiresAuth: true } // 🔒 需要登录
    },
    { 
      path: '/', 
      redirect: '/projects' 
    }
  ]
})

// 🛡️ 全局路由守卫
router.beforeEach((to, _, next) => {
  const authStore = useAuthStore()
  
  // 如果要去需要登录的页面，且没有 token
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router