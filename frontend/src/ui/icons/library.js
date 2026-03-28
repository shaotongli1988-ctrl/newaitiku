import { createFilledIcon, createStrokeIcon } from '../iconFactory'

export const ArrowDown = createStrokeIcon('ArrowDown', [
  { type: 'path', attrs: { d: 'M6 9l6 6 6-6' } },
])

export const Bell = createStrokeIcon('Bell', [
  { type: 'path', attrs: { d: 'M9.5 18h5' } },
  { type: 'path', attrs: { d: 'M6 16.5h12l-1.4-1.8a3 3 0 0 1-.6-1.8V10a4 4 0 1 0-8 0v2.9c0 .64-.22 1.26-.62 1.76L6 16.5z' } },
  { type: 'path', attrs: { d: 'M10 18a2 2 0 0 0 4 0' } },
])

export const Collection = createStrokeIcon('Collection', [
  { type: 'rect', attrs: { x: '5', y: '6', width: '10', height: '12', rx: '2' } },
  { type: 'path', attrs: { d: 'M9 9h2.5M9 12h2.5M9 15h4.5' } },
  { type: 'path', attrs: { d: 'M15 8h2a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H9' } },
])

export const Cpu = createStrokeIcon('Cpu', [
  { type: 'rect', attrs: { x: '7', y: '7', width: '10', height: '10', rx: '2.2' } },
  { type: 'rect', attrs: { x: '10', y: '10', width: '4', height: '4', rx: '1' } },
  { type: 'path', attrs: { d: 'M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3' } },
])

export const DataAnalysis = createStrokeIcon('DataAnalysis', [
  { type: 'path', attrs: { d: 'M5 19V9' } },
  { type: 'path', attrs: { d: 'M12 19V5' } },
  { type: 'path', attrs: { d: 'M19 19v-8' } },
  { type: 'path', attrs: { d: 'M4 19h16' } },
])

export const DocumentChecked = createStrokeIcon('DocumentChecked', [
  { type: 'path', attrs: { d: 'M8 3h7l4 4v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z' } },
  { type: 'path', attrs: { d: 'M15 3v4h4' } },
  { type: 'path', attrs: { d: 'M9.5 13l1.8 1.8 3.7-3.8' } },
])

export const Download = createStrokeIcon('Download', [
  { type: 'path', attrs: { d: 'M12 4v10' } },
  { type: 'path', attrs: { d: 'M8 10l4 4 4-4' } },
  { type: 'path', attrs: { d: 'M5 19h14' } },
])

export const EditPen = createStrokeIcon('EditPen', [
  { type: 'path', attrs: { d: 'M4 20l4.5-1 9.2-9.2a2.1 2.1 0 0 0-3-3L5.5 16 4 20z' } },
  { type: 'path', attrs: { d: 'M13.5 7.5l3 3' } },
])

export const House = createStrokeIcon('House', [
  { type: 'path', attrs: { d: 'M4 11.5L12 5l8 6.5' } },
  { type: 'path', attrs: { d: 'M6.5 10.5V19h11v-8.5' } },
  { type: 'path', attrs: { d: 'M10 19v-5h4v5' } },
])

export const Plus = createStrokeIcon('Plus', [
  { type: 'path', attrs: { d: 'M12 5v14M5 12h14' } },
])

export const Reading = createStrokeIcon('Reading', [
  { type: 'path', attrs: { d: 'M4.5 6.5A2.5 2.5 0 0 1 7 4h12.5v14H7a2.5 2.5 0 0 0-2.5 2.5V6.5z' } },
  { type: 'path', attrs: { d: 'M7 4v14' } },
  { type: 'path', attrs: { d: 'M10 8h6M10 11h6M10 14h4' } },
])

export const RefreshRight = createStrokeIcon('RefreshRight', [
  { type: 'path', attrs: { d: 'M20 5v6h-6' } },
  { type: 'path', attrs: { d: 'M20 11a8 8 0 1 1-2.3-5.7L20 7.6' } },
])

export const Setting = createStrokeIcon('Setting', [
  { type: 'circle', attrs: { cx: '12', cy: '12', r: '3.2' } },
  { type: 'path', attrs: { d: 'M12 3.5v2.2M12 18.3v2.2M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M3.5 12h2.2M18.3 12h2.2M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6' } },
])

export const UploadFilled = createFilledIcon('UploadFilled', [
  { type: 'path', attrs: { d: 'M12 3l4.8 5.6h-3v5.4h-3.6V8.6H7.2L12 3z' } },
  { type: 'path', attrs: { d: 'M5 16.5h14v4H5z' } },
])

export const UserFilled = createFilledIcon('UserFilled', [
  { type: 'circle', attrs: { cx: '12', cy: '8', r: '3.6' } },
  { type: 'path', attrs: { d: 'M5 20c0-3.7 3.1-6 7-6s7 2.3 7 6H5z' } },
])

export const WarningFilled = createFilledIcon('WarningFilled', [
  { type: 'path', attrs: { d: 'M12 3.5 2.8 19.5h18.4L12 3.5zm-1.2 5.2h2.4v5.4h-2.4V8.7zm0 7.2h2.4v2.1h-2.4v-2.1z' } },
])
