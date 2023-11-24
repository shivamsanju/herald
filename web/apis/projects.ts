import fetcher from '@/lib/fetcher'
import { CreateProjectData } from '@/types/projects'

export const getProjectsApi = async () => {
  const res = await fetcher.get('/api/projects')
  const resData = await res.json()
  if (!resData.success) {
    throw Error(resData.error)
  }
  return resData.data
}

export const createProjectApi = async (data: CreateProjectData) => {
  const res = await fetcher.post<CreateProjectData>('/api/projects', data, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
  const resData = await res.json()
  if (!resData.success) {
    throw Error(resData.error)
  }
  return resData.data
}

export const getProjectByIdApi = async (projectId: string) => {
  const res = await fetcher.get(`/api/projects/${projectId}`)
  const resData = await res.json()
  if (!resData.success) {
    throw Error(resData.error)
  }
  return resData.data
}

export const getProjectAdminsByIdApi = async (projectId: string) => {
  const res = await fetcher.get(`/api/projects/${projectId}/admins`)
  const resData = await res.json()
  if (!resData.success) {
    throw Error(resData.error)
  }
  return resData.data
}
