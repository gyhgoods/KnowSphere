import axios from 'axios'

const ACCESS_TOKEN_KEY = 'knowsphere.access_token'
const REFRESH_TOKEN_KEY = 'knowsphere.refresh_token'

export const tokenStorage = {
  get accessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  get refreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  set(accessToken: string, refreshToken: string) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  if (tokenStorage.accessToken) {
    config.headers.Authorization = `Bearer ${tokenStorage.accessToken}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

http.interceptors.response.use(undefined, async (error) => {
  const original = error.config
  if (error.response?.status !== 401 || original?._retried || !tokenStorage.refreshToken) {
    return Promise.reject(error)
  }
  original._retried = true
  refreshPromise ??= axios
    .post(`${http.defaults.baseURL}/auth/refresh`, {
      refresh_token: tokenStorage.refreshToken,
    })
    .then(({ data }) => {
      tokenStorage.set(data.access_token, data.refresh_token)
      return data.access_token as string
    })
    .finally(() => {
      refreshPromise = null
    })
  try {
    original.headers.Authorization = `Bearer ${await refreshPromise}`
    return http(original)
  } catch (refreshError) {
    tokenStorage.clear()
    window.location.assign('/login')
    return Promise.reject(refreshError)
  }
})

