import request from './request'

export function getCameras() {
  return request({
    url: '/cameras',
    method: 'get'
  })
}

export function createCamera(data) {
  return request({
    url: '/cameras',
    method: 'post',
    data
  })
}

export function updateCamera(id, data) {
  return request({
    url: `/cameras/${id}`,
    method: 'put',
    data
  })
}

export function deleteCamera(id) {
  return request({
    url: `/cameras/${id}`,
    method: 'delete'
  })
}

export function startCamera(id) {
  return request({
    url: `/cameras/${id}/start`,
    method: 'post'
  })
}

export function stopCamera(id) {
  return request({
    url: `/cameras/${id}/stop`,
    method: 'post'
  })
}
