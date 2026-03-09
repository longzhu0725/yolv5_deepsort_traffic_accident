import request from './request'

export function getAccidents(params) {
  return request({
    url: '/accidents',
    method: 'get',
    params
  })
}

export function getAccident(id) {
  return request({
    url: `/accidents/${id}`,
    method: 'get'
  })
}

export function updateAccidentStatus(id, status) {
  return request({
    url: `/accidents/${id}/status`,
    method: 'put',
    data: { status }
  })
}

export function updateAccident(id, data) {
  return request({
    url: `/accidents/${id}`,
    method: 'put',
    data
  })
}

export function deleteAccident(id) {
  return request({
    url: `/accidents/${id}`,
    method: 'delete'
  })
}
