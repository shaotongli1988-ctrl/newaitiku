import { defineComponent, h } from 'vue'

function createNode(type, attrs = {}) {
  return h(type, attrs)
}

export function createStrokeIcon(name, nodes = []) {
  return defineComponent({
    name,
    setup() {
      return () => h(
        'svg',
        {
          viewBox: '0 0 24 24',
          fill: 'none',
          xmlns: 'http://www.w3.org/2000/svg',
          'aria-hidden': 'true',
          stroke: 'currentColor',
          'stroke-width': '1.8',
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
        },
        nodes.map((node) => createNode(node.type, node.attrs)),
      )
    },
  })
}

export function createFilledIcon(name, nodes = []) {
  return defineComponent({
    name,
    setup() {
      return () => h(
        'svg',
        {
          viewBox: '0 0 24 24',
          xmlns: 'http://www.w3.org/2000/svg',
          'aria-hidden': 'true',
          fill: 'currentColor',
        },
        nodes.map((node) => createNode(node.type, node.attrs)),
      )
    },
  })
}
