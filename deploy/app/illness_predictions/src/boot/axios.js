import { defineBoot } from '#q-app'
import axios from 'axios'

// Create a custom instance with base URL
const api = axios.create({
  baseURL: 'https://illness.predictions.api.yukuvillage.com'
})

export default defineBoot(({ app }) => {
  // Make available in Vue components via Options API
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

// Named exports for use in non-Vue files (e.g., Vuex)
export { axios, api }   