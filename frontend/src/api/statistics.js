import request from './request'

export function getOverview() {
  return request({
    url: '/statistics/overview',
    method: 'get'
  })
}

export function getTrend(days = 7) {
  return request({
    url: '/statistics/trend',
    method: 'get',
    params: { days }
  })
}

export function getSeverity() {
  return request({
    url: '/statistics/severity',
    method: 'get'
  })
}

export function getAccidentTypes() {
  return request({
    url: '/statistics/accident-types',
    method: 'get'
  })
}

export function getTrafficFlow(hours = 24) {
  return request({
    url: '/statistics/traffic-flow',
    method: 'get',
    params: { hours }
  })
}

export function getVehicleTypes() {
  return request({
    url: '/statistics/vehicle-types',
    method: 'get'
  })
}

export function getHourlyAccidents() {
  return request({
    url: '/statistics/hourly-accidents',
    method: 'get'
  })
}
