export interface Activity {
  run_id: number
  name: string
  distance: number // meters
  moving_time: string // "H:MM:SS"
  type: 'Run' | 'Ride'
  start_date: string
  start_date_local: string
  location_country: string | null
  summary_polyline: string | null
  average_heartrate: number | null
  average_speed: number // m/s
  elevation_gain: number | null
  source: string
  streak: number
}

export type SportFilter = 'all' | 'Run' | 'Ride'
