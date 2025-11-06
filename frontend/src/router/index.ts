import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import ProgressView from '../views/ProgressView.vue'
import ResultsView from '../views/ResultsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'upload',
      component: UploadView,
    },
    {
      path: '/progress/:job_id',
      name: 'progress',
      component: ProgressView,
    },
    {
      path: '/results/:job_id',
      name: 'results',
      component: ResultsView,
    },
  ],
})

export default router
